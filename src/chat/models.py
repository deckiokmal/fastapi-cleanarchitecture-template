from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any


class MessageType(str, Enum):
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'


# Conversation Schemas
class ConversationBase(BaseModel):
    title: str


class ConversationCreate(ConversationBase):
    pass


class Conversation(ConversationBase):
    id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ConversationWithSessions(Conversation):
    chat_sessions: List["ChatSession"] = []


# ChatSession Schemas
class ChatSessionBase(BaseModel):
    title: Optional[str] = None
    session_token: str
    

class ChatSessionCreate(ChatSessionBase):
    conversation_id: UUID
    
    
class ChatSession(ChatSessionBase):
    id: UUID
    conversation_id: UUID
    user_id: UUID
    is_active: bool
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ChatSessionWithMessages(ChatSession):
    messages: List["ChatMessage"] = []
    

# ChatMessage Schemas
class ChatMessageBase(BaseModel):
    message_type: MessageType
    content: str
    tokens_used: Optional[int] = 0
    response_time: Optional[float] = None
    message_metadata: Optional[Dict[str, Any]] = None


class ChatMessageCreate(ChatMessageBase):
    chat_session_id: UUID


class ChatMessage(ChatMessageBase):
    id: UUID
    chat_session_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    
# Update forward references
ConversationWithSessions.model_rebuild()
ChatSessionWithMessages.model_rebuild()