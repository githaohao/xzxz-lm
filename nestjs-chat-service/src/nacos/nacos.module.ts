import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { NacosService } from './nacos.service';

/**
 * Nacos模块
 * 服务注册与发现功能
 */
@Module({
  imports: [ConfigModule],
  providers: [NacosService],
  exports: [NacosService],
})
export class NacosModule {} 