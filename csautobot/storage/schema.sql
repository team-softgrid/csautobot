-- MariaDB DDL Schema for csautobot

-- Disable foreign key checks temporarily to drop tables in any order
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `audit_log`;
DROP TABLE IF EXISTS `usage_meter`;
DROP TABLE IF EXISTS `inspection_log`;
DROP TABLE IF EXISTS `part_usage`;
DROP TABLE IF EXISTS `action`;
DROP TABLE IF EXISTS `incident`;
DROP TABLE IF EXISTS `charger`;
DROP TABLE IF EXISTS `site`;
DROP TABLE IF EXISTS `app_user`;
DROP TABLE IF EXISTS `tenant`;

SET FOREIGN_KEY_CHECKS = 1;

-- 1. Tenant Table
CREATE TABLE `tenant` (
    `tenant_id` VARCHAR(50) NOT NULL,
    `tenant_name` VARCHAR(100) NOT NULL,
    `plan_code` VARCHAR(50) NOT NULL DEFAULT 'FREE',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. App User Table
CREATE TABLE `app_user` (
    `user_id` VARCHAR(50) NOT NULL,
    `tenant_id` VARCHAR(50) NOT NULL,
    `email` VARCHAR(100) NOT NULL,
    `role` VARCHAR(30) NOT NULL DEFAULT 'USER',
    `status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`user_id`),
    CONSTRAINT `fk_user_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`tenant_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Site Table
CREATE TABLE `site` (
    `site_id` VARCHAR(50) NOT NULL,
    `tenant_id` VARCHAR(50) NOT NULL,
    `site_name` VARCHAR(100) NOT NULL,
    `operator_name` VARCHAR(100) DEFAULT NULL,
    `address` VARCHAR(255) DEFAULT NULL,
    `region` VARCHAR(50) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`site_id`),
    CONSTRAINT `fk_site_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`tenant_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Charger Table
CREATE TABLE `charger` (
    `charger_id` VARCHAR(50) NOT NULL,
    `tenant_id` VARCHAR(50) NOT NULL,
    `site_id` VARCHAR(50) NOT NULL,
    `manufacturer` VARCHAR(100) DEFAULT NULL,
    `model_name` VARCHAR(100) DEFAULT NULL,
    `serial_no` VARCHAR(100) DEFAULT NULL,
    `install_date` DATE DEFAULT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'NORMAL',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`charger_id`),
    CONSTRAINT `fk_charger_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`tenant_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_charger_site` FOREIGN KEY (`site_id`) REFERENCES `site` (`site_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Incident Table
CREATE TABLE `incident` (
    `incident_id` VARCHAR(50) NOT NULL,
    `tenant_id` VARCHAR(50) NOT NULL,
    `site_id` VARCHAR(50) DEFAULT NULL,
    `charger_id` VARCHAR(50) DEFAULT NULL,
    `occurred_at` DATETIME DEFAULT NULL,
    `reported_at` DATETIME DEFAULT NULL,
    `symptom_raw` TEXT NOT NULL,
    `symptom_norm` TEXT DEFAULT NULL,
    `error_code_raw` VARCHAR(50) DEFAULT NULL,
    `error_code_norm` VARCHAR(50) DEFAULT NULL,
    `severity` VARCHAR(20) DEFAULT NULL,
    `source_file` VARCHAR(255) DEFAULT NULL,
    `source_sheet` VARCHAR(100) DEFAULT NULL,
    `source_row` INT DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`incident_id`),
    CONSTRAINT `fk_incident_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`tenant_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_incident_site` FOREIGN KEY (`site_id`) REFERENCES `site` (`site_id`) ON DELETE SET NULL,
    CONSTRAINT `fk_incident_charger` FOREIGN KEY (`charger_id`) REFERENCES `charger` (`charger_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Action Table (Action taken to resolve incident)
CREATE TABLE `action` (
    `action_id` VARCHAR(50) NOT NULL,
    `incident_id` VARCHAR(50) NOT NULL,
    `action_at` DATETIME DEFAULT NULL,
    `action_type` VARCHAR(50) NOT NULL,
    `action_detail` TEXT NOT NULL,
    `result` VARCHAR(50) DEFAULT NULL,
    `downtime_min` INT DEFAULT 0,
    `engineer_name` VARCHAR(100) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`action_id`),
    CONSTRAINT `fk_action_incident` FOREIGN KEY (`incident_id`) REFERENCES `incident` (`incident_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Part Usage Table
CREATE TABLE `part_usage` (
    `part_usage_id` VARCHAR(50) NOT NULL,
    `action_id` VARCHAR(50) NOT NULL,
    `part_code` VARCHAR(50) DEFAULT NULL,
    `part_name` VARCHAR(100) DEFAULT NULL,
    `qty` INT DEFAULT 1,
    `unit_cost` DECIMAL(15, 2) DEFAULT 0.00,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`part_usage_id`),
    CONSTRAINT `fk_part_action` FOREIGN KEY (`action_id`) REFERENCES `action` (`action_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Inspection Log Table
CREATE TABLE `inspection_log` (
    `inspection_id` VARCHAR(50) NOT NULL,
    `tenant_id` VARCHAR(50) NOT NULL,
    `site_id` VARCHAR(50) NOT NULL,
    `charger_id` VARCHAR(50) DEFAULT NULL,
    `inspection_cycle` VARCHAR(20) NOT NULL, -- 'DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY'
    `inspection_type` VARCHAR(30) NOT NULL,  -- 'REGULAR', 'EMERGENCY', 'INSTALLATION'
    `checklist_json` JSON NOT NULL,          -- JSON of checklist answers
    `memo_text` TEXT DEFAULT NULL,
    `photo_urls_json` JSON DEFAULT NULL,     -- JSON array of photo URLs
    `ai_summary` TEXT DEFAULT NULL,          -- AI generated summary/recommendations
    `status` VARCHAR(20) NOT NULL DEFAULT 'DRAFT', -- 'DRAFT', 'CONFIRMED'
    `confirmed_by` VARCHAR(50) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`inspection_id`),
    CONSTRAINT `fk_inspection_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`tenant_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_inspection_site` FOREIGN KEY (`site_id`) REFERENCES `site` (`site_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_inspection_charger` FOREIGN KEY (`charger_id`) REFERENCES `charger` (`charger_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Usage Meter Table (For billing/observability)
CREATE TABLE `usage_meter` (
    `usage_id` INT AUTO_INCREMENT NOT NULL,
    `tenant_id` VARCHAR(50) NOT NULL,
    `user_id` VARCHAR(50) DEFAULT NULL,
    `feature_code` VARCHAR(50) NOT NULL, -- 'RAG_SEARCH', 'AI_SUMMARY', 'INSPECT_DRAFT'
    `model_name` VARCHAR(50) DEFAULT NULL,
    `input_tokens` INT DEFAULT 0,
    `output_tokens` INT DEFAULT 0,
    `request_count` INT NOT NULL DEFAULT 1,
    `measured_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`usage_id`),
    CONSTRAINT `fk_usage_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`tenant_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Audit Log Table
CREATE TABLE `audit_log` (
    `audit_id` INT AUTO_INCREMENT NOT NULL,
    `tenant_id` VARCHAR(50) NOT NULL,
    `user_id` VARCHAR(50) DEFAULT NULL,
    `action_code` VARCHAR(50) NOT NULL, -- 'LOGIN', 'SEARCH', 'CONFIRM_INSPECTION'
    `resource_type` VARCHAR(50) NOT NULL, -- 'INSPECTION_LOG', 'CHARGER', 'USER'
    `resource_id` VARCHAR(50) NOT NULL,
    `payload_json` JSON DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`audit_id`),
    CONSTRAINT `fk_audit_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`tenant_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Indexing for performance optimization
CREATE INDEX `idx_incident_search` ON `incident` (`tenant_id`, `site_id`, `error_code_norm`);
CREATE INDEX `idx_inspection_site` ON `inspection_log` (`tenant_id`, `site_id`, `status`);
CREATE INDEX `idx_usage_tenant_date` ON `usage_meter` (`tenant_id`, `measured_at`);
