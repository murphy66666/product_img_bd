# GPT Image 2 Edit Image Integration Plan

## Goal

Use the LLM Gateway OpenAI-compatible image edit endpoint as the main generation flow:

```http
POST https://www.llmgateway.cn/v1/images/edits
```

The request is `multipart/form-data`, not JSON, and it supports multiple uploaded product/reference images through repeated `image[]` fields.

This plan covers frontend changes, backend changes, local generated-image storage, MySQL persistence, deletion, audit, and billing metadata.

## Reference Curl

The target provider request shape is:

```bash
curl --location 'https://www.llmgateway.cn/v1/images/edits' \
  --header 'Authorization: Bearer ${OPENAI_API_KEY}' \
  --form 'model="gpt-image-2"' \
  --form 'prompt="根据上传图片生成3张商品详情图，1.本书优势：纸张、装订、内容，2.本书内容，3.和其他图书对比"' \
  --form 'image[]=@"/path/to/source-1.png"' \
  --form 'image[]=@"/path/to/source-2.jpg"' \
  --form 'image[]=@"/path/to/source-3.jpg"' \
  --form 'size="1024x1024"' \
  --form 'quality="high"' \
  --form 'n="3"' \
  --form 'output_format="png"' \
  --form 'stream="false"'
```

Important normalization:

- API keys must come from `.env`; never store them in frontend or commit them.
- `output_format` must be trimmed. The sample has a newline after `png`; backend should normalize it to `png`.
- `stream` should be sent as boolean-like `false` or string `false` according to gateway compatibility, but backend request schema should store it as a boolean.
- `n=3` means requested output count. The actual provider response may return fewer records, so backend must persist both requested count and returned count.

## Reference Response

Observed provider response:

```json
{
  "created": 1780292079,
  "data": [
    {
      "url": "https://oss.filenest.top/uploads/e4ae91b2-635e-48fb-91a3-9033d34e2793.png"
    }
  ],
  "usage": {
    "total_tokens": 2541,
    "input_tokens": 1776,
    "output_tokens": 765,
    "input_tokens_details": {
      "text_tokens": 96,
      "image_tokens": 1680
    }
  }
}
```

Primary response path for this gateway:

- `data[].url` is returned.
- The URL points to OSS.
- Backend must download the OSS image and save a local copy.
- Frontend should display the backend local public URL, not the OSS URL.

Compatibility fallback:

- If another compatible provider returns `data[].b64_json`, backend should decode base64 and save the decoded image bytes locally.

## Frontend Plan

### UI Model

Only expose GPT Image 2 for this flow.

Request model value:

```ts
model: 'gpt-image-2'
```

If the UI still displays `gpt-images-2`, keep that only as a label. The request value should be `gpt-image-2`.

### UI Inputs

The generation panel should support:

- `prompt`: required edit instruction
- `sourceImages`: required, one or more uploaded images
- `size`: default `1024x1024`
- `quality`: default `high`
- `n`: default `3`
- `outputFormat`: default `png`
- `stream`: default `false`, hidden unless streaming is implemented
- `sessionId`: active session

Recommended controls:

- Multiple image uploader for product/reference images
- Prompt textarea
- Size select: initially `1024x1024`
- Quality select: `low`, `medium`, `high`, `auto` if supported by gateway
- Output count stepper/slider mapped to `n`
- Output format select: `png`, later `jpeg`, `webp`

### Frontend Request To Backend

The frontend should upload source images first and then create a generation job using uploaded file IDs.

Recommended backend job request:

```json
{
  "model": "gpt-image-2",
  "prompt": "根据上传图片生成3张商品详情图，1.本书优势：纸张、装订、内容，2.本书内容，3.和其他图书对比",
  "sourceImageIds": ["upload-1", "upload-2", "upload-3"],
  "size": "1024x1024",
  "quality": "high",
  "n": 3,
  "outputFormat": "png",
  "stream": false,
  "sessionId": "session-id"
}
```

