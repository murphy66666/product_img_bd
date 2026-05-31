from fastapi import HTTPException, status

from app.schemas.session import ChatSession, SessionCreateRequest, SessionRenameRequest
from app.services.repository import repository


class SessionService:
    async def list_sessions(self, user_id: str, page: int, page_size: int) -> tuple[list[ChatSession], int]:
        return await repository.list_sessions(user_id, page, page_size)

    async def create_session(self, user_id: str, payload: SessionCreateRequest) -> ChatSession:
        try:
            return await repository.create_session(user_id, payload.category, payload.title)
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Session database is unavailable",
            ) from exc

    async def rename_session(
        self,
        user_id: str,
        session_id: str,
        payload: SessionRenameRequest,
    ) -> ChatSession:
        session = await repository.rename_session(user_id, session_id, payload.title)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return session

    async def delete_session(self, user_id: str, session_id: str) -> None:
        if not await repository.delete_session(user_id, session_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")


def get_session_service() -> SessionService:
    return SessionService()
