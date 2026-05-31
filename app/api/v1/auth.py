from fastapi import APIRouter, Depends

from app.api.deps import get_bearer_token, get_current_user
from app.schemas.auth import LoginData, LoginRequest, UserProfile
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ApiResponse[LoginData])
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[LoginData]:
    return ApiResponse(success=True, data=await service.login(payload), message="ok")


@router.get("/me", response_model=ApiResponse[UserProfile])
async def me(current_user: UserProfile = Depends(get_current_user)) -> ApiResponse[UserProfile]:
    return ApiResponse(success=True, data=current_user, message="ok")


@router.post("/logout", response_model=ApiResponse[dict[str, bool]])
async def logout(
    token: str = Depends(get_bearer_token),
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[dict[str, bool]]:
    await service.logout(token)
    return ApiResponse(success=True, data={"loggedOut": True}, message="ok")
