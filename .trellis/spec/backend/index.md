# Backend Development Guidelines Index

> Tech stack: Python 3 + FastAPI + Uvicorn + LangChain. Project infrastructure targets MySQL, Redis, and watchdog-based directory monitoring.

This backend supports the Vue frontend as an API service for AI product image generation. At the time these specs were written, `D:\g-code\backend` contains Trellis/agent configuration and `AGENTS.md`, but no actual FastAPI application source files yet. These guidelines define the expected backend shape for implementation work.

## Documentation Files

| File | Purpose | When to Read |
| --- | --- | --- |
| [directory-structure.md](./directory-structure.md) | Expected FastAPI package layout and module boundaries | Starting backend implementation |
| [orpc-usage.md](./orpc-usage.md) | FastAPI route guidance; oRPC is not used | Creating or changing API endpoints |
| [type-safety.md](./type-safety.md) | Pydantic schemas, response contracts, typing rules | Defining request/response models |
| [database.md](./database.md) | MySQL-first persistence rules and migration discipline | Database work |
| [authentication.md](./authentication.md) | Session/token auth expectations for FastAPI | Auth work |
| [logging.md](./logging.md) | Python logging and request/job observability | Debugging and operations |
| [performance.md](./performance.md) | Async FastAPI, Redis, queues, and file watcher concerns | Scaling or slow paths |
| [ai-sdk-integration.md](./ai-sdk-integration.md) | LangChain integration for image-generation workflows | AI features |
| [quality.md](./quality.md) | Backend verification checklist | Before handoff |

## Core Rules

- Use FastAPI routers and Pydantic models for all public JSON APIs.
- Run with Uvicorn; keep ASGI app creation importable and side-effect-light.
- Use LangChain only behind service boundaries, not directly inside route bodies.
- Use MySQL for production persistence. Do not default to SQLite.
- Use Redis for cache, rate limits, session/cache helpers, and lightweight job coordination where appropriate.
- Use watchdog only in a dedicated watcher service/module, not as import-time global behavior.
- Keep JSON response formats stable because the frontend and other systems may integrate against them.
- Never render or hard-code HTML from the backend. The Vue frontend owns UI.
- For database schema changes, provide complete SQL migration and rollback SQL.
- For destructive operations, require confirmation, operation logs, and a rollback plan.

## Expected Runtime Commands

These are target commands once the backend app exists:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

If the actual package name differs from `app`, update this index and [directory-structure.md](./directory-structure.md) together.
