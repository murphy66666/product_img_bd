from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.schemas.auth import UserProfile
from app.services.auth_service import AuthService, get_auth_service
from app.services.token_store import token_store

bearer_scheme = HTTPBearer(auto_error=False)


async def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


async def get_current_user(
    token: str = Depends(get_bearer_token),
    service: AuthService = Depends(get_auth_service),
) -> UserProfile:
    user_id = decode_access_token(token)
    if not await token_store.validate_and_refresh(token, user_id):
        settings = get_settings()
        if settings.app_env.lower() != "production" and not token_store.is_revoked(token):
            await token_store.save(token, user_id)
            return await service.current_user(user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await service.current_user(user_id)
