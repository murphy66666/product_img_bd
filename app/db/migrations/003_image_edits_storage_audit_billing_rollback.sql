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
