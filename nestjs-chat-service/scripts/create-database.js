#!/usr/bin/env node

const mysql = require('mysql2/promise');
require('dotenv').config();

async function createDatabase() {
  const config = {
    host: process.env.DB_HOST || '192.168.10.188',
    port: parseInt(process.env.DB_PORT) || 3306,
    user: process.env.DB_USERNAME || 'xwh-xzxz-ai',
    password: process.env.DB_PASSWORD || 'Ny76MSNwCyNFMeLT',
    charset: 'utf8mb4'
  };

  const targetDb = process.env.DB_DATABASE || 'xzxz_chat_history';

  console.log('🔧 创建数据库和表结构...');
  console.log(`目标数据库: ${targetDb}`);

  let connection;
  
  try {
    connection = await mysql.createConnection(config);
    console.log('✅ 连接MySQL服务器成功！');

    // 创建数据库
    console.log(`\n📦 创建数据库 '${targetDb}'...`);
    await connection.execute(`CREATE DATABASE IF NOT EXISTS \`${targetDb}\` 
      DEFAULT CHARACTER SET utf8mb4 
      DEFAULT COLLATE utf8mb4_unicode_ci`);
    console.log('✅ 数据库创建成功！');

    // 切换到新数据库
    await connection.execute(`USE \`${targetDb}\``);
    console.log(`✅ 切换到数据库 '${targetDb}'`);

    // 创建聊天会话表
    console.log('\n📋 创建聊天会话表...');
    await connection.execute(`
      CREATE TABLE IF NOT EXISTS \`chat_session\` (
        \`id\` varchar(36) NOT NULL,
        \`title\` varchar(255) NOT NULL DEFAULT '新对话',
        \`user_id\` varchar(100) DEFAULT NULL,
        \`created_at\` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        \`updated_at\` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        \`is_deleted\` tinyint(1) NOT NULL DEFAULT '0',
        PRIMARY KEY (\`id\`),
        KEY \`idx_user_id\` (\`user_id\`),
        KEY \`idx_created_at\` (\`created_at\`),
        KEY \`idx_is_deleted\` (\`is_deleted\`)
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天会话表'
    `);
    console.log('✅ 聊天会话表创建成功！');

    // 创建聊天消息表
    console.log('\n💬 创建聊天消息表...');
    await connection.execute(`
      CREATE TABLE IF NOT EXISTS \`chat_message\` (
        \`id\` varchar(36) NOT NULL,
        \`session_id\` varchar(36) NOT NULL,
        \`role\` enum('user','assistant','system') NOT NULL,
        \`content\` text NOT NULL,
        \`metadata\` json DEFAULT NULL,
        \`created_at\` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        \`updated_at\` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        \`is_deleted\` tinyint(1) NOT NULL DEFAULT '0',
        PRIMARY KEY (\`id\`),
        KEY \`idx_session_id\` (\`session_id\`),
        KEY \`idx_role\` (\`role\`),
        KEY \`idx_created_at\` (\`created_at\`),
        KEY \`idx_is_deleted\` (\`is_deleted\`),
        CONSTRAINT \`fk_chat_message_session\` FOREIGN KEY (\`session_id\`) REFERENCES \`chat_session\` (\`id\`) ON DELETE CASCADE
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天消息表'
    `);
    console.log('✅ 聊天消息表创建成功！');

    // 插入示例数据
    console.log('\n🎯 插入示例数据...');
    await connection.execute(`
      INSERT IGNORE INTO \`chat_session\` (\`id\`, \`title\`, \`user_id\`) VALUES 
      ('demo-session-001', '示例对话', 'demo-user'),
      ('demo-session-002', '技术讨论', 'demo-user')
    `);

    await connection.execute(`
      INSERT IGNORE INTO \`chat_message\` (\`id\`, \`session_id\`, \`role\`, \`content\`) VALUES 
      ('demo-msg-001', 'demo-session-001', 'user', '你好，小智小智！'),
      ('demo-msg-002', 'demo-session-001', 'assistant', '你好！我是小智小智，很高兴为您服务！有什么可以帮助您的吗？'),
      ('demo-msg-003', 'demo-session-002', 'user', '请介绍一下这个项目的技术栈'),
      ('demo-msg-004', 'demo-session-002', 'assistant', '这个项目采用了现代化的技术栈：前端使用Vue 3 + TypeScript + Vite，后端使用FastAPI + NestJS微服务架构，数据库使用MySQL，还集成了Nacos服务注册中心。')
    `);
    console.log('✅ 示例数据插入成功！');

    // 验证创建结果
    console.log('\n📊 验证创建结果...');
    const [tables] = await connection.execute('SHOW TABLES');
    console.log(`表数量: ${tables.length}`);
    tables.forEach(table => {
      console.log(`  - ${Object.values(table)[0]}`);
    });

    const [sessionCount] = await connection.execute('SELECT COUNT(*) as count FROM chat_session');
    const [messageCount] = await connection.execute('SELECT COUNT(*) as count FROM chat_message');
    console.log(`会话数量: ${sessionCount[0].count}`);
    console.log(`消息数量: ${messageCount[0].count}`);

    console.log('\n🎉 数据库初始化完成！');

  } catch (error) {
    console.error(`❌ 操作失败: ${error.message}`);
    console.error(`错误代码: ${error.code}`);
    process.exit(1);
  } finally {
    if (connection) {
      await connection.end();
      console.log('\n🔌 连接已关闭');
    }
  }
}

createDatabase(); 