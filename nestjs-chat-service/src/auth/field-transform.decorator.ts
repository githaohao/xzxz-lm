import { SetMetadata } from '@nestjs/common';

/**
 * 字段转换相关的元数据键
 */
export const DISABLE_FIELD_TRANSFORM_KEY = 'disableFieldTransform';
export const FIELD_TRANSFORM_OPTIONS_KEY = 'fieldTransformOptions';

/**
 * 禁用字段转换装饰器
 * 用于标记不需要进行字段名转换的端点
 */
export const DisableFieldTransform = () => SetMetadata(DISABLE_FIELD_TRANSFORM_KEY, true);

/**
 * 字段转换选项接口
 */
export interface FieldTransformOptions {
  /** 禁用请求体转换 */
  disableRequestTransform?: boolean;
  /** 禁用响应体转换 */
  disableResponseTransform?: boolean;
  /** 仅转换指定字段 */
  includeFields?: string[];
  /** 排除指定字段 */
  excludeFields?: string[];
}

/**
 * 自定义字段转换选项装饰器
 * 用于精细控制字段转换行为
 */
export const FieldTransformOptions = (options: FieldTransformOptions) => 
  SetMetadata(FIELD_TRANSFORM_OPTIONS_KEY, options); 