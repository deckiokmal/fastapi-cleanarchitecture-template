from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: Optional[str] = None
    is_active: bool = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    new_password_confirm: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)