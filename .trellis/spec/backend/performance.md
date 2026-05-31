# Performance Guidelines

FastAPI performance depends on keeping async paths non-blocking and moving expensive work out of request handlers.

## Async Rules

- Use `async def` for routes that await database, Redis, file, or AI calls.
- Do not call blocking filesystem, CPU-heavy, or network code directly in the event loop.
- Use background tasks, worker processes, or thread pools for blocking work.
- Keep route bodies thin and delegate orchestration to services.

## AI Generation Jobs

Image generation can be slow. Prefer job-based APIs:

1. Client creates a generation job.
2. Backend persists a pending job.
3. Worker/service performs upload, LangChain/provider calls, and storage.
4. Client polls or subscribes to job status.

Do not make long provider calls hold open a request unless the endpoint is explicitly designed for streaming.

## Redis Usage

Use Redis for:

- rate limiting
- short-lived session/cache data
- idempotency keys
- job locks or lightweight coordination
- caching provider/model metadata

Set TTLs on cache keys. Avoid storing large image blobs in Redis.

## Database Performance

- Paginate list endpoints.
- Add indexes for common filters: user id, job status, category, created time.
- Avoid loading generated image binary data from MySQL in list endpoints; store URLs or object references.
- Keep external AI calls outside database transactions.

## Watchdog Performance

Directory monitoring can produce bursty events. Debounce duplicate file events and hand work to a queue/service when processing is expensive.

## Uploads and Files

- Validate file size before processing.
- Stream large uploads where possible.
- Store file metadata in MySQL and bytes in disk/object storage, not in JSON response bodies.
