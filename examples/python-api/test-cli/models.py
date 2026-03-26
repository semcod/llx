from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, validator, root_validator


class FileType(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"
    SYMBOLIC_LINK = "symlink"


class FileStatus(str, Enum):
    ACTIVE = "active"
    DELETED = "deleted"
    HIDDEN = "hidden"


class FileCreateRequest(BaseModel):
    path: Path = Field(..., description="Absolute or relative path to the file/directory")
    file_type: FileType = Field(..., description="Type of the file system object")
    size: Optional[int] = Field(None, ge=0, description="Size in bytes, required for files")
    permissions: str = Field(
        ..., pattern=r"^[r-][w-][x-][r-][w-][x-][r-][w-][x-]$",
        description="Unix-style permissions string (e.g., 'rwxr-xr--')"
    )

    @validator("path")
    def path_must_not_be_root(cls, v):
        if v == Path("/") or v == Path("."):
            raise ValueError("Root or current directory cannot be managed directly")
        return v

    @root_validator
    def size_required_for_files(cls, values):
        file_type = values.get("file_type")
        size = values.get("size")
        if file_type == FileType.FILE and (size is None or size < 0):
            raise ValueError("Size must be specified and non-negative for files")
        if file_type == FileType.DIRECTORY and size is not None:
            raise ValueError("Size should not be provided for directories")
        return values


class FileUpdateRequest(BaseModel):
    path: Optional[Path] = Field(None, description="New path for moving/renaming")
    permissions: Optional[str] = Field(
        None, pattern=r"^[r-][w-][x-][r-][w-][x-][r-][w-][x-]$"
    )
    status: Optional[FileStatus] = None

    @validator("path")
    def path_cannot_be_root(cls, v):
        if v and (v == Path("/") or v == Path(".")):
            raise ValueError("Cannot move to root or current directory")
        return v


class FileResponse(BaseModel):
    id: int = Field(..., description="Unique identifier")
    path: Path = Field(..., description="Full path to the file")
    file_type: FileType
    size: Optional[int] = Field(None, ge=0)
    permissions: str = Field(..., pattern=r"^[r-][w-][x-][r-][w-][x-][r-][w-][x-]$")
    created_at: datetime
    updated_at: datetime
    status: FileStatus = FileStatus.ACTIVE

    class Config:
        orm_mode = True


class FileListResponse(BaseModel):
    files: List[FileResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1, le=100)


class FileDeleteRequest(BaseModel):
    permanent: bool = Field(
        False,
        description="If true, deletes permanently; otherwise, moves to trash (soft delete)"
    )


class FileDeleteResponse(BaseModel):
    success: bool
    message: str
    file_id: int
    permanently_deleted: bool


class FileSearchRequest(BaseModel):
    path_contains: Optional[str] = None
    file_type: Optional[FileType] = None
    status: Optional[FileStatus] = None
    min_size: Optional[int] = Field(None, ge=0)
    max_size: Optional[int] = Field(None, ge=0)
    created_before: Optional[datetime] = None
    created_after: Optional[datetime] = None

    @validator("max_size")
    def max_size_greater_than_min_size(cls, v, values):
        if "min_size" in values and v is not None and values["min_size"] is not None and v < values["min_size"]:
            raise ValueError("max_size must be greater than or equal to min_size")
        return v


class DatabaseFile(BaseModel):
    id: int = Field(primary_key=True, index=True)
    path: str = Field(..., max_length=1024, unique=True, index=True)
    file_type: FileType
    size: Optional[int] = Field(None, sa_column_kwargs={"nullable": True})
    permissions: str = Field(..., max_length=9)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: FileStatus = Field(default=FileStatus.ACTIVE)

    class Config:
        orm_mode = True