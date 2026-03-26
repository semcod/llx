from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="TodoAPI", description="Test API for todo management")

# In-memory storage
todos = []
next_id = 1

# Pydantic models
class TodoBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class Todo(TodoBase):
    id: int

    class Config:
        from_attributes = True

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Create a new todo
@app.post("/todos", response_model=Todo, status_code=201)
def create_todo(todo: TodoCreate):
    global next_id
    new_todo = Todo(id=next_id, **todo.model_dump())
    todos.append(new_todo)
    next_id += 1
    return new_todo

# Get all todos
@app.get("/todos", response_model=List[Todo])
def get_todos():
    return todos

# Get a specific todo by id
@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int):
    for todo in todos:
        if todo.id == todo_id:
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")

# Update a todo
@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo_update: TodoUpdate):
    for todo in todos:
        if todo.id == todo_id:
            update_data = todo_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(todo, key, value)
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")

# Delete a todo
@app.delete("/todos/{todo_id}", response_model=Todo)
def delete_todo(todo_id: int):
    for index, todo in enumerate(todos):
        if todo.id == todo_id:
            deleted_todo = todos.pop(index)
            return deleted_todo
    raise HTTPException(status_code=404, detail="Todo not found")