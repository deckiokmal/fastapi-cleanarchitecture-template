from sqlalchemy.orm import Session
from . import models
from src.auth.models import TokenData
from src.entities.chat import Conversation, ChatSession, ChatMessage
from src.entities.user import User
from src.exceptions import ConversationCreationError, ChatSessionCreationError, ChatMessageCreationError
from uuid import UUID
import logging

def create_conversation(current_user: TokenData, db: Session, conversation: models.ConversationCreate) -> Conversation:
    try:
        new_conversation = Conversation(**conversation.model_dump())
        new_conversation.user_id = current_user.get_uuid() # type: ignore
        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)
        logging.info(f"Created new conversation for user: {current_user.get_uuid()}")
        return new_conversation
    except Exception as e:
        logging.error(f"Failed to create conversation for user {current_user.get_uuid()}. Error: {str(e)}")
        raise ConversationCreationError(str(e))


def create_chat_session(current_user: TokenData, db: Session, chat_session: models.ChatMessageCreate) -> ChatSession:
    try:
        new_chat_session = ChatSession(**chat_session.model_dump())
        new_chat_session.user_id = current_user.get_uuid() # type: ignore
        db.add(new_chat_session)
        db.commit()
        db.refresh(new_chat_session)
        logging.info(f"Created new chat session for user: {current_user.get_uuid()}")
        return new_chat_session
    except Exception as e:
        logging.error(f"Failed to create chat session for user {current_user.get_uuid()}. Error: {str(e)}")
        raise ChatSessionCreationError(str(e))


def add_chat_message(current_user: TokenData, db: Session, chat_message: models.ChatMessageCreate) -> ChatMessage:
    try:
        new_chat_message = ChatMessage(**chat_message.model_dump())
        db.add(new_chat_message)
        db.commit()
        db.refresh(new_chat_message)
        logging.info(f"Added new chat message in session: {chat_message.chat_session_id}")
        return new_chat_message
    except Exception as e:
        logging.error(f"Failed to add chat message in session {chat_message.chat_session_id}. Error: {str(e)}")
        raise ChatMessageCreationError(str(e))


def get_user_conversations(current_user: TokenData, db: Session):
    try:
        # Cari user berdasarkan UUID dari token
        user = db.query(User).filter(User.id == current_user.get_uuid()).first()
        if not user:
            logging.warning(f"User not found with UUID: {current_user.get_uuid()}")
            return []
        
        # Filter conversations berdasarkan internal user ID (integer)
        conversations = db.query(Conversation).filter(Conversation.user_id == user.id).all()
        logging.info(f"Retrieved {len(conversations)} conversations for user: {current_user.get_uuid()}")
        return conversations
    except Exception as e:
        logging.error(f"Failed to get conversations for user {current_user.get_uuid()}. Error: {str(e)}")
        return []


def get_conversation_messages(current_user: TokenData, db: Session, conversation_id: UUID):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == current_user).first()
    if conversation:
        messages = []
        for session in conversation.chat_sessions:
            messages.extend(session.messages)
        return sorted(messages, key=lambda x: x.created_at)
    return []