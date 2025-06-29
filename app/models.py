from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: str = Field(..., description="User's email address")
    age: int = Field(..., ge=0, le=150, description="User's age")

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int = Field(..., description="Unique user identifier")
    created_at: datetime = Field(..., description="User creation timestamp")
    is_active: bool = Field(default=True, description="Whether the user is active")

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    is_active: Optional[bool] = None

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
