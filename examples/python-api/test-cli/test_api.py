import os
import shutil
import tempfile
import json
from pathlib import Path
from typing import Generator
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

# ----------------------------
# Application Code (FileMaster CLI API)
# ----------------------------

app = FastAPI(title="FileMaster CLI", description="Efficient file management via CLI")

class FileOperationRequest(BaseModel):
    source: str
    destination: str = None
    recursive: bool = False

class DirectoryCreateRequest(BaseModel):
    path: str
    parents: bool = True
    exist_ok: bool = True

class SearchRequest(BaseModel):
    path: str
    pattern: str
    recursive: bool = True

@app.get("/")
def read_root():
    return {"message": "Welcome to FileMaster CLI"}

@app.post("/files/copy")
def copy_file(request: FileOperationRequest):
    src = Path(request.source)
    if not src.exists():
        raise HTTPException(status_code=404, detail="Source file not found")
    if not src.is_file():
        raise HTTPException(status_code=400, detail="Source is not a file")
    
    dst = Path(request.destination)
    try:
        shutil.copy2(src, dst)
        return {"status": "success", "message": f"File copied from {src} to {dst}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/files/move")
def move_file(request: FileOperationRequest):
    src = Path(request.source)
    if not src.exists():
        raise HTTPException(status_code=404, detail="Source file not found")
    
    dst = Path(request.destination)
    try:
        shutil.move(str(src), str(dst))
        return {"status": "success", "message": f"File moved from {src} to {dst}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/files/delete")
def delete_file(request: FileOperationRequest):
    src = Path(request.source)
    if not src.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if not src.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    try:
        src.unlink()
        return {"status": "success", "message": f"File deleted: {src}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dirs/create")
def create_directory(request: DirectoryCreateRequest):
    path = Path(request.path)
    try:
        path.mkdir(parents=request.parents, exist_ok=request.exist_ok)
        return {"status": "success", "message": f"Directory created: {path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dirs/delete")
