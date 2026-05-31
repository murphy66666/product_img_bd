# LangChain Integration

This backend uses Python LangChain for AI workflow orchestration. It does not use the Vercel AI SDK.

## Placement

Keep LangChain code behind service modules, for example:

```text
app/services/langchain_service.py
app/services/generation_service.py
```

FastAPI route functions should call services and should not contain prompt construction, provider client setup, or chain orchestration directly.

## Configuration

Provider names, model ids, API keys, timeouts, and feature flags must come from environment-backed settings in `app/core/config.py`.

Do not commit provider keys.

## Generation Workflow

Expected flow for AI product image generation:

1. Validate request and uploaded/source image metadata.
2. Persist a generation job with `pending` status.
3. Build a prompt from product/category/config data.
4. Invoke LangChain/provider code through a service.
5. Store generated image URLs/metadata.
6. Update job status to `succeeded`, `failed`, or `partial_failed`.
7. Return stable JSON for frontend polling/result rendering.

## Prompt Rules

- Keep prompt templates in service/helper files, not route functions.
- Version important prompts when output behavior matters.
- Keep user prompt text separate from system/instruction prompt text.
- Validate prompt length before invoking providers.
- Log only truncated prompt excerpts when needed.

## Error Handling

Handle provider failures explicitly:

- rate limit
- timeout
- invalid credentials
- content policy rejection
- malformed provider response
- storage failure after generation

Map these to stable backend job statuses and client-safe error messages.

## Retries

Use bounded retries with backoff for transient provider/network failures. Do not retry validation errors or policy rejections.

## Avoid

- Do not put API keys in frontend code.
- Do not import JavaScript AI SDK patterns into this Python backend.
- Do not block the Uvicorn event loop with long synchronous provider calls without offloading.
- Do not store large base64 image payloads in MySQL or Redis unless there is a documented reason.
