-- MySQL 8+ initial schema for product image generation backend.

CREATE TABLE users (
  id VARCHAR(64) PRIMARY KEY,
  phone VARCHAR(32) NOT NULL UNIQUE,
  name VARCHAR(120) NOT NULL,
  avatar VARCHAR(512) NULL,
  balance INT NOT NULL DEFAULT 0,
  role VARCHAR(120) NOT NULL DEFAULT 'user',
  password_hash VARCHAR(255) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE generation_sessions (
  id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  title VARCHAR(160) NOT NULL,
  category VARCHAR(32) NOT NULL,
  config JSON NOT NULL,
  deleted_at TIMESTAMP NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_generation_sessions_user_category_created (user_id, category, created_at),
  CONSTRAINT fk_generation_sessions_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE generation_messages (
  id VARCHAR(64) PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  sender VARCHAR(32) NOT NULL,
  message_type VARCHAR(32) NOT NULL,
  text TEXT NOT NULL,
  payload JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_generation_messages_session_created (session_id, created_at),
  CONSTRAINT fk_generation_messages_session FOREIGN KEY (session_id) REFERENCES generation_sessions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE generation_jobs (
  id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  session_id VARCHAR(64) NULL,
  provider VARCHAR(64) NOT NULL,
  model VARCHAR(128) NOT NULL,
  provider_job_id VARCHAR(128) NULL,
  category VARCHAR(32) NOT NULL,
  status VARCHAR(32) NOT NULL,
  aspect_ratio VARCHAR(32) NOT NULL,
  resolution VARCHAR(32) NOT NULL,
  quantity INT NOT NULL,
  prompt TEXT NOT NULL,
  source_image_url TEXT NULL,
  request_payload JSON NOT NULL,
  error_code VARCHAR(64) NULL,
  error_message TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_generation_jobs_user_status_created (user_id, status, created_at),
  INDEX idx_generation_jobs_session_created (session_id, created_at),
  CONSTRAINT fk_generation_jobs_user FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT fk_generation_jobs_session FOREIGN KEY (session_id) REFERENCES generation_sessions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE generated_images (
  id VARCHAR(64) PRIMARY KEY,
  job_id VARCHAR(64) NOT NULL,
  user_id VARCHAR(64) NOT NULL,
  session_id VARCHAR(64) NULL,
  url TEXT NOT NULL,
  original_url TEXT NULL,
  prompt TEXT NOT NULL,
  provider VARCHAR(64) NOT NULL,
  model VARCHAR(128) NOT NULL,
  resolution VARCHAR(32) NOT NULL,
  aspect_ratio VARCHAR(32) NOT NULL,
  category VARCHAR(32) NOT NULL,
  tags JSON NULL,
  deleted_at TIMESTAMP NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_generated_images_user_category_created (user_id, category, created_at),
  CONSTRAINT fk_generated_images_job FOREIGN KEY (job_id) REFERENCES generation_jobs(id),
  CONSTRAINT fk_generated_images_user FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT fk_generated_images_session FOREIGN KEY (session_id) REFERENCES generation_sessions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE smart_templates (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  image_url VARCHAR(1024) NOT NULL,
  prompt TEXT NOT NULL,
  model VARCHAR(128) NOT NULL,
  aspect_ratio VARCHAR(32) NOT NULL,
  resolution VARCHAR(32) NOT NULL,
  quantity INT NOT NULL,
  type TINYINT NOT NULL COMMENT '1=product main image, 2=product detail image',
  sort_order INT NOT NULL DEFAULT 0,
  is_enabled TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_smart_templates_type_enabled_sort (type, is_enabled, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO smart_templates (
  id, name, image_url, prompt, model, aspect_ratio, resolution, quantity, type, sort_order
) VALUES
  (
    'tpl-main-skincare',
    'Beauty skincare',
    'https://images.unsplash.com/photo-1526947425960-945c6e72858f?auto=format&fit=crop&w=150&q=80',
    'Premium skincare serum bottle standing in water ripples, soft morning light, commercial product photography',
    'gemini-banana',
    '1:1',
    '2k',
    3,
    1,
    10
  ),
  (
    'tpl-main-digital',
    'Smart digital',
    'https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=150&q=80',
    'Silver over-ear headphones floating in a clean studio scene with subtle soundwave arcs and crisp reflections',
    'gpt-images-2',
    '16:9',
    '2k',
    2,
    1,
    20
  ),
  (
    'tpl-detail-sneaker',
    'Sport sneaker',
    'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=150&q=80',
    'Futuristic sport sneaker floating above a neon grid, cyber city lighting, premium ecommerce detail image',
    'jimeng',
    '9:16',
    '2k',
    4,
    2,
    10
  );

CREATE TABLE operation_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id VARCHAR(64) NULL,
  action VARCHAR(128) NOT NULL,
  target_type VARCHAR(64) NOT NULL,
  target_id VARCHAR(128) NULL,
  detail JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_operation_logs_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
