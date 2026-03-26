Here is the Python code for Pydantic models for 'My Project':
from pydantic import BaseModel, Field
from typing import Optional

class User(BaseModel):
    id: int
    name: str
    email: str
    password: str

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    name: Optional[str]
    email: Optional[str]
    password: Optional[str]

    class Config:
        orm_mode = True

class UserDB(User):
    hashed_password: str

class Item(BaseModel):
    id: int
    title: str
    description: str
    owner_id: int

    class Config:
        orm_mode = True

class ItemCreate(BaseModel):
    title: str
    description: str
    owner_id: int

    class Config:
        orm_mode = True

class ItemUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]

    class Config:
        orm_mode = True

class ItemDB(Item):
    owner: UserDB

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str

class UserInDB(UserDB):
    items: list[ItemDB]

class ItemInDB(ItemDB):
    owner: UserDB
This code defines the following Pydantic models:

* `User`: a user model with `id`, `name`, `email`, and `password` fields.
* `UserCreate`: a user creation model with `name`, `email`, and `password` fields.
* `UserUpdate`: a user update model with `name`, `email`, and `password` fields.
* `UserDB`: a user database model with `id`, `name`, `email`, `password`, and `hashed_password` fields.
* `Item`: an item model with `id`, `title`, `description`, and `owner_id` fields.
* `ItemCreate`: an item creation model with `title`, `description`, and `owner_id` fields.
* `ItemUpdate`: an item update model with `title` and `description` fields.
* `ItemDB`: an item database model with `id`, `title`, `description`, `owner_id`, and `owner` fields.
* `Token`: a token model with `access_token` and `token_type` fields.
* `TokenData`: a token data model with `email` field.
* `UserInDB`: a user database model with `id`, `name`, `email`, `password`, `hashed_password`, and `items` fields.
* `ItemInDB`: an item database model with `id`, `title`, `description`, `owner_id`, and `owner` fields.

Each model includes validation and database schema definitions. The `orm_mode` configuration is set to `True` for models that will be used with an ORM (Object-Relational Mapping) tool like SQLAlchemy.