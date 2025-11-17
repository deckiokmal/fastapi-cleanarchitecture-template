from sqlalchemy import Column, String, ForeignKey, DateTime, func, Boolean, Text, Integer, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from ..database.core import Base


class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship('User', back_populates='conversations')
    chat_sessions = relationship('ChatSession', back_populates='conversation', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title}, user_id={self.user_id})>"
    

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255))
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    conversation = relationship("Conversation", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session", cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, session_token='{self.session_token}')>"
    

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    chat_session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    message_type = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    response_time = Column(Float)  # in seconds
    message_metadata = Column(JSON)  # for additional data like model used, temperature, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    chat_session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, type='{self.message_type}')>"
    
    
class BotPersonality(Base):
    __tablename__ = "bot_personalities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    system_prompt = Column(Text, nullable=False)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation_settings = relationship("ConversationSetting", back_populates="bot_personality")
    
    def __repr__(self):
        return f"<BotPersonality(id={self.id}, name='{self.name}')>"


class ConversationSetting(Base):
    __tablename__ = "conversation_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    bot_personality_id = Column(UUID(as_uuid=True), ForeignKey("bot_personalities.id", ondelete="SET NULL"), nullable=True)
    settings = Column(JSON)  # Additional settings like model name, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation")
    bot_personality = relationship("BotPersonality", back_populates="conversation_settings")
    
    def __repr__(self):
        return f"<ConversationSetting(id={self.id}, conversation_id={self.conversation_id})>"


class UserFeedback(Base):
    __tablename__ = "user_feedbacks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    chat_message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer)  # 1-5 scale
    feedback_text = Column(Text)
    is_helpful = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    chat_message = relationship("ChatMessage")
    
    def __repr__(self):
        return f"<UserFeedback(id={self.id}, rating={self.rating})>"