# Logging and Observability

Use Python logging consistently. Avoid `print()` for backend runtime diagnostics.

## Logging Setup

Create logging configuration under `app/core/logging.py`. Configure:

- timestamp
- level
- logger name
- request id or correlation id when available
- user id/job id for business workflows when safe

JSON logs are preferred for production, but plain structured messages are acceptable during early implementation if fields are consistent.

## Request Logging

Add middleware for request id and basic request timing once the app exists. Do not log sensitive headers, tokens, passwords, or raw uploaded image data.

Useful fields:

- `request_id`
- `method`
- `path`
- `status_code`
- `duration_ms`
- `user_id` when authenticated

## AI Job Logging

For generation workflows, log:

- job id
- user id
- selected model/provider
- quantity
- status transitions
- provider latency
- retry count
- failure category

Never log full secrets or unbounded prompts. If prompt logging is needed for debugging, truncate and mark it explicitly.

## Watchdog Logging

Directory watcher handlers should log:

- watched path
- event type
- file path
- action taken
- errors and retry decisions

Watchers must not silently swallow exceptions.

## Error Handling

- Catch expected provider/database/cache errors at service boundaries.
- Convert client-facing failures into stable FastAPI responses.
- Preserve full exception details in server logs only.
- Include enough context to debug without leaking private data.
