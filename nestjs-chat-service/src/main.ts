import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AppModule } from './app.module';
import 'reflect-metadata';

/**
 * 应用启动函数
 */
async function bootstrap() {
  const logger = new Logger('Bootstrap');
  
  try {
    // 创建NestJS应用实例
    const app = await NestFactory.create(AppModule, {
      logger: ['log', 'error', 'warn', 'debug', 'verbose'],
    });

    // 获取配置服务
    const configService = app.get(ConfigService);

    // 启用全局验证管道
    app.useGlobalPipes(new ValidationPipe({
      transform: true,
      whitelist: true,
      forbidNonWhitelisted: true,
      transformOptions: {
        enableImplicitConversion: true,
      },
    }));

    // 启用CORS
    app.enableCors({
      origin: [
        'http://localhost:3000',
        'http://localhost:3001',
        'http://localhost:3002',
        'http://localhost:3004',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:3001',
        'http://127.0.0.1:3002',
        'http://127.0.0.1:3004',
      ],
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization'],
      credentials: true,
    });

    // 设置全局路径前缀（可选）
    // app.setGlobalPrefix('api');

    // 获取端口配置
    const port = configService.get<number>('PORT', 8001);
    const host = configService.get<string>('HOST', '0.0.0.0');

    // 启动应用
    await app.listen(port, host);

    logger.log(`🚀 小智小智聊天历史服务启动成功!`);
    logger.log(`📡 服务地址: http://${host}:${port}`);
    logger.log(`🏥 健康检查: http://${host}:${port}/chat/health`);
    logger.log(`📚 API文档: http://${host}:${port}/chat`);
    
    // 输出环境信息
    const environment = configService.get<string>('NODE_ENV', 'development');
    const nacosEnabled = configService.get<boolean>('NACOS_ENABLED', true);
    const dbHost = configService.get<string>('DB_HOST', 'localhost');
    const dbPort = configService.get<number>('DB_PORT', 3307);
    
    logger.log(`🌍 运行环境: ${environment}`);
    logger.log(`🔗 Nacos注册: ${nacosEnabled ? '已启用' : '已禁用'}`);
    logger.log(`💾 数据库: ${dbHost}:${dbPort}`);

  } catch (error) {
    logger.error('应用启动失败:', error);
    process.exit(1);
  }
}

// 启动应用
bootstrap(); 