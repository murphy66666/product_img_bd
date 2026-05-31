# FastAPI API Routes

oRPC is not part of this backend stack. Keep this file as the API endpoint guidance file because the existing Trellis tree already references it.

## Current Decision

Use FastAPI route modules, not oRPC routers. Public API behavior should be defined with:

- FastAPI `APIRouter`
- Pydantic request and response models
- dependency-injected database/cache/auth resources
- stable JSON envelopes

## Route Pattern

```python
from fastapi import APIRouter, Depends
from app.schemas.generation import GenerationRequest, GenerationResponse
from app.services.generation_service import GenerationService, get_generation_service

router = APIRouter(prefix="/generation", tags=["generation"])

@router.post("/jobs", response_model=GenerationResponse)
async def create_generation_job(
    payload: GenerationRequest,
    service: GenerationService = Depends(get_generation_service),
) -> GenerationResponse:
    return await service.create_job(payload)
```

## Response Contract

Use stable JSON response models. Prefer an envelope for business operations:

```json
{
  "success": true,
  "data": {},
  "message": "ok"
}
```

For failures, use FastAPI `HTTPException` for protocol errors and a consistent response body for expected business failures. Document error codes before frontend integration.

## Endpoint Areas

Expected initial endpoints:

- `GET /api/v1/health`: process health and dependency probes.
- `POST /api/v1/auth/login`: authenticate user when backend auth exists.
- `POST /api/v1/generation/jobs`: create an AI image generation job.
- `GET /api/v1/generation/jobs/{job_id}`: fetch job status/result.
- `GET /api/v1/gallery`: list generated images for the current user.
- `DELETE /api/v1/gallery/{image_id}`: delete or hide a generated image with audit logging.

## Rules

- Do not return raw ORM rows directly from routes.
- Do not call LangChain directly in route functions.
- Do not expose internal exception messages to clients.
- Do not change response field names casually after frontend integration.
- Do not add GraphQL/oRPC/React Query assumptions to this Python backend.

## Scenario: Creating Chat Sessions

### 1. Scope / Trigger
- Trigger: `POST /api/v1/sessions` is a cross-layer contract used by the Vue sidebar to create a new conversation and deep-link to it.

### 2. Signatures
- API: `POST /api/v1/sessions`
- Request: `{"category": "main" | "detail", "title"?: string}`
- Response: `ApiResponse[ChatSession]`
- DB writes: `generation_sessions` plus the initial assistant row in `generation_messages`.

### 3. Contracts
- The route must derive `user_id` from `get_current_user`; clients must not send `user_id`.
- A successful response means the session and initial message were committed to MySQL.
- Returned `ChatSession` keeps frontend field aliases: `createdAt`, `aspectRatio`, `uploadedImageUrl`.

### 4. Validation & Error Matrix
- Missing/invalid bearer token -> `401`.
- Invalid `category` -> FastAPI/Pydantic validation error.
- MySQL/session write failure -> `503` with `detail="Session database is unavailable"`.

### 5. Good/Base/Bad Cases
- Good: Authenticated request creates a `main` session, persists it, and returns one assistant welcome message.
- Base: Empty title uses the default category-specific title.
- Bad: Database unavailable must not return a fake successful session.

### 6. Tests Required
- Route test for successful session creation with persisted session shape.
- Route test for database-unavailable failure returning `503`.

### 7. Wrong vs Correct

#### Wrong
```python
try:
    await repository.create_session(...)
except DatabaseError:
    return ChatSession(...)
```

#### Correct
```python
try:
    return await repository.create_session(...)
except RuntimeError as exc:
    raise HTTPException(status_code=503, detail="Session database is unavailable") from exc
```
