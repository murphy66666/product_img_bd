-- Remove demo user data while preserving users.id = 'admin'.
-- MySQL 8+.
--
-- Safety guard: review the preflight SELECT results first. To execute deletion,
-- keep the SET value exactly as CONFIRM_REMOVE_DEMO_USER.
-- Rollback data is stored in backup tables named backup_002_demo_*.

SET @demo_user_id := 'u-demo';
SET @admin_user_id := 'admin';
SET @confirm := 'CONFIRM_REMOVE_DEMO_USER';

SELECT
  (SELECT COUNT(*) FROM users WHERE id = @admin_user_id) AS admin_users_to_keep,
  (SELECT COUNT(*) FROM users WHERE id = @demo_user_id) AS demo_users_to_delete,
  (SELECT COUNT(*) FROM generation_sessions WHERE user_id = @demo_user_id) AS demo_sessions,
  (SELECT COUNT(*) FROM generation_messages WHERE session_id IN (
    SELECT id FROM generation_sessions WHERE user_id = @demo_user_id
  )) AS demo_messages,
  (SELECT COUNT(*) FROM generation_jobs WHERE user_id = @demo_user_id) AS demo_jobs,
  (SELECT COUNT(*) FROM generated_images WHERE user_id = @demo_user_id) AS demo_images,
  (SELECT COUNT(*) FROM operation_logs WHERE user_id = @demo_user_id) AS demo_operation_logs;

DELIMITER //
CREATE PROCEDURE remove_demo_user_data_002()
BEGIN
  IF @confirm <> 'CONFIRM_REMOVE_DEMO_USER' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Deletion not confirmed';
  END IF;

  IF (SELECT COUNT(*) FROM users WHERE id = @admin_user_id) = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Admin user is missing; aborting cleanup';
  END IF;

  START TRANSACTION;

  CREATE TABLE IF NOT EXISTS backup_002_demo_users AS SELECT * FROM users WHERE 1 = 0;
  CREATE TABLE IF NOT EXISTS backup_002_demo_generation_sessions AS SELECT * FROM generation_sessions WHERE 1 = 0;
  CREATE TABLE IF NOT EXISTS backup_002_demo_generation_messages AS SELECT * FROM generation_messages WHERE 1 = 0;
  CREATE TABLE IF NOT EXISTS backup_002_demo_generation_jobs AS SELECT * FROM generation_jobs WHERE 1 = 0;
  CREATE TABLE IF NOT EXISTS backup_002_demo_generated_images AS SELECT * FROM generated_images WHERE 1 = 0;
  CREATE TABLE IF NOT EXISTS backup_002_demo_operation_logs AS SELECT * FROM operation_logs WHERE 1 = 0;

  INSERT INTO backup_002_demo_users SELECT * FROM users WHERE id = @demo_user_id;
  INSERT INTO backup_002_demo_generation_sessions SELECT * FROM generation_sessions WHERE user_id = @demo_user_id;
  INSERT INTO backup_002_demo_generation_messages
    SELECT * FROM generation_messages
    WHERE session_id IN (SELECT id FROM generation_sessions WHERE user_id = @demo_user_id);
  INSERT INTO backup_002_demo_generation_jobs SELECT * FROM generation_jobs WHERE user_id = @demo_user_id;
  INSERT INTO backup_002_demo_generated_images SELECT * FROM generated_images WHERE user_id = @demo_user_id;
  INSERT INTO backup_002_demo_operation_logs SELECT * FROM operation_logs WHERE user_id = @demo_user_id;

  DELETE FROM generated_images WHERE user_id = @demo_user_id;
  DELETE FROM generation_messages
    WHERE session_id IN (SELECT id FROM generation_sessions WHERE user_id = @demo_user_id);
  DELETE FROM generation_jobs WHERE user_id = @demo_user_id;
  DELETE FROM generation_sessions WHERE user_id = @demo_user_id;
  DELETE FROM operation_logs WHERE user_id = @demo_user_id;
  DELETE FROM users WHERE id = @demo_user_id;

  INSERT INTO operation_logs (user_id, action, target_type, target_id, detail)
  VALUES (
    NULL,
    'remove_demo_user_data',
    'user',
    @demo_user_id,
    JSON_OBJECT(
      'preserved_user_id', @admin_user_id,
      'backup_tables', JSON_ARRAY(
        'backup_002_demo_users',
        'backup_002_demo_generation_sessions',
        'backup_002_demo_generation_messages',
        'backup_002_demo_generation_jobs',
        'backup_002_demo_generated_images',
        'backup_002_demo_operation_logs'
      )
    )
  );

  COMMIT;
END//
DELIMITER ;

CALL remove_demo_user_data_002();
DROP PROCEDURE remove_demo_user_data_002;

SELECT
  (SELECT COUNT(*) FROM users WHERE id = @admin_user_id) AS admin_users_remaining,
  (SELECT COUNT(*) FROM users WHERE id = @demo_user_id) AS demo_users_remaining,
  (SELECT COUNT(*) FROM generation_sessions WHERE user_id = @demo_user_id) AS demo_sessions_remaining,
  (SELECT COUNT(*) FROM generation_jobs WHERE user_id = @demo_user_id) AS demo_jobs_remaining,
  (SELECT COUNT(*) FROM generated_images WHERE user_id = @demo_user_id) AS demo_images_remaining;