def delete_directory(request: FileOperationRequest):
    path = Path(request.source)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Directory not found")
    if not path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")
    
    try:
        if request.recursive:
            shutil.rmtree(path)
        else:
            path.rmdir()
        return {"status": "success", "message": f"Directory deleted: {path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
def search_files(request: SearchRequest):
    path = Path(request.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    
    matches = []
    try:
        if request.recursive:
            pattern = f"**/{request.pattern}"
        else:
            pattern = request.pattern
        
        for file_path in path.glob(pattern):
            matches.append(str(file_path))
        
        return {"status": "success", "matches": matches, "count": len(matches)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/info")
def file_info(path: str):
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File or directory not found")
    
    stat = file_path.stat()
    info = {
        "name": file_path.name,
        "path": str(file_path),
        "is_file": file_path.is_file(),
        "is_dir": file_path.is_dir(),
        "size": stat.st_size,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
    }
    return {"status": "success", "info": info}

# ----------------------------
# Test Setup
# ----------------------------

@pytest.fixture(scope="module")
def test_client() -> Generator:
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
def temp_dir() -> Generator:
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    shutil.rmtree(dir_path)

@pytest.fixture(scope="function")
def sample_files(temp_dir: Path) -> Path:
    # Create sample files and directories
    (temp_dir / "test.txt").write_text("Hello, World!")
    (temp_dir / "subdir").mkdir()
    (temp_dir / "subdir" / "nested.txt").write_text("Nested content")
    (temp_dir / "image.jpg").write_bytes(b'\xff\xd8\xff\xe0\x00\x10')
    yield temp_dir

# ----------------------------
# Unit and Integration Tests
# ----------------------------

def test_read_root(test_client: TestClient):
    response = test_client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Welcome to FileMaster CLI"

def test_create_directory_success(test_client: TestClient, temp_dir: Path):
    dir_path = temp_dir / "new_dir" / "nested"
    response = test_client.post("/dirs/create", json={
        "path": str(dir_path),
        "parents": True,
        "exist_ok": True
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert (dir_path).exists()
    assert (dir_path).is_dir()

def test_create_directory_already_exists(test_client: TestClient, temp_dir: Path):
    # Create directory first
    dir_path = temp_dir / "existing"
    dir_path.mkdir()
    
    # Try to create again with exist_ok=True
    response = test_client.post("/dirs/create", json={
        "path": str(dir_path),
        "parents": False,
        "exist_ok": True
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_create_directory_no_parents(test_client: TestClient, temp_dir: Path):
    dir_path = temp_dir / "parent" / "child"
    # Should fail because parent doesn't exist and parents=False
    response = test_client.post("/dirs/create", json={
        "path": str(dir_path),
        "parents": False,
        "exist_ok": False
    })
    assert response.status_code == 500  # Will raise OSError which becomes 500

def test_copy_file_success(test_client: TestClient, sample_files: Path):
    src = sample_files / "test.txt"
    dst = sample_files / "test_copy.txt"
    
    response = test_client.post("/files/copy", json={
        "source": str(src),
        "destination": str(dst)
    })
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert dst.exists()
    assert dst.read_text() == "Hello, World!"

def test_copy_file_source_not_found(test_client: TestClient, temp_dir: Path):
    response = test_client.post("/files/copy", json={
        "source": str(temp_dir / "nonexistent.txt"),
        "destination": str(temp_dir / "dest.txt")
    })
    assert response.status_code == 404
    assert "Source file not found" in response.json()["detail"]

def test_copy_file_source_not_file(test_client: TestClient, temp_dir: Path):
    # Create a directory with the same name
    (temp_dir / "not_a_file").mkdir()
    response = test_client.post("/files/copy", json={
        "source": str(temp_dir / "not_a_file"),
        "destination": str(temp_dir / "dest.txt")
    })
    assert response.status_code == 400
    assert "Source is not a file" in response.json()["detail"]

def test_move_file_success(test_client: TestClient, sample_files: Path):
    src = sample_files / "test.txt"
    dst = sample_files / "moved.txt"
    
    response = test_client.post("/files/move", json={
        "source": str(src),
        "destination": str(dst)
    })
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert not src.exists()
    assert dst.exists()
    assert dst.read_text() == "Hello, World!"

def test_move_file_source_not_found(test_client: TestClient, temp_dir: Path):
    response = test_client.post("/files/move", json={
        "source": str(temp_dir / "nonexistent.txt"),
        "destination": str(temp_dir / "dest.txt")
    })
    assert response.status_code == 404
    assert "Source file not found" in response.json()["detail"]

def test_delete_file_success(test_client: TestClient, sample_files: Path):
    file_path = sample_files / "test.txt"
    assert file_path.exists()
    
    response = test_client.post("/files/delete", json={
        "source": str(file_path)
    })
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert not file_path.exists()

def test_delete_file_not_found(test_client: TestClient, temp_dir: Path):
    response = test_client.post("/files/delete", json={
        "source": str(temp_dir / "nonexistent.txt")
    })
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]

def test_delete_file_is_directory(test_client: TestClient, sample_files: Path):
    response = test_client.post("/files/delete", json={
        "source": str(sample_files / "subdir")
    })
    assert response.status_code == 400
    assert "Path is not a file" in response.json()["detail"]

def test_delete_directory_success(test_client: TestClient, sample_files: Path):
    dir_path = sample_files / "subdir"
    assert dir_path.exists()
    
    response = test_client.post("/dirs/delete", json={
        "source": str(dir_path),
        "recursive": True
    })
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert not dir_path.exists()

def test_delete_directory_not_found(test_client: TestClient, temp_dir: Path):
    response = test_client.post("/dirs/delete", json={
        "source": str(temp_dir / "nonexistent_dir"),
        "recursive": False
    })
    assert response.status_code == 404
    assert "Directory not found" in response.json()["detail"]

def test_delete_directory_not_directory(test_client: TestClient, sample_files: Path):
    response = test_client.post("/dirs/delete", json={
        "source": str(sample_files / "test.txt"),
        "recursive": False
    })
    assert response.status_code == 400
    assert "Path is not a directory" in response.json()["detail"]

def test_delete_directory_non_recursive_not_empty(test_client: TestClient, sample_files: Path):
    # Try to delete non-empty directory without recursive=True
    dir_path = sample_files / "subdir"
    response = test_client.post("/dirs/delete", json={
        "source": str(dir_path),
        "recursive": False
    })
    # This will fail with 500 because rmdir on non-empty dir raises OSError
    assert response.status_code == 500

def test_search_files_success(test_client: TestClient, sample_files: Path):
    response = test_client.post("/search", json={
        "path": str(sample_files),
        "pattern": "*.txt",
        "recursive": True
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] >= 2  # test.txt and nested.txt
    matches = data["matches"]
    assert any("test.txt" in match for match in matches)
    assert any("nested.txt" in match for match in matches)

def test_search_files_no_matches(test_client: TestClient, sample_files: Path):
    response = test_client.post("/search", json={
        "path": str(sample_files),
        "pattern": "*.pdf",
        "recursive": True
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] == 0
    assert len(data["matches"]) == 0

def test_search_files_path_not_found(test_client: TestClient, temp_dir: Path):
    response = test_client.post("/search", json={
        "path": str(temp_dir / "nonexistent"),
        "pattern": "*.txt",
        "recursive": True
    })
    assert response.status_code == 404
    assert "Path not found" in response.json()["detail"]

def test_file_info_success(test_client: TestClient, sample_files: Path):
    file_path = sample_files / "test.txt"
    response = test_client.get(f"/files/info?path={str(file_path)}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    info = data["info"]
    assert info["name"] == "test.txt"
    assert info["is_file"] is True
    assert info["is_dir"] is False
    assert info["size"] == 13  # "Hello, World!" length

def test_file_info_directory(test_client: TestClient, sample_files: Path):
    dir_path = sample_files / "subdir"
    response = test_client.get(f"/files/info?path={str(dir_path)}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    info = data["info"]
    assert info["name"] == "subdir"
    assert info["is_dir"] is True
    assert info["is_file"] is False

def test_file_info_not_found(test_client: TestClient, temp_dir: Path):
    response = test_client.get(f"/files/info?path={str(temp_dir / 'nonexistent.txt')}")
    assert response.status_code == 404
    assert "File or directory not found" in response.json()["detail"]

# ----------------------------
# Error Handling Tests
# ----------------------------

def test_invalid_json_request(test_client: TestClient):
    response = test_client.post("/files/copy", content="invalid json")
    assert response.status_code == 422  # Unprocessable Entity

def test_missing_required_fields(test_client: TestClient):
    response = test_client.post("/files/copy", json={"destination": "/path"})
    assert response.status_code == 422

def test_unexpected_exception_handling(test_client: TestClient, monkeypatch):
    # Mock Path.exists to raise an unexpected exception
    def mock_exists_raise(*args, **kwargs):
        raise RuntimeError("Unexpected error")
    
    monkeypatch.setattr(Path, "exists", mock_exists_raise)
    
    response = test_client.post("/files/copy", json={
        "source": "/some/path",
        "destination": "/another/path"
    })
    
    assert response.status_code == 500
    assert "Unexpected error" in response.json()["detail"]

# ----------------------------
# Integration Tests
# ----------------------------

def test_full_file_lifecycle(test_client: TestClient, temp_dir: Path):
    # Create directory
    dir_path = temp_dir / "lifecycle_test"
    response = test_client.post("/dirs/create", json={"path": str(dir_path)})
    assert response.status_code == 200
    
    # Create a file
    file_path = dir_path / "lifecycle.txt"
    file_path.write_text("Lifecycle test content")
    
    # Get file info
    response = test_client.get(f"/files/info?path={str(file_path)}")
    assert response.status_code == 200
    assert response.json()["info"]["size"] == 23
    
    # Copy the file
    copy_path = dir_path / "lifecycle_copy.txt"
    response = test_client.post("/files/copy", json={
        "source": str(file_path),
        "destination": str(copy_path)
    })
    assert response.status_code == 200
    assert copy_path.exists()
    
    # Move the original file
    moved_path = dir_path / "lifecycle_moved.txt"
    response = test_client.post("/files/move", json={
        "source": str(file_path),
        "destination": str(moved_path)
    })
    assert response.status_code == 200
    assert not file_path.exists()
    assert moved_path.exists()
    
    # Search for txt files
    response = test_client.post("/search", json={
        "path": str(dir_path),
        "pattern": "*.txt"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 2
    
    # Delete copy
    response = test_client.post("/files/delete", json={"source": str(copy_path)})
    assert response.status_code == 200
    assert not copy_path.exists()
    
    # Delete moved file
    response = test_client.post("/files/delete", json={"source": str(moved_path)})
    assert response.status_code == 200
    assert not moved_path.exists()
    
    # Delete directory
    response = test_client.post("/dirs/delete", json={
        "source": str(dir_path),
        "recursive": True
    })
    assert response.status_code == 200
    assert not dir_path.exists()

# ----------------------------
# Pytest Configuration
# ----------------------------

# Note: Add to pyproject.toml or setup.cfg for coverage
# [tool.coverage.run]
# source = ["."]
# omit = ["*test*", "*/site-packages/*", "*/venv/*"]