Frontend should not send local Windows paths to the backend. Browser file paths such as `C:/Users/...` are only valid in manual curl tests, not production browser requests.

### Frontend Files To Change Later

- `D:\g-code\frontend\src\api\generation.ts`
  - Add `sourceImageIds`, `size`, `quality`, `n`, `outputFormat`, `stream`
  - Map `outputFormat` to backend camelCase
- `D:\g-code\frontend\src\api\uploads.ts`
  - Ensure upload response includes stable upload ID and preview URL
- `D:\g-code\frontend\src\components\ConfigPanel.vue`
  - Replace single source image behavior with multi-image upload
  - Require at least one source image before generation
  - Add `size`, `quality`, `n`, `outputFormat` controls
  - Hide or lock model selection to GPT Image 2
- `D:\g-code\frontend\src\stores\chat.ts`
  - Store uploaded source image IDs in session config
  - Store preview URLs only for display

## Backend Plan

### Configuration

Add or confirm environment-backed settings:

```env
OPENAI_BASE_URL=https://www.llmgateway.cn/v1
OPENAI_API_KEY=
GENERATED_IMAGE_STORAGE_DIR=storage/gen_image
```

No API key should appear in source code, frontend code, migration files, or logs.

### Backend Job API

Keep the existing stable envelope:

```json
{
  "success": true,
  "data": {},
  "message": "ok"
}
```

Recommended endpoint:

```http
POST /api/v1/generation/jobs
```

Request body:

```json
{
  "model": "gpt-image-2",
  "prompt": "根据上传图片生成3张商品详情图，1.本书优势：纸张、装订、内容，2.本书内容，3.和其他图书对比",
  "sourceImageIds": ["upload-1", "upload-2", "upload-3"],
  "size": "1024x1024",
  "quality": "high",
  "n": 3,
  "outputFormat": "png",
  "stream": false,
  "sessionId": "session-id"
}
```

Backend validation:

- `model` must be `gpt-image-2`
- `prompt` is required
- `sourceImageIds` must contain at least one image
- every upload ID must belong to the current user
- uploaded files must still exist locally
- uploaded MIME type must be image-compatible
- `size` must be supported, initially `1024x1024`
- `quality` must be normalized, initially `high`
- `outputFormat` must be trimmed and normalized to `png`
- `n` must be within provider limit
- `stream=false` only until streaming is implemented

### Provider Request

Backend provider converts the JSON job into multipart form data:

```text
model=gpt-image-2
prompt=<prompt>
image[]=@<local upload file 1>
image[]=@<local upload file 2>
image[]=@<local upload file 3>
size=1024x1024
quality=high
n=3
output_format=png
stream=false
```

The backend must record the provider request metadata, but must not store raw image bytes in JSON.

Recommended `provider_request_payload`:

```json
{
  "endpoint": "/images/edits",
  "contentType": "multipart/form-data",
  "model": "gpt-image-2",
  "prompt": "根据上传图片生成3张商品详情图，1.本书优势：纸张、装订、内容，2.本书内容，3.和其他图书对比",
  "size": "1024x1024",
  "quality": "high",
  "n": 3,
  "output_format": "png",
  "stream": false,
  "imageFiles": [
    {
      "uploadId": "upload-1",
      "field": "image[]",
      "fileName": "source-1.png",
      "mimeType": "image/png",
      "fileSize": 123456,
      "checksumSha256": "..."
    }
  ]
}
```

### Provider Response

Recommended `provider_response_payload`:

```json
{
  "created": 1780292079,
  "requestedCount": 3,
  "returnedCount": 1,
  "responseTypes": ["url"],
  "data": [
    {
      "index": 0,
      "url": "https://oss.filenest.top/uploads/e4ae91b2-635e-48fb-91a3-9033d34e2793.png"
    }
  ],
  "usage": {
    "total_tokens": 2541,
    "input_tokens": 1776,
    "output_tokens": 765,
    "input_tokens_details": {
      "text_tokens": 96,
      "image_tokens": 1680
    }
  }
}
```

