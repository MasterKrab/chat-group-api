from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    id: int
    username: str


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    current_password: Optional[str] = None


class UserOutput(User):
    avatar: Optional[str]

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None


class Channel(BaseModel):
    name: str
    description: str
