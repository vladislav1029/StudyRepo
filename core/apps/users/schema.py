from ninja import Schema


class LoginSchema(Schema):
    username: str
    password: str

class RegisterSchema(Schema):
    username: str
    email: str
    password1: str
    password2: str

class UserOut(Schema):
    username: str
    email: str
    is_active: bool