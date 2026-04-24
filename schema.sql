-- MariaDB schema aligned with the current Zalo desktop tool structure.
-- This script replaces the older mixed schema contract with the current model:
--   profiles
--   zalo_accounts
--   account_click_targets
--   messages

CREATE DATABASE IF NOT EXISTS zalo_tool
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE zalo_tool;


-- 1. Reusable Chrome profiles
CREATE TABLE IF NOT EXISTS profiles (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    chrome_executable VARCHAR(512) NOT NULL,
    profile_path VARCHAR(512) NOT NULL,
    target_url VARCHAR(512) NOT NULL DEFAULT 'https://chat.zalo.me',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_profiles_name (name),
    UNIQUE KEY uq_profiles_profile_path (profile_path)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- 2. Launchable Zalo accounts linked to one profile
CREATE TABLE IF NOT EXISTS zalo_accounts (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    profile_id VARCHAR(64) NOT NULL,
    proxy VARCHAR(512) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_zalo_accounts_profile_id (profile_id),
    CONSTRAINT fk_zalo_accounts_profile
        FOREIGN KEY (profile_id) REFERENCES profiles(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- 3. Class Manage targets owned by one account
CREATE TABLE IF NOT EXISTS account_click_targets (
    id VARCHAR(64) PRIMARY KEY,
    account_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    selector_kind VARCHAR(50) NOT NULL,
    selector_value TEXT NOT NULL,
    upload_file_path VARCHAR(1024) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_account_click_targets_name (account_id, name),
    CONSTRAINT fk_account_click_targets_account
        FOREIGN KEY (account_id) REFERENCES zalo_accounts(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- 4. Minimal message persistence
CREATE TABLE IF NOT EXISTS messages (
    msgId VARCHAR(100) PRIMARY KEY,
    fromGroupId VARCHAR(100) DEFAULT NULL,
    toGroupId VARCHAR(100) DEFAULT NULL,
    fromAccountId VARCHAR(64) DEFAULT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_messages_from_account_id (fromAccountId),
    KEY idx_messages_from_group_id (fromGroupId),
    KEY idx_messages_to_group_id (toGroupId),
    CONSTRAINT fk_messages_from_account
        FOREIGN KEY (fromAccountId) REFERENCES zalo_accounts(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
