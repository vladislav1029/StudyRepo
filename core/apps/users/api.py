from ninja import NinjaAPI
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.conf import settings
from .schema import LoginSchema, RegisterSchema, UserOut
from django.contrib.auth import get_user_model

User = get_user_model()

api = NinjaAPI(
    title="Auth API",
    csrf=False,
    urls_namespace="auth",
)


def _set_refresh_cookie(response, refresh_token: str):
    """Устанавливает refresh-токен в HTTP-only куку."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # ← False для HTTP в dev; в проде — True
        samesite="Lax",
        max_age=settings.NINJA_JWT["REFRESH_TOKEN_LIFETIME"],
        path="/",  # ← работает для всех путей
    )
    return response


@api.post("/login", auth=None, tags=["auth"])
def login(request, payload: LoginSchema):
    user = authenticate(username=payload.username, password=payload.password)
    if not user:
        return api.create_response(
            request,
            {"detail": "Invalid credentials"},
            status=401,
        )

    refresh = RefreshToken.for_user(user)
    response = api.create_response(
        request,
        {
            "success": True,
            "user": UserOut.from_orm(user),
            "access": str(refresh.access_token),
        },
        status=200,
    )
    return _set_refresh_cookie(response, str(refresh))


@api.post("/register", auth=None, tags=["auth"])
def register(request, payload: RegisterSchema):
    if payload.password1 != payload.password2:
        return api.create_response(
            request,
            {"detail": "Passwords do not match"},
            status=400,
        )

    if User.objects.filter(username=payload.username).exists():
        return api.create_response(
            request,
            {"detail": "Username already taken"},
            status=400,
        )

    try:
        user = User.objects.create_user(
            username=payload.username,
            email=payload.email,
            password=payload.password1,
        )
        refresh = RefreshToken.for_user(user)
        response = api.create_response(
            request,
            {
                "success": True,
                "user": UserOut.from_orm(user),
                "access": str(refresh.access_token),
            },
            status=201,
        )
        return _set_refresh_cookie(response, str(refresh))

    except ValidationError as e:
        return api.create_response(
            request,
            {"detail": str(e)},
            status=400,
        )


@api.post("/refresh", auth=None, tags=["auth"])
def refresh(request):
    refresh_token = request.COOKIES.get("refresh_token")
    if not refresh_token:
        return api.create_response(
            request,
            {"detail": "Refresh token missing"},
            status=401,
        )

    try:
        # ВАЖНО: используем `token=...`
        refresh = RefreshToken(token=refresh_token)
        access_token = str(refresh.access_token)

        response = api.create_response(
            request,
            {"access": access_token},
            status=200,
        )

        # Ротация refresh-токена (если включена)
        if getattr(settings, "NINJA_JWT", {}).get("ROTATE_REFRESH_TOKENS", False):
            user_id = refresh.access_token.payload.get("user_id")
            try:
                user = User.objects.get(id=user_id)
                new_refresh = RefreshToken.for_user(user)
                response = _set_refresh_cookie(response, str(new_refresh))
            except User.DoesNotExist:
                return api.create_response(
                    request,
                    {"detail": "User not found"},
                    status=401,
                )

        return response

    except Exception as e:
        print("JWT Error:", str(e))
        return api.create_response(
            request,
            {"detail": "Invalid refresh token"},
            status=401,
        )


@api.post("/logout", auth=JWTAuth(), tags=["auth"])
def logout(request):
    refresh_token = request.COOKIES.get("refresh_token")
    if refresh_token:
        try:
            token = RefreshToken(token=refresh_token)
            token.blacklist()  # добавляет в чёрный список
        except Exception:
            pass  # игнорируем ошибки (например, просроченный токен)

    response = api.create_response(request, {"success": True}, status=200)
    response.delete_cookie("refresh_token", path="/")
    return response


@api.get("/me", auth=JWTAuth(), tags=["auth"])
def me(request):
    return UserOut.from_orm(request.auth)
