# api/auth.py или где у тебя api = NinjaAPI()

from ninja import NinjaAPI
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from ninja.security import django_auth
from core.apps.users.schema import LoginSchema, RegisterSchema, UserOut
from django.middleware.csrf import get_token

api = NinjaAPI(title="Api", csrf=True)  # важно: csrf=True для сессий


@api.post("/login", auth=None, tags=["auth"])  # auth=None — доступно всем
def login_user(request, payload: LoginSchema):
    user = authenticate(username=payload.username, password=payload.password)
    if user is not None:
        login(request, user)  # ← создаёт сессию!
        return {
            "success": True,
            "user": UserOut.from_orm(user),
            "csrfToken": get_token(request),
        }
    return api.create_response(request, {"detail": "Invalid credentials"}, status=401)


@api.post("/logout", auth=django_auth, tags=["auth"])
def logout_user(request):
    logout(request)
    return {"success": True}


@api.post("/register", auth=None, tags=["auth"])
def register_user(request, payload: RegisterSchema):
    if payload.password1 != payload.password2:
        return api.create_response(
            request, {"detail": "Passwords do not match"}, status=400
        )

    if User.objects.filter(username=payload.username).exists():
        return api.create_response(
            request, {"detail": "Username already taken"}, status=400
        )

    try:
        user = User.objects.create_user(
            username=payload.username, email=payload.email, password=payload.password1
        )
        # Автоматически логиним после регистрации (опционально)
        login(request, user)
        return {"success": True, "user": UserOut.from_orm(user)}
    except ValidationError as e:
        return api.create_response(request, {"detail": str(e)}, status=400)


@api.get("/me", auth=django_auth, tags=["auth"])
def me(request):
    return UserOut.from_orm(request.auth)
