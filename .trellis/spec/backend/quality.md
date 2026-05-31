# Backend Quality Checklist

Use this checklist after backend changes.

## Current Source Status

No FastAPI application source exists yet in `D:\g-code\backend`. Until it is scaffolded, backend code verification commands are expected targets rather than runnable commands.

## Expected Commands After Scaffold

```bash
python -m compileall app
python -m pytest
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

If a different package name or test runner is chosen, update this file and [index.md](./index.md).

## Review Checklist

- FastAPI routes use Pydantic request and response models.
- Route functions are thin and delegate to services.
- LangChain/provider calls are isolated behind service modules.
- MySQL is the production database target; no default SQLite shortcut was introduced.
- Redis usage has clear TTLs and does not store large image blobs.
- Watchdog observers start explicitly and have shutdown handling.
- JSON response shapes are stable and documented.
- Destructive operations have confirmation, audit logging, and rollback/restoration notes.
- Database schema changes include forward and rollback SQL.
- Secrets are read from environment variables and not committed.

## Manual Smoke Test Once App Exists

1. Start Uvicorn.
2. Call `GET /api/v1/health`.
3. Verify OpenAPI docs load at `/docs` in development.
4. Exercise auth/login if implemented.
5. Create a generation job with valid payload.
6. Verify job status/result response matches the documented schema.
7. Confirm logs include request id and job id without leaking secrets.
