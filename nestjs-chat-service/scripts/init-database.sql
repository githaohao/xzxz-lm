-- 小智小智聊天历史数据库初始化脚本

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS `xzxz_chat_history` 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE `xzxz_chat_history`;

-- 创建聊天会话表
CREATE TABLE IF NOT EXISTS `chat_session` (
  `id` varchar(36) NOT NULL,
  `title` varchar(255) NOT NULL DEFAULT '新对话',
  `user_id` varchar(100) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_is_deleted` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天会话表';

-- 创建聊天消息表
CREATE TABLE IF NOT EXISTS `chat_message` (
  `id` varchar(36) NOT NULL,
  `session_id` varchar(36) NOT NULL,
  `role` enum('user','assistant','system') NOT NULL,
  `content` text NOT NULL,
  `metadata` json DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_role` (`role`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_is_deleted` (`is_deleted`),
  CONSTRAINT `fk_chat_message_session` FOREIGN KEY (`session_id`) REFERENCES `chat_session` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天消息表';

-- 插入示例数据
INSERT IGNORE INTO `chat_session` (`id`, `title`, `user_id`) VALUES 
('demo-session-001', '示例对话', 'demo-user'),
('demo-session-002', '技术讨论', 'demo-user');

INSERT IGNORE INTO `chat_message` (`id`, `session_id`, `role`, `content`) VALUES 
('demo-msg-001', 'demo-session-001', 'user', '你好，小智小智！'),
('demo-msg-002', 'demo-session-001', 'assistant', '你好！我是小智小智，很高兴为您服务！有什么可以帮助您的吗？'),
('demo-msg-003', 'demo-session-002', 'user', '请介绍一下这个项目的技术栈'),
('demo-msg-004', 'demo-session-002', 'assistant', '这个项目采用了现代化的技术栈：前端使用Vue 3 + TypeScript + Vite，后端使用FastAPI + NestJS微服务架构，数据库使用MySQL，还集成了Nacos服务注册中心。');

-- 显示表结构
SHOW TABLES;
DESCRIBE chat_session;
DESCRIBE chat_message; 