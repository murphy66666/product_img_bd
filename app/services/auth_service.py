from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import create_access_token
from app.db.mysql import mysql_sessions
from app.schemas.auth import LoginData, LoginRequest, UserProfile
from app.services.token_store import token_store

try:
    import bcrypt
except ImportError:  # pragma: no cover - dependency is provided by passlib[bcrypt]
    bcrypt = None


class AuthService:
    async def login(self, payload: LoginRequest) -> LoginData:
        user = await self._find_database_user(payload.phone)
        if user is not None:
            if not self._verify_password(payload.password, user.get("password_hash")):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
            profile = UserProfile(
                id=user["id"],
                name=user["name"],
                avatar=user["avatar"] or "",
                balance=user["balance"],
                role=user["role"],
            )
            token = create_access_token(profile.id)
            await token_store.save(token, profile.id)
            return LoginData(token=token, user=profile)

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    async def current_user(self, user_id: str) -> UserProfile:
        user = await self._find_database_user_by_id(user_id)
        if user is not None:
            return UserProfile(
                id=user["id"],
                name=user["name"],
                avatar=user["avatar"] or "",
                balance=user["balance"],
                role=user["role"],
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")

    async def logout(self, token: str) -> None:
        await token_store.delete(token)

    async def _find_database_user(self, login_name: str) -> dict[str, Any] | None:
        try:
            async for session in mysql_sessions.session():
                result = await session.execute(
                    text(
                        """
                        SELECT id, phone, name, avatar, balance, role, password_hash
                        FROM users
                        WHERE phone = :login_name OR name = :login_name
                        LIMIT 1
                        """
                    ),
                    {"login_name": login_name},
                )
                row = result.mappings().first()
                return dict(row) if row is not None else None
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError):
            return None
        return None

    async def _find_database_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        try:
            async for session in mysql_sessions.session():
                result = await session.execute(
                    text(
                        """
                        SELECT id, phone, name, avatar, balance, role, password_hash
                        FROM users
                        WHERE id = :user_id
                        LIMIT 1
                        """
                    ),
                    {"user_id": user_id},
                )
                row = result.mappings().first()
                return dict(row) if row is not None else None
        except (SQLAlchemyError, OSError, RuntimeError, AttributeError):
            return None
        return None

    def _verify_password(self, plain_password: str, password_hash: str | None) -> bool:
        if bcrypt is None or not password_hash:
            return False
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def get_auth_service() -> AuthService:
    return AuthService()
