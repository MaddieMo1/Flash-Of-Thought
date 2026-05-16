from fastapi import APIRouter, Depends

from app.models.user import TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.auth_service import auth_service, get_current_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, summary="Register a user")
async def register_user(payload: UserRegister):
    user = auth_service.create_user(payload.email, payload.password)
    token = auth_service.create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": auth_service.public_user(user),
    }


@router.post("/login", response_model=TokenResponse, summary="Login and get an access token")
async def login_user(payload: UserLogin):
    user = auth_service.authenticate_user(payload.email, payload.password)
    token = auth_service.create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": auth_service.public_user(user),
    }


@router.get("/me", response_model=UserResponse, summary="Get the current user")
async def get_me(current_user=Depends(get_current_user)):
    return auth_service.public_user(current_user)