Do not treat `n=3` as guaranteed three records. The backend should use `len(data)` as the actual returned count.

### Local Image Save

For every returned `data[]` item:

1. If `url` exists, download the OSS image.
2. If `b64_json` exists, decode it.
3. Create daily folder on first save:

```text
storage/gen_image/YYYYMMDD
```

4. Save using:

```text
YYYYMMDDHHMMSS_{user_id}_{random}.{ext}
```

Example:

```text
storage/gen_image/20260601/20260601153022_admin_a8f39c.png
```

5. Calculate file size and SHA-256 checksum.
6. Store local metadata in `generated_images`.
7. Return local `publicUrl` to frontend:

```text
/storage/gen_image/20260601/20260601153022_admin_a8f39c.png
```

## Database Plan

Formal support for history gallery, deletion, audit, and billing requires MySQL records.

Do not store image binary or full base64 in MySQL.

### Migration Files

Recommended files:

```text
app/db/migrations/003_image_edits_storage_audit_billing.sql
app/db/migrations/003_image_edits_storage_audit_billing_rollback.sql
```

### Migration SQL

```sql
-- MySQL 8+ migration for GPT Image 2 edit-image request audit,
-- local generated-image storage, history gallery, soft delete, and billing metadata.

SET NAMES utf8mb4 COLLATE utf8mb4_0900_ai_ci;

ALTER TABLE generation_jobs
  ADD COLUMN provider_endpoint VARCHAR(255) NULL AFTER provider_job_id,
  ADD COLUMN provider_request_payload JSON NULL AFTER request_payload,
  ADD COLUMN provider_response_payload JSON NULL AFTER provider_request_payload,
  ADD COLUMN provider_created BIGINT NULL AFTER provider_response_payload,
  ADD COLUMN size VARCHAR(32) NULL AFTER resolution,
  ADD COLUMN quality VARCHAR(32) NULL AFTER size,
  ADD COLUMN output_format VARCHAR(32) NULL AFTER quality,
  ADD COLUMN stream TINYINT(1) NOT NULL DEFAULT 0 AFTER output_format,
  ADD COLUMN requested_count INT NULL AFTER quantity,
  ADD COLUMN returned_count INT NULL AFTER requested_count,
  ADD COLUMN source_upload_ids JSON NULL AFTER source_image_url,
  ADD COLUMN total_tokens INT NULL AFTER provider_created,
  ADD COLUMN input_tokens INT NULL AFTER total_tokens,
  ADD COLUMN output_tokens INT NULL AFTER input_tokens,
  ADD COLUMN input_text_tokens INT NULL AFTER output_tokens,
  ADD COLUMN input_image_tokens INT NULL AFTER input_text_tokens,
  ADD COLUMN billing_status VARCHAR(32) NOT NULL DEFAULT 'unbilled' AFTER input_image_tokens,
  ADD COLUMN billing_amount DECIMAL(12, 4) NULL AFTER billing_status,
  ADD COLUMN billing_currency VARCHAR(16) NULL AFTER billing_amount;

ALTER TABLE generated_images
  ADD COLUMN remote_url TEXT NULL AFTER url,
  ADD COLUMN local_path VARCHAR(1024) NULL AFTER remote_url,
  ADD COLUMN public_url VARCHAR(1024) NULL AFTER local_path,
  ADD COLUMN storage_disk VARCHAR(32) NOT NULL DEFAULT 'local' AFTER public_url,
  ADD COLUMN storage_date CHAR(8) NULL AFTER storage_disk,
  ADD COLUMN file_name VARCHAR(255) NULL AFTER storage_date,
  ADD COLUMN file_ext VARCHAR(16) NULL AFTER file_name,
  ADD COLUMN mime_type VARCHAR(128) NULL AFTER file_ext,
  ADD COLUMN file_size BIGINT NULL AFTER mime_type,
  ADD COLUMN checksum_sha256 CHAR(64) NULL AFTER file_size,
  ADD COLUMN source_upload_ids JSON NULL AFTER checksum_sha256,
  ADD COLUMN provider_response_item JSON NULL AFTER source_upload_ids,
  ADD COLUMN provider_data_index INT NULL AFTER provider_response_item,
  ADD COLUMN total_tokens INT NULL AFTER provider_data_index,
  ADD COLUMN input_tokens INT NULL AFTER total_tokens,
  ADD COLUMN output_tokens INT NULL AFTER input_tokens,
  ADD COLUMN input_text_tokens INT NULL AFTER output_tokens,
  ADD COLUMN input_image_tokens INT NULL AFTER input_text_tokens,
  ADD COLUMN billing_status VARCHAR(32) NOT NULL DEFAULT 'unbilled' AFTER input_image_tokens,
  ADD COLUMN billing_amount DECIMAL(12, 4) NULL AFTER billing_status,
  ADD COLUMN billing_currency VARCHAR(16) NULL AFTER billing_amount;

CREATE INDEX idx_generation_jobs_billing_status_created
  ON generation_jobs (billing_status, created_at);

CREATE INDEX idx_generation_jobs_provider_created
  ON generation_jobs (provider, model, created_at);

CREATE INDEX idx_generated_images_storage_date
  ON generated_images (storage_date);

CREATE INDEX idx_generated_images_user_deleted_created
  ON generated_images (user_id, deleted_at, created_at);

INSERT INTO operation_logs (user_id, action, target_type, target_id, detail)
VALUES (
  NULL,
  'migration_003_image_edits_storage_audit_billing',
  'migration',
  '003',
  JSON_OBJECT(
    'provider_endpoint', '/images/edits',
    'storage_dir', 'storage/gen_image/YYYYMMDD',
    'tables', JSON_ARRAY('generation_jobs', 'generated_images'),
    'purpose', 'record edit-image request, response, token usage, local image storage, gallery history, and billing metadata'
  )
);
```

