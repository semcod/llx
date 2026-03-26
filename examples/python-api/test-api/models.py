from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class TodoStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: TodoStatus = TodoStatus.pending
    due_date: Optional[datetime] = None

    @validator('due_date')
    def due_date_must_be_in_future(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError('due_date must be in the future')
        return v


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[TodoStatus] = None
    due_date: Optional[datetime] = None

    @validator('due_date')
    def due_date_must_be_in_future(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError('due_date must be in the future')
        return v


class TodoInDBBase(TodoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Todo(TodoInDBBase):
    pass


class TodoInDB(TodoInDBBase):
    pass


class TodoListResponse(BaseModel):
    todos: List[Todo]
    total: int
    page: int
    size: int


class ErrorResponse(BaseModel):
    detail: str


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime