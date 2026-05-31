# Backend Directory Structure

Current repository fact: `D:\g-code\backend` has no application package yet. When implementing the backend, create a modular FastAPI structure instead of putting everything in one file.

## Recommended Layout

```text
backend/
  app/
    __init__.py
    main.py                    # FastAPI app creation and router registration
    api/
      __init__.py
      v1/
        __init__.py
        router.py              # include all v1 routers
        auth.py
        generation.py
        gallery.py
        health.py
    core/
      __init__.py
      config.py                # environment settings
      logging.py               # logging configuration
      security.py              # password/JWT/session helpers
    db/
      __init__.py
      mysql.py                 # engine/session/pool setup
      migrations/              # SQL migration files if no migration tool exists
    models/
      __init__.py              # ORM models if an ORM is used
    schemas/
      __init__.py
      auth.py
      generation.py
      gallery.py
      common.py
    services/
      __init__.py
      auth_service.py
      generation_service.py
      image_storage.py
      langchain_service.py
      gallery_service.py
    cache/
      __init__.py
      redis.py
    watchers/
      __init__.py
      image_directory_watcher.py
    utils/
      __init__.py
  tests/
  requirements.txt
  .env.example
```

## Module Boundaries

- `app/main.py`: create the FastAPI app, configure middleware, include routers, and expose `app` for Uvicorn.
- `api/v1/`: route functions only. Validate inputs, call services, and return response schemas.
- `schemas/`: Pydantic request/response models. This is the public API contract.
- `services/`: business logic, LangChain calls, storage, and workflow orchestration.
- `db/`: MySQL connection, sessions, and migrations.
- `cache/`: Redis client setup and cache helpers.
- `watchers/`: watchdog observers and handlers. Start them explicitly from an app lifespan hook or worker command.
- `core/`: config, logging, security, and cross-cutting infrastructure.

## Rules

- Do not put routes, SQL, LangChain prompts, and file watching in one large module.
- Keep router modules thin and service modules testable.
- Do not open database, Redis, or watchdog connections at import time. Initialize through app startup/lifespan or dependency providers.
- Keep generated/uploaded image file handling behind an `image_storage` service so local disk, object storage, or CDN changes do not rewrite route code.
- Keep API versioning under `/api/v1` once endpoints are public.

## Current Source Status

Because no backend app files exist yet, future code changes should first scaffold the app layout, dependencies, `.env.example`, and a health endpoint before adding product-specific generation workflows.
