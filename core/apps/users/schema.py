# core/apps/users/schemas.py

from ninja import Schema
from django.contrib.auth.models import User

class LoginSchema(Schema):
    username: str
    password: str

class RegisterSchema(Schema):
    username: str
    email: str
    password1: str
    password2: str

class UserOut(Schema):
    id: int
    username: str
    email: str

    @staticmethod
    def from_orm(user: User):
        return UserOut(
            id=user.id,
            username=user.username,
            email=user.email,
        )