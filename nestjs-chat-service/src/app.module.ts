import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { APP_INTERCEPTOR } from '@nestjs/core';
import { ChatModule } from './chat/chat.module';
import { AuthModule } from './auth/auth.module';
import { NacosModule } from './nacos/nacos.module';
import { createDatabaseConfig } from './config/database.config';
import { FieldTransformInterceptor } from './auth/field-transform.interceptor';

/**
 * 应用主模块
 * 小智小智聊天历史服务的根模块
 */
@Module({
  imports: [
    // 配置模块 - 加载环境变量
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: ['.env.local', '.env'],
    }),
    
    // 数据库模块 - TypeORM配置
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: createDatabaseConfig,
      inject: [ConfigService],
    }),
    
    // 业务模块
    ChatModule,
    AuthModule,
    NacosModule,
  ],
  controllers: [],
  providers: [
    // 全局字段转换拦截器
    {
      provide: APP_INTERCEPTOR,
      useClass: FieldTransformInterceptor,
    },
  ],
})
export class AppModule {} 