/**
 * 字段名转换工具类
 * 支持下划线命名和驼峰命名之间的相互转换
 */
export class FieldTransformer {
  /**
   * 下划线转驼峰
   * user_id -> userId
   * dept_id -> deptId
   */
  static toCamelCase(str: string): string {
    return str.replace(/_([a-z])/g, (match, letter) => letter.toUpperCase());
  }

  /**
   * 驼峰转下划线
   * userId -> user_id
   * deptId -> dept_id
   */
  static toSnakeCase(str: string): string {
    return str.replace(/([A-Z])/g, '_$1').toLowerCase();
  }

  /**
   * 将对象的键从下划线转换为驼峰
   */
  static objectKeysToCamelCase<T = any>(obj: Record<string, any>): T {
    if (!obj || typeof obj !== 'object') {
      return obj as T;
    }

    const result: Record<string, any> = {};
    
    for (const [key, value] of Object.entries(obj)) {
      const camelKey = this.toCamelCase(key);
      
      // 递归处理嵌套对象
      if (Array.isArray(value)) {
        result[camelKey] = value.map(item => 
          typeof item === 'object' && item !== null 
            ? this.objectKeysToCamelCase(item)
            : item
        );
      } else if (typeof value === 'object' && value !== null) {
        result[camelKey] = this.objectKeysToCamelCase(value);
      } else {
        result[camelKey] = value;
      }
    }

    return result as T;
  }

  /**
   * 将对象的键从驼峰转换为下划线
   */
  static objectKeysToSnakeCase<T = any>(obj: Record<string, any>): T {
    if (!obj || typeof obj !== 'object') {
      return obj as T;
    }

    const result: Record<string, any> = {};
    
    for (const [key, value] of Object.entries(obj)) {
      const snakeKey = this.toSnakeCase(key);
      
      // 递归处理嵌套对象
      if (Array.isArray(value)) {
        result[snakeKey] = value.map(item => 
          typeof item === 'object' && item !== null 
            ? this.objectKeysToSnakeCase(item)
            : item
        );
      } else if (typeof value === 'object' && value !== null) {
        result[snakeKey] = this.objectKeysToSnakeCase(value);
      } else {
        result[snakeKey] = value;
      }
    }

    return result as T;
  }

  /**
   * 字段映射配置 - 与若依系统标准保持一致
   * 支持下划线到驼峰的映射
   */
  static readonly FIELD_MAPPING = {
    // 若依系统标准字段 (下划线 -> 驼峰)
    'user_id': 'userId',
    'username': 'username',  // 保持不变
    'user_key': 'userKey',
    'login_user': 'loginUser',
    'role_permission': 'rolePermission',
    'from_source': 'fromSource',
    
    // 扩展字段
    'dept_id': 'deptId',
    'data_scope': 'dataScope',
    'roles': 'roles',  // 保持不变
    
    // 通用字段
    'created_at': 'createdAt',
    'updated_at': 'updatedAt',
    'deleted_at': 'deletedAt',
    'created_by': 'createdBy',
    'updated_by': 'updatedBy',
    
    // 反向映射 (驼峰 -> 下划线)
    'userId': 'user_id',
    'userKey': 'user_key',
    'loginUser': 'login_user',
    'rolePermission': 'role_permission',
    'fromSource': 'from_source',
    'deptId': 'dept_id',
    'dataScope': 'data_scope',
    'createdAt': 'created_at',
    'updatedAt': 'updated_at',
    'deletedAt': 'deleted_at',
    'createdBy': 'created_by',
    'updatedBy': 'updated_by',
  };

  /**
   * 使用预定义映射转换字段名
   */
  static mapFieldName(fieldName: string): string {
    return this.FIELD_MAPPING[fieldName] || fieldName;
  }

  /**
   * 使用预定义映射转换对象键名
   */
  static mapObjectKeys<T = any>(obj: Record<string, any>, direction: 'toSnake' | 'toCamel' = 'toCamel'): T {
    if (!obj || typeof obj !== 'object') {
      return obj as T;
    }

    const result: Record<string, any> = {};
    
    for (const [key, value] of Object.entries(obj)) {
      // 使用预定义映射或自动转换
      let mappedKey: string;
      if (direction === 'toCamel') {
        mappedKey = this.FIELD_MAPPING[key] || this.toCamelCase(key);
      } else {
        mappedKey = this.FIELD_MAPPING[key] || this.toSnakeCase(key);
      }
      
      // 递归处理嵌套对象
      if (Array.isArray(value)) {
        result[mappedKey] = value.map(item => 
          typeof item === 'object' && item !== null 
            ? this.mapObjectKeys(item, direction)
            : item
        );
      } else if (typeof value === 'object' && value !== null) {
        result[mappedKey] = this.mapObjectKeys(value, direction);
      } else {
        result[mappedKey] = value;
      }
    }

    return result as T;
  }

  /**
   * 从多种可能的字段名中获取值
   * 支持同时检查驼峰和下划线格式
   */
  static getFieldValue(obj: Record<string, any>, fieldName: string): any {
    // 首先尝试原始字段名
    if (obj.hasOwnProperty(fieldName)) {
      return obj[fieldName];
    }
    
    // 尝试映射后的字段名
    const mappedName = this.mapFieldName(fieldName);
    if (mappedName !== fieldName && obj.hasOwnProperty(mappedName)) {
      return obj[mappedName];
    }
    
    // 尝试自动转换
    const camelCase = this.toCamelCase(fieldName);
    if (obj.hasOwnProperty(camelCase)) {
      return obj[camelCase];
    }
    
    const snakeCase = this.toSnakeCase(fieldName);
    if (obj.hasOwnProperty(snakeCase)) {
      return obj[snakeCase];
    }
    
    return undefined;
  }
} 