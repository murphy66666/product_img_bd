# Python Type Safety and API Schemas

Use Python type hints and Pydantic models as the backend contract. FastAPI uses these models for validation and OpenAPI generation.

## Rules

- Every request body must have a Pydantic model.
- Every JSON response should have a `response_model`.
- Keep schemas in `app/schemas/`, not inline inside route functions once reused.
- Use `Literal` or `Enum` for constrained fields like generation category, status, model, and aspect ratio.
- Avoid `dict[str, Any]` in public responses unless the field is intentionally arbitrary metadata and documented.
- Convert ORM/database rows into response schemas before returning.

## Suggested Common Models

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    message: str | None = None
```

## Generation Schema Concepts

Expected frontend-facing fields:

- `category`: `main` or `detail`
- `model`: model identifier string
- `aspect_ratio`: string such as `1:1` or `9:16`
- `resolution`: string such as `2k` or `4k`
- `quantity`: positive integer with mode-specific limits
- `prompt`: non-empty string
- `source_image_id` or `source_image_url`

## Scenario: New Session Tutorial Dialogue

### 1. Scope / Trigger
- Trigger: New image-generation sessions should include a short tutorial dialogue so the frontend can show users how to write a useful generation prompt.

### 2. Signatures
- API: `POST /api/v1/sessions`
- Response field: `data.messages: list[ChatMessage]`
- Helper: `app.services.repository._tutorial_messages(category, created_at)`

### 3. Contracts
- New sessions include three tutorial messages in order: assistant intro, user example prompt, assistant tip.
- Each tutorial message sets `payload.tutorial = true`.
- `category = "main"` uses a `1:1` main-image prompt example.
- `category = "detail"` uses a `9:16` detail-image prompt example.
- Messages must still use the stable `ChatMessage` schema: `id`, `sender`, `text`, `createdAt`, `type`, `payload`.

### 4. Validation & Error Matrix
- Unsupported `category` is rejected by `SessionCreateRequest` before repository code runs.
- Missing message payload tutorial marker should fail unit coverage for tutorial messages.

### 5. Good/Base/Bad Cases
- Good: frontend receives assistant/user/assistant tutorial messages immediately after creating a session.
- Base: listing sessions returns the persisted tutorial messages in chronological order.
- Bad: tutorial content is hard-coded in a route body or returned outside the `ChatMessage` schema.

### 6. Tests Required
- Unit test for `_tutorial_messages("main", created_at)` asserting sender order, tutorial payload marker, and main-image prompt content.
- Existing session route tests should continue to validate the stable response envelope.

### 7. Wrong vs Correct

#### Wrong
```python
return {"messages": ["upload image first"]}
```

#### Correct
```python
ChatMessage(
    id=message_id,
    sender="assistant",
    text="...",
    createdAt=created_at,
    payload={"tutorial": True},
)
```

## Validation

- Validate file type and size before storing uploads.
- Validate `quantity` server-side even if the frontend clamps it.
- Validate prompt length before sending to LangChain providers.
- Normalize timestamps to ISO 8601 strings in API responses.

## Static Checks

When tooling exists, prefer:

```bash
python -m compileall app
python -m pytest
```

If mypy or pyright is added, document the exact command in [quality.md](./quality.md).
