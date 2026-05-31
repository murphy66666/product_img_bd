from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.schemas.auth import UserProfile
from app.schemas.common import ApiResponse, PaginationMeta
from app.schemas.session import (
    ChatSession,
    MessageListData,
    SessionCreateRequest,
    SessionListData,
    SessionRenameRequest,
)
from app.services.repository import repository
from app.services.session_service import SessionService, get_session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=ApiResponse[SessionListData])
async def list_sessions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    current_user: UserProfile = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
) -> ApiResponse[SessionListData]:
    sessions, total = await service.list_sessions(current_user.id, page, page_size)
    return ApiResponse(
        success=True,
        data=SessionListData(
            sessions=sessions,
            pagination=PaginationMeta(page=page, pageSize=page_size, total=total),
        ),
        message="ok",
    )


@router.post("", response_model=ApiResponse[ChatSession])
async def create_session(
    payload: SessionCreateRequest,
    current_user: UserProfile = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
) -> ApiResponse[ChatSession]:
    return ApiResponse(success=True, data=await service.create_session(current_user.id, payload), message="ok")


@router.patch("/{session_id}", response_model=ApiResponse[ChatSession])
async def rename_session(
    session_id: str,
    payload: SessionRenameRequest,
    current_user: UserProfile = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
) -> ApiResponse[ChatSession]:
    session = await service.rename_session(current_user.id, session_id, payload)
    return ApiResponse(success=True, data=session, message="ok")


@router.delete("/{session_id}", response_model=ApiResponse[dict[str, bool]])
async def delete_session(
    session_id: str,
    current_user: UserProfile = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
) -> ApiResponse[dict[str, bool]]:
    await service.delete_session(current_user.id, session_id)
    return ApiResponse(success=True, data={"deleted": True}, message="ok")


@router.get("/{session_id}/messages", response_model=ApiResponse[MessageListData])
async def list_messages(
    session_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> ApiResponse[MessageListData]:
    messages = await repository.list_messages(current_user.id, session_id)
    return ApiResponse(success=True, data=MessageListData(messages=messages), message="ok")
