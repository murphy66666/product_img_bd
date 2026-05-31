-- Rollback for 001_initial_schema.sql. Drop child tables before parents.

DROP TABLE IF EXISTS operation_logs;
DROP TABLE IF EXISTS smart_templates;
DROP TABLE IF EXISTS generated_images;
DROP TABLE IF EXISTS generation_jobs;
DROP TABLE IF EXISTS generation_messages;
DROP TABLE IF EXISTS generation_sessions;
DROP TABLE IF EXISTS users;
