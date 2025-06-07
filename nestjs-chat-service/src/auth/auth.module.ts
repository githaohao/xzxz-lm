import { Module } from '@nestjs/common';
import { AuthGuard } from './auth.guard';
import { SecurityContextHolder } from './security-context';
import { FieldTransformer } from './field-transformer';
import { FieldTransformInterceptor } from './field-transform.interceptor';

/**
 * 认证模块
 * 配置网关认证相关功能和字段转换
 * 
 * ⚠️ 网关认证说明：
 * - 本服务依赖网关进行JWT验证，不在此服务中重复验证
 * - 用户信息通过网关在请求头中传递
 * - 使用SecurityContextHolder管理用户上下文信息
 * - 与若依微服务架构中的HeaderInterceptor配合使用
 * 
 * 🔄 字段转换说明：
 * - 支持多种字段名格式（驼峰、下划线等）
 * - 自动转换API请求和响应中的字段名
 * - FieldTransformer提供字段名转换工具方法
 * - FieldTransformInterceptor自动处理API数据转换
 */
@Module({
  providers: [
    AuthGuard, 
    SecurityContextHolder, 
    FieldTransformer, 
    FieldTransformInterceptor
  ],
  exports: [
    AuthGuard, 
    SecurityContextHolder, 
    FieldTransformer, 
    FieldTransformInterceptor
  ],
})
export class AuthModule {} 