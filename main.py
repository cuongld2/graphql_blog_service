from logging import log, CRITICAL

import bcrypt
import graphene
import uvicorn
from fastapi import FastAPI, HTTPException
from graphene import String
from graphql import GraphQLError
from jwt import PyJWTError
from starlette.graphql import GraphQLApp

import crud
import models
from app_utils import decode_access_token
from database import db_session
from schemas import BlogSchema, UserInfoSchema, UserCreate, UserAuthenticate, TokenData, BlogBase

ACCESS_TOKEN_EXPIRE_MINUTES = 30


db = db_session.session_factory()


class Query(graphene.ObjectType):

    all_blogs = graphene.List(BlogSchema)

    def resolve_all_blogs(self, info):
        query = BlogSchema.get_query(info)  # SQLAlchemy query
        return query.all()


class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        fullname = graphene.String()

    ok = graphene.Boolean()
    user = graphene.Field(lambda: UserInfoSchema)

    @staticmethod
    def mutate(root, info, username, password, fullname, ):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = UserInfoSchema(username=username, password=hashed_password, fullname=fullname)
        ok = True
        db_user = crud.get_user_by_username(db, username=username)
        if db_user:
            raise GraphQLError("Username already registered")
        user_info = UserCreate(username=username, password=password, fullname=fullname)
        crud.create_user(db, user_info)
        return CreateUser(user=user, ok=ok)


class AuthenUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    token = graphene.String()

    @staticmethod
    def mutate(root, info, username, password):
        db_user = crud.get_user_by_username(db, username=username)
        user_authenticate = UserAuthenticate(username=username, password=password)
        if db_user is None:
            raise GraphQLError("Username not existed")
        else:
            is_password_correct = crud.check_username_password(db, user_authenticate)
            if is_password_correct is False:
                raise GraphQLError("Password is not correct")
            else:
                from datetime import timedelta
                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                from app_utils import create_access_token
                access_token = create_access_token(
                    data={"sub": username}, expires_delta=access_token_expires)
                return AuthenUser(token=access_token)


class CreateNewBlog(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        token = graphene.String(required=True)

    ok = graphene.Boolean()

    @staticmethod
    def mutate(root, info, title, content, token):
        try:
            payload = decode_access_token(data=token)
            username: str = payload.get("sub")
            if username is None:
                raise GraphQLError("Invalid credentials")
            token_data = TokenData(username=username)
        except PyJWTError:
            raise GraphQLError("Invalid credentials")
        user = crud.get_user_by_username(db, username=token_data.username)
        if user is None:
            raise GraphQLError("Invalid credentials")
        blog = BlogBase(title=title, content=content)
        crud.create_new_blog(db=db, blog=blog)
        ok = True
        return CreateNewBlog(ok=ok)


class MyMutations(graphene.ObjectType):
    user = CreateUser.Field()
    authen_user = AuthenUser.Field()
    create_new_blog = CreateNewBlog.Field()


app = FastAPI()
app.add_route("/graphql", GraphQLApp(schema=graphene.Schema(query=Query, mutation=MyMutations)))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)