from fastapi import APIRouter, status, HTTPException
from typing import List
from uuid import UUID

from ..database.core import DbSession
from . import  models
from . import service
from ..auth.service import CurrentUser
from ..exceptions import GetConversationError

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


# Conversation Endpoints
@router.post("/conversations", response_model=models.Conversation, status_code=status.HTTP_201_CREATED)
def create_conversation(db: DbSession, current_user: CurrentUser, conversation: models.ConversationCreate):
    return service.create_conversation(db, current_user, conversation)


@router.get("/conversations", response_model=List[models.Conversation])
def get_user_conversations(db: DbSession, current_user: CurrentUser):
    return service.get_user_conversations(db, current_user)


@router.get("/conversations/{conversation_id}", response_model=models.ConversationWithSessions)
def get_conversation(db: DbSession, current_user: CurrentUser, conversation_id: UUID):
    conversation = service.get_conversation(db, current_user, conversation_id)
    
    if not conversation:
        raise GetConversationError("Conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(db: DbSession, current_user: CurrentUser, conversation_id: UUID):
    success = service.delete_conversation(db, current_user, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")


# Chat Session Endpoints
@router.post("/chat-sessions", response_model=models.ChatSession, status_code=status.HTTP_201_CREATED)
def create_chat_session(db: DbSession, current_user: CurrentUser, chat_session: models.ChatSessionCreate):
    return service.create_chat_session(db, current_user, chat_session)


@router.get("/chat-sessions/{session_token}", response_model=models.ChatSessionWithMessages)
def get_chat_session(db: DbSession, current_user: CurrentUser, session_token: str):
    chat_session = service.get_session_by_token(db, current_user, session_token)
    
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return chat_session


@router.post("/chat-sessions/{session_id}/end", status_code=status.HTTP_200_OK)
def end_chat_session(db: DbSession, current_user: CurrentUser, session_id: UUID):
    success = service.end_chat_session(db, current_user, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return {"message": "Chat session ended successfully"}


# Chat Message Endpoints
@router.post("/chat-messages", response_model=models.ChatMessage, status_code=status.HTTP_201_CREATED)
def add_chat_message(db: DbSession, current_user: CurrentUser, chat_message: models.ChatMessageCreate):
    return service.add_chat_message(db, current_user, chat_message)


@router.get("/chat-sessions/{session_id}/messages", response_model=List[models.ChatMessage])
def get_chat_message(db: DbSession, current_user: CurrentUser, session_id: UUID):
    return service.get_session_messages(db, current_user, session_id)