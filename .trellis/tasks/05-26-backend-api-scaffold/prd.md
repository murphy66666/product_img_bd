# Backend API Scaffold for Frontend Generation

## Goal

Build the first backend implementation in `D:\g-code\backend` to support the existing Vue frontend in `D:\g-code\frontend`.

The backend must use:

- Python 3
- uv package management
- FastAPI
- Uvicorn
- LangChain service boundary
- MySQL 8+ as the database target
- Redis-ready configuration
- watchdog-ready module structure

## Current Frontend Behaviors to Support

The Vue frontend currently simulates these features locally with Pinia and localStorage:

- Phone/password login
- Current user info, theme, and balance display
- Generation modes: `main` and `detail`
- Session list, create, rename, delete, active session messages
- Generation config: model, aspect ratio, resolution, quantity, prompt, uploaded/source image URL
- Generation progress and result image grid
- Gallery list and image delete/download metadata

The backend should expose stable JSON APIs so the frontend can migrate from local mock state to API-backed state.

## Required First Implementation Scope

1. Create a uv-managed Python project.
2. Scaffold FastAPI app structure under `app/`.
3. Add config loading with Pydantic settings and `.env.example`.
4. Add CORS support for the Vite frontend.
5. Add health endpoint: `GET /api/v1/health`.
6. Add mock auth endpoints:
   - `POST /api/v1/auth/login`
   - `GET /api/v1/auth/me`
7. Add session APIs backed by in-memory repository for first-stage local run:
   - list sessions
   - create session
   - rename session
   - delete session
   - list messages for a session
8. Add gallery APIs backed by in-memory repository:
   - list gallery images
   - delete image
9. Add generation job APIs:
   - `POST /api/v1/generation/jobs`
   - `GET /api/v1/generation/jobs/{job_id}`
10. Add multi-model provider abstraction with mock providers for:
   - `gpt-images-1.5`
   - `gemini-banana`
   - `jimeng`
   - `happyhouse`
11. Keep a LangChain service boundary, but do not require real provider credentials in the first implementation.
12. Add MySQL 8+ schema SQL and rollback SQL under a migration folder. Do not use SQLite.
13. Add basic pytest coverage for health, model listing, and generation job creation.

## API Response Contract

Use a stable envelope:

```json
{
  "success": true,
  "data": {},
  "message": "ok"
}
```

## Model Behavior

All first-stage model adapters may return mock images. They must share a common interface so real APIs can replace them later without changing routes.

Each model has capabilities:

- provider key
- model key
- display name
- supported aspect ratios
- supported resolutions
- max quantity
- image input support

Backend validates requested model capabilities before creating a job.

## Non-Goals for First Implementation

- No real OpenAI/Gemini/Jimeng/Alibaba provider calls yet.
- No frontend changes yet unless explicitly requested later.
- No real MySQL persistence required in runtime for this first scaffold, but SQL must be provided and the code must not default to SQLite.
- No production authentication; mock login is acceptable for frontend migration.

## Done Criteria

- `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` can start the backend after dependencies are installed.
- `GET /api/v1/health` returns success.
- `/docs` exposes the API.
- A generation job can be created with each supported model key.
- Tests for core endpoints pass if dependencies are installed.
- MySQL 8+ schema and rollback SQL are present.
