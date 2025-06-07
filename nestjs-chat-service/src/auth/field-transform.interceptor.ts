import { Injectable, NestInterceptor, ExecutionContext, CallHandler } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { FieldTransformer } from './field-transformer';
import { 
  DISABLE_FIELD_TRANSFORM_KEY, 
  FIELD_TRANSFORM_OPTIONS_KEY, 
  FieldTransformOptions 
} from './field-transform.decorator';

/**
 * 字段转换拦截器
 * 自动将API响应中的字段名从下划线格式转换为驼峰格式
 * 也支持请求体的字段转换
 */
@Injectable()
export class FieldTransformInterceptor implements NestInterceptor {
  constructor(private readonly reflector: Reflector) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    // 检查是否禁用字段转换
    const isDisabled = this.reflector.getAllAndOverride<boolean>(DISABLE_FIELD_TRANSFORM_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);

    if (isDisabled) {
      return next.handle();
    }

    // 获取字段转换选项
    const options = this.reflector.getAllAndOverride<FieldTransformOptions>(FIELD_TRANSFORM_OPTIONS_KEY, [
      context.getHandler(),
      context.getClass(),
    ]) || {};

    const request = context.switchToHttp().getRequest();
    
    // 转换请求体字段名（如果有且未被禁用）
    if (!options.disableRequestTransform && request.body && typeof request.body === 'object') {
      // 将请求体中的驼峰字段转换为下划线格式发送给后端服务
      request.body = this.transformObject(request.body, 'toSnake', options);
      console.log('请求体字段转换（驼峰->下划线）:', request.body);
    }

    // 转换响应体字段名
    return next.handle().pipe(
      map((data) => {
        if (!options.disableResponseTransform && data && typeof data === 'object') {
          // 将响应数据中的下划线字段转换为驼峰格式返回给前端
          const transformedData = this.transformObject(data, 'toCamel', options);
          console.log('响应体字段转换（下划线->驼峰）:', {
            original: this.getSampleFields(data),
            transformed: this.getSampleFields(transformedData)
          });
          return transformedData;
        }
        return data;
      })
    );
  }

  /**
   * 根据选项转换对象字段
   */
  private transformObject(obj: any, direction: 'toSnake' | 'toCamel', options: FieldTransformOptions): any {
    if (!obj || typeof obj !== 'object') {
      return obj;
    }

    // 如果有包含字段列表，只转换指定字段
    if (options.includeFields?.length) {
      const result = { ...obj };
      for (const field of options.includeFields) {
        if (obj.hasOwnProperty(field)) {
          const newKey = direction === 'toCamel' 
            ? FieldTransformer.toCamelCase(field)
            : FieldTransformer.toSnakeCase(field);
          if (newKey !== field) {
            result[newKey] = obj[field];
            delete result[field];
          }
        }
      }
      return result;
    }

    // 排除指定字段
    if (options.excludeFields?.length) {
      const result = FieldTransformer.mapObjectKeys(obj, direction);
      for (const field of options.excludeFields) {
        if (obj.hasOwnProperty(field)) {
          result[field] = obj[field]; // 保持原字段名
        }
      }
      return result;
    }

    // 默认转换所有字段
    return FieldTransformer.mapObjectKeys(obj, direction);
  }

  /**
   * 获取对象的示例字段用于调试
   */
  private getSampleFields(obj: any, maxFields: number = 5): string[] {
    if (!obj || typeof obj !== 'object') {
      return [];
    }

    const keys = Object.keys(obj);
    return keys.slice(0, maxFields);
  }
} 