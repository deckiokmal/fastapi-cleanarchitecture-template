# tests/test_chat_endpoints.py
from fastapi.testclient import TestClient
from uuid import uuid4

def test_chat_crud_operations(client: TestClient, auth_headers):
    # Create conversation
    create_response = client.post(
        "/chat/conversations",
        headers=auth_headers,
        json={
            "title": "Test Conversation"
        }
    )
    assert create_response.status_code == 201
    conversation_data = create_response.json()
    conversation_id = conversation_data["id"]
    assert conversation_data["title"] == "Test Conversation"

    # Get all conversations
    list_response = client.get("/chat/conversations", headers=auth_headers)
    assert list_response.status_code == 200
    conversations = list_response.json()
    assert len(conversations) > 0
    assert any(conv["id"] == conversation_id for conv in conversations)

    # Get specific conversation
    get_response = client.get(f"/chat/conversations/{conversation_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == conversation_id

    # Create chat session
    session_response = client.post(
        "/chat/chat-sessions",
        headers=auth_headers,
        json={
            "conversation_id": conversation_id,
            "session_token": f"test_session_{uuid4().hex}",
            "title": "Test Chat Session"
        }
    )
    assert session_response.status_code == 201
    session_data = session_response.json()
    session_id = session_data["id"]
    session_token = session_data["session_token"]
    assert session_data["session_token"].startswith("test_session_")
    assert session_data["title"] == "Test Chat Session"

    # Add user message
    user_message_response = client.post(
        "/chat/chat-messages",
        headers=auth_headers,
        json={
            "chat_session_id": session_id,
            "message_type": "user",
            "content": "Hello, what is Python?",
            "tokens_used": 10,
            "response_time": None,
            "message_metadata": None
        }
    )
    assert user_message_response.status_code == 201
    user_message = user_message_response.json()
    assert user_message["content"] == "Hello, what is Python?"
    assert user_message["message_type"] == "user"
    user_message_id = user_message["id"]

    # Add assistant message (LLM Response)
    assistant_message_response = client.post(
        "/chat/chat-messages",
        headers=auth_headers,
        json={
            "chat_session_id": session_id,
            "message_type": "assistant",
            "content": "Python is a programming language...",
            "tokens_used": 25,
            "response_time": 1500,
            "message_metadata": {
                "model": "gpt-3.5-turbo",
                "usage": {"total_tokens": 35}
            }
        }
    )
    assert assistant_message_response.status_code == 201
    assistant_message = assistant_message_response.json()
    assert assistant_message["content"] == "Python is a programming language..."
    assert assistant_message["message_type"] == "assistant"
    assert assistant_message["tokens_used"] == 25

    # Get session with messages
    get_session_response = client.get(f"/chat/chat-sessions/{session_token}", headers=auth_headers)
    assert get_session_response.status_code == 200
    session_with_messages = get_session_response.json()
    assert session_with_messages["id"] == session_id
    assert len(session_with_messages["messages"]) == 2
    assert session_with_messages["messages"][0]["message_type"] == "user"
    assert session_with_messages["messages"][1]["message_type"] == "assistant"

    # Get session messages via endpoint
    get_messages_response = client.get(f"/chat/chat-sessions/{session_id}/messages", headers=auth_headers)
    assert get_messages_response.status_code == 200
    messages = get_messages_response.json()
    assert len(messages) == 2

    # End chat session
    end_session_response = client.post(f"/chat/chat-sessions/{session_id}/end", headers=auth_headers)
    assert end_session_response.status_code == 200
    assert end_session_response.json()["message"] == "Chat session ended successfully"

    # Verify session is ended (should not be accessible)
    get_ended_session_response = client.get(f"/chat/chat-sessions/{session_token}", headers=auth_headers)
    assert get_ended_session_response.status_code == 404

    # Delete conversation
    delete_response = client.delete(f"/chat/conversations/{conversation_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    # Verify conversation is deleted
    get_deleted_response = client.get(f"/chat/conversations/{conversation_id}", headers=auth_headers)
    assert get_deleted_response.status_code == 404

def test_chat_authorization(client: TestClient, auth_headers):
    # Create a conversation first
    create_response = client.post(
        "/chat/conversations",
        headers=auth_headers,
        json={"title": "Test Conversation"}
    )
    conversation_id = create_response.json()["id"]

    # Create a session
    session_response = client.post(
        "/chat/chat-sessions",
        headers=auth_headers,
        json={
            "conversation_id": conversation_id,
            "session_token": f"test_session_{uuid4().hex}"
        }
    )
    session_id = session_response.json()["id"]
    session_token = session_response.json()["session_token"]

    # Test endpoints that require authentication
    endpoints = [
        ("GET", "/chat/conversations"),
        ("POST", "/chat/conversations"),
        ("GET", f"/chat/conversations/{conversation_id}"),
        ("DELETE", f"/chat/conversations/{conversation_id}"),
        ("POST", "/chat/chat-sessions"),
        ("GET", f"/chat/chat-sessions/{session_token}"),
        ("POST", f"/chat/chat-sessions/{session_id}/end"),
        ("POST", "/chat/chat-messages"),
        ("GET", f"/chat/chat-sessions/{session_id}/messages")
    ]

    for method, endpoint in endpoints:
        response = client.request(method, endpoint)
        assert response.status_code == 401, f"Endpoint {method} {endpoint} should require authentication"

def test_chat_not_found(client: TestClient, auth_headers):
    non_existent_id = str(uuid4())
    non_existent_token = "non_existent_token_123"

    # Test non-existent conversation
    response = client.get(f"/chat/conversations/{non_existent_id}", headers=auth_headers)
    assert response.status_code == 404

    response = client.delete(f"/chat/conversations/{non_existent_id}", headers=auth_headers)
    assert response.status_code == 404

    # Test non-existent session
    response = client.get(f"/chat/chat-sessions/{non_existent_token}", headers=auth_headers)
    assert response.status_code == 404

    response = client.post(f"/chat/chat-sessions/{non_existent_id}/end", headers=auth_headers)
    assert response.status_code == 404

    # Test non-existent session messages
    response = client.get(f"/chat/chat-sessions/{non_existent_id}/messages", headers=auth_headers)
    assert response.status_code == 200  # Should return empty list, not 404
    assert response.json() == []

def test_invalid_chat_session_creation(client: TestClient, auth_headers):
    # Try to create session with non-existent conversation
    invalid_session_data = {
        "conversation_id": str(uuid4()),  # Non-existent conversation
        "session_token": f"test_session_{uuid4().hex}",
        "title": "Invalid Session"
    }
    response = client.post("/chat/chat-sessions", json=invalid_session_data, headers=auth_headers)
    assert response.status_code == 400  # Should fail with ChatSessionCreationError

def test_invalid_message_creation(client: TestClient, auth_headers):
    # Create a conversation first
    create_response = client.post(
        "/chat/conversations",
        headers=auth_headers,
        json={"title": "Test Conversation"}
    )
    conversation_id = create_response.json()["id"]

    # Create a session
    session_response = client.post(
        "/chat/chat-sessions",
        headers=auth_headers,
        json={
            "conversation_id": conversation_id,
            "session_token": f"test_session_{uuid4().hex}"
        }
    )
    valid_session_id = session_response.json()["id"]

    # Try to create message with invalid session ID
    invalid_message_data = {
        "chat_session_id": str(uuid4()),  # Non-existent session
        "message_type": "user",
        "content": "This should fail"
    }
    response = client.post("/chat/chat-messages", json=invalid_message_data, headers=auth_headers)
    assert response.status_code == 400  # Should fail with ChatMessageCreationError

    # Try to create message with invalid message type
    invalid_type_message_data = {
        "chat_session_id": valid_session_id,
        "message_type": "invalid_type",  # Invalid message type
        "content": "This should fail too"
    }
    response = client.post("/chat/chat-messages", json=invalid_type_message_data, headers=auth_headers)
    # This might fail with 400 or 422 depending on validation
    assert response.status_code in [400, 422]

def test_conversation_soft_delete(client: TestClient, auth_headers):
    # Create conversation
    create_response = client.post(
        "/chat/conversations",
        headers=auth_headers,
        json={"title": "Test Soft Delete"}
    )
    conversation_id = create_response.json()["id"]

    # Verify it exists
    get_response = client.get(f"/chat/conversations/{conversation_id}", headers=auth_headers)
    assert get_response.status_code == 200

    # Delete conversation (soft delete)
    delete_response = client.delete(f"/chat/conversations/{conversation_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    # Verify it's not accessible anymore
    get_deleted_response = client.get(f"/chat/conversations/{conversation_id}", headers=auth_headers)
    assert get_deleted_response.status_code == 404

    # Verify it doesn't appear in conversations list
    list_response = client.get("/chat/conversations", headers=auth_headers)
    conversations = list_response.json()
    assert not any(conv["id"] == conversation_id for conv in conversations)