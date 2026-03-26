Here is the Python code for Pydantic models for 'My Project':
from pydantic import BaseModel, Field
from typing import Optional

# Request Models

class UserRequest(BaseModel):
    """User request model"""
    username: str = Field(..., title="Username", description="Username of the user")
    email: str = Field(..., title="Email", description="Email of the user")
    password: str = Field(..., title="Password", description="Password of the user")

class UserUpdateRequest(BaseModel):
    """User update request model"""
    username: Optional[str] = Field(None, title="Username", description="Username of the user")
    email: Optional[str] = Field(None, title="Email", description="Email of the user")
    password: Optional[str] = Field(None, title="Password", description="Password of the user")

class ProjectRequest(BaseModel):
    """Project request model"""
    name: str = Field(..., title="Name", description="Name of the project")
    description: str = Field(..., title="Description", description="Description of the project")

class TaskRequest(BaseModel):
    """Task request model"""
    name: str = Field(..., title="Name", description="Name of the task")
    description: str = Field(..., title="Description", description="Description of the task")
    project_id: int = Field(..., title="Project ID", description="ID of the project")

# Response Models

class UserResponse(BaseModel):
    """User response model"""
    id: int
    username: str
    email: str

class ProjectResponse(BaseModel):
    """Project response model"""
    id: int
    name: str
    description: str

class TaskResponse(BaseModel):
    """Task response model"""
    id: int
    name: str
    description: str
    project_id: int

# Database Schemas

class UserDB(BaseModel):
    """User database schema"""
    id: int
    username: str
    email: str
    password: str

class ProjectDB(BaseModel):
    """Project database schema"""
    id: int
    name: str
    description: str

class TaskDB(BaseModel):
    """Task database schema"""
    id: int
    name: str
    description: str
    project_id: int
Note that I've used the `Field` function to add metadata to the models, such as titles and descriptions. I've also used the `Optional` type to indicate that certain fields are optional. Let me know if you have any questions or need further clarification!