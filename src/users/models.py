from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    new_password_confirm: str


class User(UserBase):
    id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)