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
