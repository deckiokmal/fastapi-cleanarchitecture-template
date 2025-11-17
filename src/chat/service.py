from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from uuid import UUID
from . import models
from src.auth.models import TokenData
from src.entities.chat import Conversation, ChatSession, ChatMessage
from src.entities.user import User
from src.exceptions import ConversationCreationError, ChatSessionCreationError, ChatMessageCreationError, GetConversationError
from typing import List, Optional
import logging


# Conversation Services
def create_conversation(db: Session, current_user: TokenData, conversation_data: models.ConversationCreate) -> Conversation:
    try:
        new_conversation = Conversation(**conversation_data.model_dump())
        new_conversation.user_id = current_user.get_uuid() # type: ignore
        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)
        logging.info(f"Created new conversation for user: {current_user.get_uuid()}")
        return new_conversation
    except Exception as e:
        logging.error(f"Failed to create conversation for user {current_user.get_uuid()}. Error: {str(e)}")
        raise ConversationCreationError(str(e))


def get_user_conversations(db: Session, current_user: TokenData) -> List[Conversation]:
    try:
        # Cari user berdasarkan UUID dari token
        user = db.query(User).filter(User.id == current_user.get_uuid()).first()
        if not user:
            logging.warning(f"User not found with UUID: {current_user.get_uuid()}")
            return []
        
        # Filter conversations berdasarkan internal user ID
        conversations = db.query(Conversation).filter(Conversation.user_id == user.id, Conversation.is_active == True).order_by(Conversation.updated_at.desc()).all()
        logging.info(f"Retrieved {len(conversations)} conversations for user: {current_user.get_uuid()}")
        return conversations
    except Exception as e:
        logging.error(f"Failed to get conversations for user {current_user.get_uuid()}. Error: {str(e)}")
        return []


def get_conversation(db: Session, current_user: TokenData, conversation_id: UUID) -> Optional[Conversation]:
    try:
        # Cari user berdasarkan UUID dari token
        user = db.query(User).filter(User.id == current_user.get_uuid()).first()
        if not user:
            logging.warning(f"User not found with UUID: {current_user.get_uuid()}")
            raise GetConversationError("User not found.")
        
        conversation = db.query(Conversation).filter(and_(Conversation.id == conversation_id, Conversation.user_id == user.id, Conversation.is_active == True)).first()
        return conversation
    except Exception as e:
        logging.error(f"Failed to get conversation {conversation_id} for user {current_user.get_uuid()}. Error: {str(e)}")
        raise GetConversationError(str(e))


def delete_conversation(db: Session, current_user: TokenData, conversation_id: UUID) -> bool:
    try:
        # Cari user berdasarkan UUID dari token
        user = db.query(User).filter(User.id == current_user.get_uuid()).first()
        if not user:
            logging.warning(f"User not found with UUID: {current_user.get_uuid()}")
            raise GetConversationError("User not found.")
        
        conversation = db.query(Conversation).filter(and_(Conversation.id == conversation_id, Conversation.user_id == user.id)).first()
        
        if conversation:
            # Soft delete by setting is_active to False
            conversation.is_active = False # type: ignore
            db.commit()
            logging.info(f"Deleted conversation {conversation_id} for user: {current_user.get_uuid()}")
            return True
        return False
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to delete conversation {conversation_id} for user {current_user.get_uuid()}. Error: {str(e)}")
        return False


# Chat Session Services
def create_chat_session(db: Session, current_user: TokenData, session_data: models.ChatSessionCreate) -> ChatSession:
    try:
        # Verify conversation exists and belongs to user
        conversation = db.query(Conversation).filter(and_(Conversation.id == session_data.conversation_id, Conversation.user_id == current_user.get_uuid(), Conversation.is_active == True)).first()
        
        if not conversation:
            raise ChatSessionCreationError("Conversation not found or does not belong to the user.")
        
        new_chat_session = ChatSession(**session_data.model_dump())
        new_chat_session.user_id = current_user.get_uuid() # type: ignore
        db.add(new_chat_session)
        db.commit()
        db.refresh(new_chat_session)
        logging.info(f"Created new chat session for user: {current_user.get_uuid()}")
        return new_chat_session
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to create chat session for user {current_user.get_uuid()}. Error: {str(e)}")
        raise ChatSessionCreationError(str(e))


def get_session_by_token(db: Session, current_user: TokenData, session_token: str) -> Optional[ChatSession]:
    try:
        chat_session = db.query(ChatSession).filter(and_(ChatSession.session_token == session_token, ChatSession.user_id == current_user.get_uuid(), ChatSession.is_active == True)).first()
        return chat_session
    except Exception as e:
        logging.error(f"Failed to get chat session with token {session_token} for user {current_user.get_uuid()}. Error: {str(e)}")
        return None


def end_chat_session(db: Session, current_user: TokenData, session_id: UUID) -> bool:
    try:
        chat_session = db.query(ChatSession).filter(and_(ChatSession.id == session_id, ChatSession.user_id == current_user.get_uuid())).first()
        
        if chat_session:
            chat_session.is_active = False # type: ignore
            chat_session.ended_at = func.now() # type: ignore
            db.commit()
            logging.info(f"Ended chat session {session_id} for user: {current_user.get_uuid()}")
            return True
        return False
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to end chat session {session_id} for user {current_user.get_uuid()}. Error: {str(e)}")
        return False


# Chat Message Services
def add_chat_message(db: Session, current_user: TokenData, message_data: models.ChatMessageCreate) -> ChatMessage:
    try:
        # Verify chat session exists and belongs to user
        chat_session = db.query(ChatSession).filter(and_(ChatSession.id == message_data.chat_session_id, ChatSession.user_id == current_user.get_uuid(), ChatSession.is_active == True)).first()
        
        if not chat_session:
            raise ChatMessageCreationError("Chat session not found or does not belong to the user.")
        
        new_chat_message = ChatMessage(**message_data.model_dump())
        db.add(new_chat_message)
        db.commit()
        db.refresh(new_chat_message)
        logging.info(f"Added new chat message in session: {message_data.chat_session_id}")
        return new_chat_message
    except Exception as e:
        logging.error(f"Failed to add chat message in session {message_data.chat_session_id}. Error: {str(e)}")
        raise ChatMessageCreationError(str(e))


def get_session_messages(db: Session, current_user: TokenData, session_id: UUID) -> List[ChatMessage]:
    try:
        # Verify session belongs to user
        session = db.query(ChatSession).filter(and_(ChatSession.id == session_id, ChatSession.user_id == current_user.get_uuid(), ChatSession.is_active == True)).first()
        
        if not session:
            logging.warning(f"Chat session {session_id} not found or does not belong to user {current_user.get_uuid()}")
            return []
        
        messages = db.query(ChatMessage).filter(ChatMessage.chat_session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
        logging.info(f"Retrieved {len(messages)} messages for chat session: {session_id}")
        return messages
    except Exception as e:
        logging.error(f"Failed to get messages for chat session {session_id}. Error: {str(e)}")
        return []