# Database Guidelines

The project standard is MySQL for production persistence. Do not default to SQLite.

## Current Status

No backend app source, ORM models, or migration files exist yet. Database work must start by choosing and documenting the MySQL access layer.

## Recommended Choices

FastAPI-compatible options:

- SQLAlchemy 2.x async engine with `asyncmy` or `aiomysql`
- Alembic for migrations
- Pydantic schemas for API contracts, separate from ORM models

If another MySQL library is chosen, update this file with the concrete session, migration, and transaction patterns.

## Connection Rules

- Read database URL from environment, not source code.
- Use MySQL in development/test unless a test-only substitute is explicitly documented.
- Force MySQL client connections to `charset=utf8mb4`; do not rely on server or workstation defaults.
- Create database engines and pools during app startup/lifespan, not at import time.
- Use dependency providers for sessions.
- Close sessions and connections reliably.

## Migration Rules

Any database schema change must include:

- Complete forward SQL or Alembic migration.
- Complete rollback SQL or downgrade migration.
- Impact notes for existing data.
- Verification query.

Example SQL shape:

```sql
ALTER TABLE generation_jobs
  ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'pending';

-- rollback
ALTER TABLE generation_jobs
  DROP COLUMN status;
```

## Transaction Rules

Use transactions for workflows that create or update multiple related records, such as:

- generation job record plus generated image records
- user balance deduction plus job creation
- deletion/audit log pairs

Do not mix external AI calls inside long database transactions. Store a pending job, commit, run external work, then update status/results.

## Query Rules

- Avoid N+1 queries. Batch by IDs where possible.
- Select only needed columns for list endpoints.
- Use indexes for user id, job status, created time, and lookup keys.
- Paginate gallery and job-history endpoints.
- Never build SQL through string concatenation with user input.

## Destructive Operations

For delete/clear operations:

- Require user confirmation at the API or UI boundary.
- Write an operation log/audit row where applicable.
- Prefer soft delete for user-visible generated assets unless hard delete is explicitly required.
- Provide a rollback or restoration plan.

## Scenario: UTF-8 Database Boundary

### 1. Scope / Trigger
- Trigger: Any backend change that reads or writes multilingual text through MySQL, migrations, or JSON APIs.

### 2. Signatures
- Connection helper: `app.db.mysql.mysql_utf8mb4_url(database_url: str) -> str`
- SQL session bootstrap: `SET NAMES utf8mb4 COLLATE utf8mb4_0900_ai_ci;`
- Table defaults: `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci`

### 3. Contracts
- MySQL SQLAlchemy URLs must resolve to a URL containing `charset=utf8mb4`.
- Non-MySQL URLs are not production defaults and must not be introduced as a silent fallback.
- SQL migrations that create text-bearing tables must declare `utf8mb4` table defaults.

### 4. Validation & Error Matrix
- Missing MySQL charset in `DATABASE_URL` -> helper adds `charset=utf8mb4` before engine creation.
- Existing `charset=utf8mb4` -> helper preserves a single charset parameter.
- Migration without `utf8mb4` defaults -> reject during review before applying to MySQL.

### 5. Good/Base/Bad Cases
- Good: `mysql+aiomysql://user:pass@host/db` becomes `...?charset=utf8mb4` at engine creation.
- Base: `mysql+aiomysql://user:pass@host/db?charset=utf8mb4` remains unchanged.
- Bad: `mysql+aiomysql://user:pass@host/db?charset=gbk` is accepted into production.

### 6. Tests Required
- Unit test for adding `charset=utf8mb4` to a MySQL URL.
- Unit test for preserving an existing `charset=utf8mb4`.
- Source scan test confirming backend text sources decode with `encoding="utf-8"`.

### 7. Wrong vs Correct

#### Wrong
```python
create_async_engine(settings.database_url)
```

#### Correct
```python
create_async_engine(mysql_utf8mb4_url(settings.database_url))
```

## Scenario: Demo User Data Removal

### 1. Scope / Trigger
- Trigger: Production cleanup of `users.id = 'u-demo'` and all records owned by that user while preserving `users.id = 'admin'`.

### 2. Signatures
- Forward SQL: `app/db/migrations/002_remove_demo_user_data.sql`
- Rollback SQL: `app/db/migrations/002_remove_demo_user_data_rollback.sql`
- Affected tables: `users`, `generation_sessions`, `generation_messages`, `generation_jobs`, `generated_images`, `operation_logs`.

### 3. Contracts
- Cleanup SQL must check that `admin` exists before deleting demo data.
- Backup tables named `backup_002_demo_*` must be populated before deletion.
- Deletion order must respect foreign keys: images, messages, jobs, sessions, logs, then user.
- Cleanup must write an `operation_logs` audit row after deleting `u-demo`.

### 4. Validation & Error Matrix
- Confirmation variable mismatch -> SQL `SIGNAL` aborts.
- Missing `admin` user -> SQL `SIGNAL` aborts.
- Backup tables missing during rollback -> rollback fails visibly instead of pretending data was restored.

### 5. Good/Base/Bad Cases
- Good: preflight counts reviewed, `admin` count is 1, cleanup leaves zero `u-demo` owned rows.
- Base: no `u-demo` rows exist, script records cleanup and leaves `admin` untouched.
- Bad: `DELETE FROM users WHERE id <> 'admin'` deletes non-demo production users.

### 6. Tests Required
- Auth regression test that demo login no longer creates `u-demo`.
- Migration review must verify the final SELECT reports zero demo users, sessions, jobs, and images.

### 7. Wrong vs Correct

#### Wrong
```sql
DELETE FROM users WHERE id <> 'admin';
```

#### Correct
```sql
DELETE FROM generated_images WHERE user_id = 'u-demo';
DELETE FROM users WHERE id = 'u-demo';
```

## Scenario: Smart Templates Table

### 1. Scope / Trigger
- Trigger: Smart templates are database-backed configuration used by the Vue workbench.

### 2. Signatures
- Table: `smart_templates`
- Key fields: `id`, `name`, `image_url`, `prompt`, `model`, `aspect_ratio`, `resolution`, `quantity`, `type`, `sort_order`, `is_enabled`.
- API filter: `GET /api/v1/templates?type=1|2`.

### 3. Contracts
- `type=1` means product main image templates.
- `type=2` means product detail image templates.
- Queries must filter `is_enabled = 1` and sort by `sort_order ASC, created_at DESC`.
- Frontend response fields use camelCase (`imageUrl`, `aspectRatio`) even though DB columns are snake_case.

### 4. Validation & Error Matrix
- `type` outside `1|2` -> FastAPI returns `422`.
- Empty table -> return an empty `templates` list, not mock rows.
- Disabled row (`is_enabled=0`) -> excluded from API results.

### 5. Good/Base/Bad Cases
- Good: `type=2` returns only detail image templates.
- Base: no `type` filter can return all enabled templates for admin-style consumers.
- Bad: frontend hard-codes template data and drifts from database-managed prompts.

### 6. Tests Required
- Route test for successful filtered list.
- Route test for invalid `type`.
- Migration includes forward table/seed SQL and rollback `DROP TABLE`.

### 7. Wrong vs Correct

#### Wrong
```sql
SELECT * FROM smart_templates;
```

#### Correct
```sql
SELECT id, name, image_url, prompt, model, aspect_ratio, resolution, quantity, type
FROM smart_templates
WHERE is_enabled = 1 AND type = :type
ORDER BY sort_order ASC, created_at DESC;
```
