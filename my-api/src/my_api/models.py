"""
Pydantic models for the API.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SmoketestRequest(BaseModel):
    id: int = Field(..., description="Unique identifier for the request")
    name: str = Field(..., description="Name of the request")
    description: Optional[str] = Field(None, description="Description of the request")
    created_at: datetime = Field(..., description="Timestamp when the request was created")
    updated_at: datetime = Field(..., description="Timestamp when the request was last updated")

class SmoketestResponse(BaseModel):
    id: int = Field(..., description="Unique identifier for the response")
    name: str = Field(..., description="Name of the response")
    description: Optional[str] = Field(None, description="Description of the response")
    created_at: datetime = Field(..., description="Timestamp when the response was created")
    updated_at: datetime = Field(..., description="Timestamp when the response was last updated")

class SmoketestDBSchema(BaseModel):
    id: int = Field(..., description="Unique identifier for the database schema")
    name: str = Field(..., description="Name of the database schema")
    description: Optional[str] = Field(None, description="Description of the database schema")
    created_at: datetime = Field(..., description="Timestamp when the database schema was created")
    updated_at: datetime = Field(..., description="Timestamp when the database schema was last updated")

class SmoketestDBSchemaRequest(BaseModel):
    id: int = Field(..., description="Unique identifier for the database schema request")
    name: str = Field(..., description="Name of the database schema request")
    description: Optional[str] = Field(None, description="Description of the database schema request")
    created_at: datetime = Field(..., description="Timestamp when the database schema request was created")
    updated_at: datetime = Field(..., description="Timestamp when the database schema request was last updated")

class SmoketestDBSchemaResponse(BaseModel):
    id: int = Field(..., description="Unique identifier for the database schema response")
    name: str = Field(..., description="Name of the database schema response")
    description: Optional[str] = Field(None, description="Description of the database schema response")
    created_at: datetime = Field(..., description="Timestamp when the database schema response was created")
    updated_at: datetime = Field(..., description="Timestamp when the database schema response was last updated")