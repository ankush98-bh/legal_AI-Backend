from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from .group_schema import GroupResponse

class UserBase(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    username: str
    mail_id: EmailStr
    role: str
    group_id: int
    is_staff: Optional[bool] = False
    is_superuser: Optional[bool] = False

class UserCreate(UserBase):
    password: str  # Include password on creation

class UserResponse(UserBase):
    user_id: int
    created_at: datetime
    group: Optional[GroupResponse] = None  # Relationship field

    class Config:
        orm_mode = True
