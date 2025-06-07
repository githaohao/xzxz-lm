import {
  Injectable,
  CanActivate,
  ExecutionContext,
  UnauthorizedException,
  SetMetadata,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { Request } from 'express';
import { SecurityContextHolder, SecurityConstants, UserContext } from './security-context';
import { FieldTransformer } from './field-transformer';

/**
 * 公开端点装饰器 - 标记不需要认证的端点
 */
export const IS_PUBLIC_KEY = 'isPublic';
export const Public = () => SetMetadata(IS_PUBLIC_KEY, true);

/**
 * 网关认证守卫
 * 从网关传递的请求头中获取用户信息，与若依系统网关集成
 * 支持@Public装饰器跳过认证
 * 
 * 注意：此守卫假设已经通过网关进行了JWT验证，
 * 用户信息通过请求头传递，无需在此服务中再次验证JWT
 */
@Injectable()
export class AuthGuard implements CanActivate {
  constructor(
    private readonly reflector: Reflector,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    // 检查是否为公开端点
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    
    if (isPublic) {
      return true;
    }

    const request = context.switchToHttp().getRequest<Request>();
    
    // 从请求头中获取用户信息（由网关传递）
    const userContext = this.extractUserFromHeaders(request);
    console.log(userContext);
    if (!userContext.userId) {
      throw new UnauthorizedException('网关未传递用户身份信息，请检查网关配置');
    }

    // 在异步上下文中设置用户信息
    const contextMap = new Map<string, any>();
    
    // 设置用户信息到上下文中
    if (userContext.userId) contextMap.set(SecurityConstants.DETAILS_USER_ID, String(userContext.userId));
    if (userContext.username) contextMap.set(SecurityConstants.DETAILS_USERNAME, userContext.username);
    if (userContext.userKey) contextMap.set(SecurityConstants.USER_KEY, userContext.userKey);
    if (userContext.permissions?.length) contextMap.set(SecurityConstants.ROLE_PERMISSION, userContext.permissions.join(','));
    if (userContext.roles?.length) contextMap.set(SecurityConstants.ROLES, userContext.roles.join(','));
    if (userContext.deptId) contextMap.set(SecurityConstants.DEPT_ID, String(userContext.deptId));
    if (userContext.dataScope) contextMap.set(SecurityConstants.DATA_SCOPE, userContext.dataScope);

    // 运行在指定上下文中（这将在请求处理期间保持上下文）
    return SecurityContextHolder.run(contextMap, () => {
      // 同时将用户信息附加到请求对象，保持向后兼容性
      request['user'] = {
        userId: userContext.userId,
        username: userContext.username,
        roles: userContext.roles || [],
        permissions: userContext.permissions || [],
        userKey: userContext.userKey,
        deptId: userContext.deptId,
        dataScope: userContext.dataScope,
      };

      console.log('用户认证成功:', {
        userId: userContext.userId,
        username: userContext.username,
        roles: userContext.roles,
        permissions: userContext.permissions,
        source: '网关请求头',
        timestamp: new Date().toISOString(),
      });

      return true;
    });
  }

  /**
   * 从请求头中提取用户信息（由网关传递）
   * 支持多种字段名格式（驼峰、下划线等）
   */
  private extractUserFromHeaders(request: Request): UserContext {
    const headers = request.headers;
    
    // 辅助函数：获取请求头值，支持多种字段名格式
    const getHeaderValue = (primaryKey: string): string => {
      // 获取该字段的所有可能的名称
      const alternatives = SecurityConstants.FIELD_ALTERNATIVES[primaryKey] || [primaryKey];
      
      for (const key of alternatives) {
        const value = headers[key.toLowerCase()];
        if (value) {
          return Array.isArray(value) ? value[0] || '' : value || '';
        }
      }
      
      // 如果都没找到，尝试使用字段转换器自动查找
      const headerObj = Object.keys(headers).reduce((acc, key) => {
        acc[key] = Array.isArray(headers[key]) ? headers[key][0] : headers[key];
        return acc;
      }, {} as Record<string, string>);
      
      // 尝试通过字段转换器获取值
      const transformedValue = FieldTransformer.getFieldValue(headerObj, primaryKey);
      return transformedValue || '';
    };

    // 从请求头中提取用户信息
    const userContext: UserContext = {
      userId: this.parseNumber(getHeaderValue(SecurityConstants.DETAILS_USER_ID)),
      username: getHeaderValue(SecurityConstants.DETAILS_USERNAME),
      userKey: getHeaderValue(SecurityConstants.USER_KEY),
      deptId: this.parseNumber(getHeaderValue(SecurityConstants.DEPT_ID)),
      dataScope: getHeaderValue(SecurityConstants.DATA_SCOPE),
    };

    // 解析权限信息（逗号分隔的字符串）
    const permissionsStr = getHeaderValue(SecurityConstants.ROLE_PERMISSION);
    if (permissionsStr) {
      userContext.permissions = permissionsStr.split(',').filter(p => p.trim()).map(p => p.trim());
    }

    // 解析角色信息（逗号分隔的字符串）
    const rolesStr = getHeaderValue(SecurityConstants.ROLES);
    if (rolesStr) {
      userContext.roles = rolesStr.split(',').filter(r => r.trim()).map(r => r.trim());
    }

    // 记录调试信息
    console.log('请求头字段匹配结果（若依标准）:', {
      'user_id': getHeaderValue(SecurityConstants.DETAILS_USER_ID),
      'username': getHeaderValue(SecurityConstants.DETAILS_USERNAME),
      'user_key': getHeaderValue(SecurityConstants.USER_KEY),
      'dept_id': getHeaderValue(SecurityConstants.DEPT_ID),
      'data_scope': getHeaderValue(SecurityConstants.DATA_SCOPE),
      'role_permission': getHeaderValue(SecurityConstants.ROLE_PERMISSION),
      'roles': getHeaderValue(SecurityConstants.ROLES),
      'from_source': getHeaderValue(SecurityConstants.FROM_SOURCE),
      'Authorization': getHeaderValue(SecurityConstants.AUTHORIZATION_HEADER),
      originalHeaders: Object.keys(headers),
    });

    return userContext;
  }

  /**
   * 安全地解析数字，失败时返回undefined
   */
  private parseNumber(value: string): number | undefined {
    const num = parseInt(value, 10);
    return isNaN(num) ? undefined : num;
  }
}

/**
 * 用户信息接口 - 兼容若依系统和原有接口
 */
export interface UserInfo {
  userId?: number;
  username?: string;
  roles?: string[];
  permissions?: string[];
  userKey?: string;
  deptId?: number;
  dataScope?: string;
} 