### Rollback SQL

```sql
-- Rollback for 003_image_edits_storage_audit_billing.sql.
-- This rollback removes metadata columns only.
-- It does not delete files under storage/gen_image.

SET NAMES utf8mb4 COLLATE utf8mb4_0900_ai_ci;

DROP INDEX idx_generated_images_user_deleted_created ON generated_images;
DROP INDEX idx_generated_images_storage_date ON generated_images;
DROP INDEX idx_generation_jobs_provider_created ON generation_jobs;
DROP INDEX idx_generation_jobs_billing_status_created ON generation_jobs;

ALTER TABLE generated_images
  DROP COLUMN billing_currency,
  DROP COLUMN billing_amount,
  DROP COLUMN billing_status,
  DROP COLUMN input_image_tokens,
  DROP COLUMN input_text_tokens,
  DROP COLUMN output_tokens,
  DROP COLUMN input_tokens,
  DROP COLUMN total_tokens,
  DROP COLUMN provider_data_index,
  DROP COLUMN provider_response_item,
  DROP COLUMN source_upload_ids,
  DROP COLUMN checksum_sha256,
  DROP COLUMN file_size,
  DROP COLUMN mime_type,
  DROP COLUMN file_ext,
  DROP COLUMN file_name,
  DROP COLUMN storage_date,
  DROP COLUMN storage_disk,
  DROP COLUMN public_url,
  DROP COLUMN local_path,
  DROP COLUMN remote_url;

ALTER TABLE generation_jobs
  DROP COLUMN billing_currency,
  DROP COLUMN billing_amount,
  DROP COLUMN billing_status,
  DROP COLUMN input_image_tokens,
  DROP COLUMN input_text_tokens,
  DROP COLUMN output_tokens,
  DROP COLUMN input_tokens,
  DROP COLUMN total_tokens,
  DROP COLUMN source_upload_ids,
  DROP COLUMN returned_count,
  DROP COLUMN requested_count,
  DROP COLUMN stream,
  DROP COLUMN output_format,
  DROP COLUMN quality,
  DROP COLUMN size,
  DROP COLUMN provider_created,
  DROP COLUMN provider_response_payload,
  DROP COLUMN provider_request_payload,
  DROP COLUMN provider_endpoint;

INSERT INTO operation_logs (user_id, action, target_type, target_id, detail)
VALUES (
  NULL,
  'rollback_003_image_edits_storage_audit_billing',
  'migration',
  '003',
  JSON_OBJECT(
    'note', 'Removed edit-image storage, provider audit, usage, and billing metadata columns. Local files were not deleted.'
  )
);
```

