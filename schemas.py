from graphene_sqlalchemy import SQLAlchemyObjectType
from models import UserInfo, Blog
from pydantic import BaseModel


class UserInfoBase(BaseModel):
    username: str


class UserCreate(UserInfoBase):
    fullname: str
    password: str


class UserAuthenticate(UserInfoBase):
    password: str


class UserInformation(UserInfoBase):
    id: int

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str = None


class BlogBase(BaseModel):
    title: str
    content: str


class BlogInformation(BlogBase):
    id: int

    class Config:
        orm_mode = True


class UserInfoSchema(SQLAlchemyObjectType):
    class Meta:
        model = UserInfo


class BlogSchema(SQLAlchemyObjectType):
    class Meta:
        model = Blog


