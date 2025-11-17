import pytest
import warnings
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.core import Base
from src.entities.user import User
from src.entities.todo import Todo
from src.entities.chat import Conversation, ChatSession, ChatMessage
from src.auth.models import TokenData
from src.auth.service import get_password_hash
from src.rate_limiter import limiter


@pytest.fixture(scope="function")
def db_session():
    # Use a unique database URL for testing
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_user():
    # Create a user with a known password hash
    password_hash = get_password_hash("password123")
    return User(
        id=uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password_hash=password_hash
    )

@pytest.fixture(scope="function")
def test_token_data():
    return TokenData(user_id=str(uuid4()))

@pytest.fixture(scope="function")
def test_todo(test_token_data):
    return Todo(
        id=uuid4(),
        description="Test Description",
        is_completed=False,
        created_at=datetime.now(timezone.utc),
        user_id=test_token_data.get_uuid()
    )

@pytest.fixture(scope="function")
def client(db_session):
    from src.main import app
    from src.database.core import get_db
    
    # Disable rate limiting for tests
    limiter.reset()
    
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
            
    app.dependency_overrides[get_db] = override_get_db
    
    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def auth_headers(client, db_session):
    # Register a test user
    response = client.post(
        "/auth/",
        json={
            "email": "test.user@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    assert response.status_code == 201
    
    # Login to get access token
    response = client.post(
        "/auth/token",
        data={
            "username": "test.user@example.com",
            "password": "testpassword123",
            "grant_type": "password"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"} 

@pytest.fixture
def test_conversation(db_session, test_user):
    """Create a test conversation"""
    conversation = Conversation(
        title="Test Conversation",
        user_id=test_user.id,
        is_active=True
    )
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    return conversation


@pytest.fixture
def test_chat_session(db_session, test_user, test_conversation):
    """Create a test chat session"""
    session_token = f"test_session_{uuid4().hex}"
    chat_session = ChatSession(
        session_token=session_token,
        title="Test Chat Session",
        user_id=test_user.id,
        conversation_id=test_conversation.id,
        is_active=True
    )
    db_session.add(chat_session)
    db_session.commit()
    db_session.refresh(chat_session)
    return chat_session


@pytest.fixture
def test_chat_messages(db_session, test_chat_session):
    """Create test chat messages"""
    user_message = ChatMessage(
        chat_session_id=test_chat_session.id,
        message_type="user",
        content="Hello, what is Python?",
        tokens_used=10
    )
    
    assistant_message = ChatMessage(
        chat_session_id=test_chat_session.id,
        message_type="assistant",
        content="Python is a programming language...",
        tokens_used=25,
        response_time=1500,
        message_metadata={"model": "gpt-3.5-turbo", "usage": {"total_tokens": 35}}
    )
    
    db_session.add(user_message)
    db_session.add(assistant_message)
    db_session.commit()
    
    return [user_message, assistant_message]


@pytest.fixture
def another_test_user(db_session):
    """Create another test user for authorization tests"""
    user_id = uuid4()
    password_hash = get_password_hash("password123")
    user = User(
        id=user_id,
        email=f"another_{user_id}@example.com",
        first_name="Another",
        last_name="User",
        password_hash=password_hash
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# Utility functions for tests
@pytest.fixture
def create_conversation_payload():
    def _create_payload(title="Test Conversation"):
        return {"title": title}
    return _create_payload


@pytest.fixture
def create_chat_session_payload():
    def _create_payload(conversation_id, session_token=None, title="Test Chat Session"):
        if session_token is None:
            session_token = f"test_session_{uuid4().hex}"
        return {
            "conversation_id": str(conversation_id),
            "session_token": session_token,
            "title": title
        }
    return _create_payload


@pytest.fixture
def create_chat_message_payload():
    def _create_payload(chat_session_id, message_type="user", content="Test message", tokens_used=10):
        return {
            "chat_session_id": str(chat_session_id),
            "message_type": message_type,
            "content": content,
            "tokens_used": tokens_used,
            "response_time": None if message_type == "user" else 1000,
            "message_metadata": None if message_type == "user" else {"model": "gpt-3.5-turbo"}
        }
    return _create_payload


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_data(db_session):
    """Clean up test data after each test"""
    yield
    try:
        # Delete in correct order to respect foreign key constraints
        db_session.query(ChatMessage).delete()
        db_session.query(ChatSession).delete()
        db_session.query(Conversation).delete()
        db_session.query(Todo).delete()
        db_session.query(User).delete()
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        print(f"Cleanup error: {e}")