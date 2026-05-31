from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas.auth import UserProfile
from app.schemas.common import ApiResponse
from app.schemas.generation import (
    GenerationJobCreateRequest,
    GenerationJobData,
    ModelListData,
    ProviderStatusData,
)
from app.services.generation_queue import enqueue_generation_job
from app.services.generation_service import GenerationService, get_generation_service

router = APIRouter(prefix="/generation", tags=["generation"])


@router.get("/models", response_model=ApiResponse[ModelListData])
async def list_models(
    _current_user: UserProfile = Depends(get_current_user),
    service: GenerationService = Depends(get_generation_service),
) -> ApiResponse[ModelListData]:
    return ApiResponse(success=True, data=ModelListData(models=service.list_models()), message="ok")


@router.get("/providers/status", response_model=ApiResponse[ProviderStatusData])
async def list_provider_statuses(
    _current_user: UserProfile = Depends(get_current_user),
    service: GenerationService = Depends(get_generation_service),
) -> ApiResponse[ProviderStatusData]:
    return ApiResponse(
        success=True,
        data=ProviderStatusData(providers=service.list_provider_statuses()),
        message="ok",
    )


@router.post("/jobs", response_model=ApiResponse[GenerationJobData])
async def create_generation_job(
    payload: GenerationJobCreateRequest,
    current_user: UserProfile = Depends(get_current_user),
    service: GenerationService = Depends(get_generation_service),
) -> ApiResponse[GenerationJobData]:
    job = await service.create_job(current_user.id, payload)
    await enqueue_generation_job(current_user.id, job.id, payload)
    return ApiResponse(success=True, data=GenerationJobData(job=job), message="ok")


@router.get("/jobs/{job_id}", response_model=ApiResponse[GenerationJobData])
async def get_generation_job(
    job_id: str,
    current_user: UserProfile = Depends(get_current_user),
    service: GenerationService = Depends(get_generation_service),
) -> ApiResponse[GenerationJobData]:
    job = await service.get_job(current_user.id, job_id)
    return ApiResponse(success=True, data=GenerationJobData(job=job), message="ok")
