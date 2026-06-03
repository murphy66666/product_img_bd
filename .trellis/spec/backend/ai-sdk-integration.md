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

## Scenario: GPT Image 2 Edit-Image Provider

### 1. Scope / Trigger
- Trigger: Product image generation uses the OpenAI-compatible image edit endpoint because the user uploads one or more product/reference images.

### 2. Signatures
- Backend API: `POST /api/v1/generation/jobs`
- Provider endpoint: `POST {normalized OPENAI_BASE_URL}/images/edits`; normalization appends `/v1` when the configured base URL does not already end with `/v1`.
- Multipart provider fields: `model`, `prompt`, repeated `image[]`, `size`, `quality`, `n`, `output_format`, `stream`.
- Environment keys: `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `GENERATED_IMAGE_STORAGE_DIR`.

### 3. Contracts
- Frontend sends uploaded backend file IDs as `sourceImageIds`; it must not send workstation file paths.
- Backend resolves each upload ID to a local file and sends repeated `image[]` multipart parts.
- Provider request metadata may be stored in JSON, but raw image bytes and full `b64_json` values must not be stored in MySQL.
- Provider `data[].url` responses are downloaded and saved locally; `data[].b64_json` responses are decoded and saved locally.
- Downloaded provider images must be validated before replacing the local target file: compare `Content-Length` when present, reject empty/oversized payloads, and verify PNG `IEND`, JPEG EOF, or WebP RIFF declared size for those formats.
- Frontend receives local `publicUrl` values for display.
- `OPENAI_BASE_URL` may be configured as `https://www.llmgateway.cn` or `https://www.llmgateway.cn/v1`; both must call `https://www.llmgateway.cn/v1/images/edits`.

### 4. Validation & Error Matrix
- Missing `sourceImageIds` for `gpt-image-2` -> `400`.
- Missing `OPENAI_API_KEY` for `gpt-image-2` -> job fails with a client-safe error; do not route the request to `MockImageProvider`.
- Missing `OPENAI_BASE_URL` for `gpt-image-2` -> job fails with a client-safe error; do not route the request to `MockImageProvider`.
- Provider `401` or other HTTP error -> parse the provider JSON error/message and store a client-safe `errorMessage`; do not collapse every provider failure to the generic text `Generation failed`.
- Unknown upload ID -> generation job fails with a client-safe error.
- Unsupported `size`, `quality`, or `outputFormat` -> validation error before provider call.
- Provider returns fewer images than `n` -> persist `requestedCount` and `returnedCount`; choose `succeeded` or `partial_failed` based on saved result count and product policy.
- Provider image download/save failure -> `failed` or `partial_failed`.
- Provider image URL short-read, missing PNG `IEND`, missing JPEG EOF, or mismatched WebP declared size -> reject the image and fail the job with a client-safe storage/download error; do not persist a truncated local file.

### 5. Good/Base/Bad Cases
- Good: Three uploaded image IDs produce a multipart edit request with three `image[]` parts and persisted local generated images.
- Base: Provider returns one composite image for `n=3`; backend records `requestedCount=3` and `returnedCount=1`.
- Bad: Backend sends only JSON with `sourceImageUrl` to `/images/edits`.
- Bad: `get_provider("gpt-image-2")` silently returns `MockImageProvider` when OpenAI credentials are missing.
- Bad: `OPENAI_BASE_URL=https://www.llmgateway.cn` calls `https://www.llmgateway.cn/images/edits` and receives an authentication/path error even though the same key works with `/v1/images/edits`.

### 6. Tests Required
- Route test asserting `gpt-image-2` payload accepts `sourceImageIds`, `size`, `quality`, `n`, and trimmed `outputFormat`.
- Provider factory test asserting `gpt-image-2` requires `OPENAI_API_KEY` and `OPENAI_BASE_URL`, and returns `OpenAIImageEditProvider` only when both are configured.
- Provider URL tests asserting bare gateway domains and `/v1` base URLs both resolve to `/v1/images/edits`.
- Provider error parsing test asserting gateway JSON errors become the job `errorMessage`.
- Upload test asserting returned upload `id` can be used as a source image ID.
- Storage unit test for daily folder path and local public URL when practical.
- Storage regression tests for provider URL short-read and PNG/JPEG/WebP completeness validation.

### 7. Wrong vs Correct

#### Wrong
```python
payload = {"image": "C:/Users/example/product.png"}
```

#### Correct
```python
files = [("image[]", open(upload_path, "rb"))]
data = {"model": "gpt-image-2", "prompt": prompt, "size": "1024x1024", "n": "3"}
```