## Audit Plan

Use `operation_logs` for:

- `generation_job_created`
- `provider_edit_request_sent`
- `provider_edit_response_received`
- `generated_image_remote_downloaded`
- `generated_image_saved`
- `generated_image_soft_deleted`
- `generated_image_physical_deleted`
- `generation_job_failed`
- `generation_job_partial_failed`
- `billing_recorded`

Audit log detail should include:

- `job_id`
- `image_id`
- `provider_endpoint`
- `requested_count`
- `returned_count`
- `remote_url`
- `local_path`
- `public_url`
- `file_size`
- `checksum_sha256`
- `usage`

## Billing Plan

Persist usage from provider response:

```json
{
  "total_tokens": 2541,
  "input_tokens": 1776,
  "output_tokens": 765,
  "input_text_tokens": 96,
  "input_image_tokens": 1680
}
```

Billing calculation can be separate from generation. Store billing state:

- `unbilled`
- `calculated`
- `charged`
- `refunded`
- `failed`

## Failure Handling

Provider request failed:

- mark job `failed`
- store safe error code/message
- write operation log

Provider returned fewer images than requested:

- save returned images
- set `requested_count=3`
- set `returned_count=1`
- mark job as `succeeded` if provider status is successful and product accepts composite output
- otherwise mark job `partial_failed`

Remote OSS download failed:

- retry with bounded retries
- if still failed, mark image save failure
- mark job `failed` or `partial_failed`

DB insert failed after local file save:

- delete just-saved local file if safe
- log cleanup result

Delete image:

- soft delete first by setting `deleted_at`
- write operation log
- physical delete only after explicit confirmation

## Verification Plan

Backend:

```powershell
cd D:\g-code\backend
uv run pytest
uv run ruff check app tests
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```powershell
cd D:\g-code\frontend
npm run build
npm run dev
```

Manual verification:

1. Upload three source images.
2. Submit GPT Image 2 edit job with `quality=high`, `n=3`, `outputFormat=png`.
3. Confirm backend sends repeated `image[]` fields.
4. Confirm provider request uses `/v1/images/edits`.
5. Confirm provider response `data[].url` is recorded.
6. Confirm OSS image is downloaded into `storage/gen_image/YYYYMMDD/`.
7. Confirm DB stores request payload, response payload, usage, remote URL, local path, public URL, file size, and checksum.
8. Confirm frontend gallery displays local public URL.
9. Confirm delete writes `deleted_at` and operation log.

## Implementation Order

1. Update backend request schema for edit-image parameters.
2. Ensure uploads API returns IDs that resolve to local files.
3. Update frontend multi-image upload state.
4. Update frontend generation request payload.
5. Implement provider multipart call to `/images/edits`.
6. Implement response handling for `url` primary and `b64_json` fallback.
7. Implement daily local generated-image storage.
8. Add migration and rollback SQL.
9. Persist provider request/response/usage metadata.
10. Persist generated image local metadata.
11. Update gallery listing and delete behavior.
12. Add tests and run verification.
