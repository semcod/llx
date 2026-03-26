from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List
import io
import uuid
import datetime

app = FastAPI(
    title="FileMaster CLI",
    description="A robust command-line interface for efficient file management with CRUD operations.",
    version="1.0.0"
)

# In-memory storage for files
file_storage: Dict[str, dict] = {}

class FileMetadata(BaseModel):
    id: str
    filename: str
    size: int
    content_type: str
    created_at: datetime.datetime

class FileListResponse(BaseModel):
    files: List[FileMetadata]

class SuccessResponse(BaseModel):
    message: str
    file_id: str = None

class ErrorResponse(BaseModel):
    detail: str

# Health check endpoint
@app.get("/health", response_model=SuccessResponse, summary="Health Check")
def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return SuccessResponse(message="FileMaster CLI is running")

# Create (Upload) a file
@app.post("/files", response_model=SuccessResponse, summary="Upload a file", 
          responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a new file to the server.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    try:
        content = await file.read()
        file_id = str(uuid.uuid4())
        
        file_info = {
            "id": file_id,
            "filename": file.filename,
            "content": content,
            "size": len(content),
            "content_type": file.content_type or "application/octet-stream",
            "created_at": datetime.datetime.utcnow()
        }
        
        file_storage[file_id] = file_info
        
        return SuccessResponse(message="File uploaded successfully", file_id=file_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

# Read (List) all files
@app.get("/files", response_model=FileListResponse, summary="List all files")
def list_files():
    """
    Retrieve a list of all stored files with their metadata.
    """
    files = []
    for file_info in file_storage.values():
        metadata = FileMetadata(
            id=file_info["id"],
            filename=file_info["filename"],
            size=file_info["size"],
            content_type=file_info["content_type"],
            created_at=file_info["created_at"]
        )
        files.append(metadata)
    
    return FileListResponse(files=files)

# Read (Download) a specific file
@app.get("/files/{file_id}", summary="Download a file", 
         responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def download_file(file_id: str):
    """
    Download a file by its ID.
    """
    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_info = file_storage[file_id]
        return StreamingResponse(
            io.BytesIO(file_info["content"]),
            media_type=file_info["content_type"],
            headers={"Content-Disposition": f"attachment; filename={file_info['filename']}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

# Update (Rename) a file
@app.put("/files/{file_id}", response_model=SuccessResponse, 
         summary="Rename a file", responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}})
def rename_file(file_id: str, new_filename: str = Form(...)):
    """
    Rename an existing file.
    """
    if not new_filename:
        raise HTTPException(status_code=400, detail="New filename is required")
    
    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_storage[file_id]["filename"] = new_filename
    return SuccessResponse(message="File renamed successfully", file_id=file_id)

# Delete a file
@app.delete("/files/{file_id}", response_model=SuccessResponse, 
            summary="Delete a file", responses={404: {"model": ErrorResponse}})
def delete_file(file_id: str):
    """
    Delete a file by its ID.
    """
    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail="File not found")
    
    del file_storage[file_id]
    return SuccessResponse(message="File deleted successfully", file_id=file_id)

# Get file metadata
@app.get("/files/{file_id}/metadata", response_model=FileMetadata, 
         summary="Get file metadata", responses={404: {"model": ErrorResponse}})
def get_file_metadata(file_id: str):
    """
    Retrieve metadata for a specific file.
    """
    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_info = file_storage[file_id]
    return FileMetadata(
        id=file_info["id"],
        filename=file_info["filename"],
        size=file_info["size"],
        content_type=file_info["content_type"],
        created_at=file_info["created_at"]
    )