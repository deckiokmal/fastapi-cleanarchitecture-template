from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional


class ConversationBase(BaseModel):
    title: str


class ConversationCreate(ConversationBase):
    user_id: UUID


class Conversation(ConversationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ChatMessageBase(BaseModel):
    content: str
    message_type: str


class ChatMessageCreate(ChatMessageBase):
    chat_session_id: UUID


class ChatMessage(ChatMessageBase):
    id: UUID
    chat_session_id: UUID
    created_at: datetime
    tokens_used: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)