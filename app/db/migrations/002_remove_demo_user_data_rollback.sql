-- Restore demo user data backed up by 002_remove_demo_user_data.sql.
-- Run only if the backup_002_demo_* tables still exist.

SET @demo_user_id := 'u-demo';
SET @confirm := 'CONFIRM_RESTORE_DEMO_USER';

DELIMITER //
CREATE PROCEDURE restore_demo_user_data_002()
BEGIN
  IF @confirm <> 'CONFIRM_RESTORE_DEMO_USER' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Restore not confirmed';
  END IF;

  START TRANSACTION;

  INSERT IGNORE INTO users SELECT * FROM backup_002_demo_users;
  INSERT IGNORE INTO generation_sessions SELECT * FROM backup_002_demo_generation_sessions;
  INSERT IGNORE INTO generation_messages SELECT * FROM backup_002_demo_generation_messages;
  INSERT IGNORE INTO generation_jobs SELECT * FROM backup_002_demo_generation_jobs;
  INSERT IGNORE INTO generated_images SELECT * FROM backup_002_demo_generated_images;
  INSERT IGNORE INTO operation_logs SELECT * FROM backup_002_demo_operation_logs;

  INSERT INTO operation_logs (user_id, action, target_type, target_id, detail)
  VALUES (
    @demo_user_id,
    'restore_demo_user_data',
    'user',
    @demo_user_id,
    JSON_OBJECT('source_migration', '002_remove_demo_user_data')
  );

  COMMIT;
END//
DELIMITER ;

CALL restore_demo_user_data_002();
DROP PROCEDURE restore_demo_user_data_002;

SELECT
  (SELECT COUNT(*) FROM users WHERE id = @demo_user_id) AS demo_users_restored,
  (SELECT COUNT(*) FROM generation_sessions WHERE user_id = @demo_user_id) AS demo_sessions_restored,
  (SELECT COUNT(*) FROM generation_jobs WHERE user_id = @demo_user_id) AS demo_jobs_restored,
  (SELECT COUNT(*) FROM generated_images WHERE user_id = @demo_user_id) AS demo_images_restored;
