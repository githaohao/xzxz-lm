import { TypeOrmModuleOptions } from '@nestjs/typeorm';
import { ConfigService } from '@nestjs/config';
import { ChatSession } from '../chat/entities/chat-session.entity';
import { ChatMessage } from '../chat/entities/chat-message.entity';

/**
 * 数据库配置工厂函数
 */
export const createDatabaseConfig = (configService: ConfigService): TypeOrmModuleOptions => ({
  type: 'mysql',
  host: configService.get<string>('DB_HOST', 'localhost'),
  port: configService.get<number>('DB_PORT', 3306),
  username: configService.get<string>('DB_USERNAME', 'chat_user'),
  password: configService.get<string>('DB_PASSWORD', 'chat_password'),
  database: configService.get<string>('DB_DATABASE', 'xzxz_chat_history'),
  entities: [ChatSession, ChatMessage],
  synchronize: configService.get<boolean>('DB_SYNCHRONIZE', true), // 生产环境应设为false
  logging: configService.get<boolean>('DB_LOGGING', false),
  timezone: '+08:00', // 设置为中国时区
  charset: 'utf8mb4',
  extra: {
    connectionLimit: 10,
    acquireTimeout: 60000,
    timeout: 60000,
  },
}); 