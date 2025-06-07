import { AsyncLocalStorage } from 'async_hooks';

/**
 * 安全上下文常量 - 与若依系统保持完全一致
 * 
 * @author ruoyi
 */
export class SecurityConstants {
  /**
   * 用户ID字段 - 与若依系统标准一致
   */
  static readonly DETAILS_USER_ID = 'user_id';
  
  /**
   * 用户名字段 - 与若依系统标准一致  
   */
  static readonly DETAILS_USERNAME = 'username';
  
  /**
   * 授权信息字段 - 与若依系统标准一致
   */
  static readonly AUTHORIZATION_HEADER = 'Authorization';
  
  /**
   * 请求来源 - 与若依系统标准一致
   */
  static readonly FROM_SOURCE = 'from-source';
  
  /**
   * 内部请求 - 与若依系统标准一致
   */
  static readonly INNER = 'inner';
  
  /**
   * 用户标识 - 与若依系统标准一致
   */
  static readonly USER_KEY = 'user_key';
  
  /**
   * 登录用户 - 与若依系统标准一致
   */
  static readonly LOGIN_USER = 'login_user';
  
  /**
   * 角色权限 - 与若依系统标准一致
   */
  static readonly ROLE_PERMISSION = 'role_permission';
  
  /** 扩展字段 - 角色信息 */
  static readonly ROLES = 'roles';
  
  /** 扩展字段 - 部门ID */
  static readonly DEPT_ID = 'dept_id';
  
  /** 扩展字段 - 数据权限 */
  static readonly DATA_SCOPE = 'data_scope';

  /**
   * 支持的字段名备选方案（兼容性考虑）
   */
  static readonly FIELD_ALTERNATIVES = {
    [SecurityConstants.DETAILS_USER_ID]: ['user_id', 'user-id', 'userid'],
    [SecurityConstants.DETAILS_USERNAME]: ['username', 'user_name', 'user-name'],
    [SecurityConstants.USER_KEY]: ['user_key', 'user-key', 'userkey'],
    [SecurityConstants.ROLE_PERMISSION]: ['role_permission', 'role-permission', 'rolepermission'],
    [SecurityConstants.ROLES]: ['roles'],
    [SecurityConstants.DEPT_ID]: ['dept_id', 'dept-id', 'deptid'],
    [SecurityConstants.DATA_SCOPE]: ['data_scope', 'data-scope', 'datascope'],
  };
}

/**
 * 用户上下文信息接口
 */
export interface UserContext {
  userId?: number;
  username?: string;
  userKey?: string;
  permissions?: string[];
  roles?: string[];
  deptId?: number;
  dataScope?: string;
  [key: string]: any;
}

/**
 * 安全上下文持有者
 * 类似于若依的SecurityContextHolder，用于获取当前线程中的用户信息
 * 注意：必须在网关通过请求头的方法传入，同时在拦截器设置值。否则这里无法获取
 */
export class SecurityContextHolder {
  private static readonly asyncLocalStorage = new AsyncLocalStorage<Map<string, any>>();

  /**
   * 设置上下文值
   */
  static set(key: string, value: any): void {
    const store = this.getLocalMap();
    store.set(key, value ?? '');
  }

  /**
   * 获取上下文值
   */
  static get(key: string): string {
    const store = this.getLocalMap();
    return String(store.get(key) ?? '');
  }

  /**
   * 获取指定类型的上下文值
   */
  static getValue<T>(key: string, defaultValue?: T): T {
    const store = this.getLocalMap();
    const value = store.get(key);
    return value !== undefined ? (value as T) : (defaultValue as T);
  }

  /**
   * 获取本地存储Map
   */
  static getLocalMap(): Map<string, any> {
    let store = this.asyncLocalStorage.getStore();
    if (!store) {
      store = new Map<string, any>();
      // 注意：这里不能设置store，因为我们不在异步上下文中
      // 实际应用中，这个Map应该在每个请求开始时初始化
    }
    return store;
  }

  /**
   * 设置本地存储Map
   */
  static setLocalMap(contextMap: Map<string, any>): void {
    // 在实际应用中，这通常在拦截器中使用asyncLocalStorage.run()方法
    console.log('Context map set with keys:', Array.from(contextMap.keys()));
  }

  /**
   * 运行在指定上下文中
   */
  static run<T>(contextMap: Map<string, any>, callback: () => T): T {
    return this.asyncLocalStorage.run(contextMap, callback);
  }

  /**
   * 获取用户ID
   */
  static getUserId(): number {
    const userId = this.get(SecurityConstants.DETAILS_USER_ID);
    return userId ? parseInt(userId, 10) : 0;
  }

  /**
   * 设置用户ID
   */
  static setUserId(userId: string | number): void {
    this.set(SecurityConstants.DETAILS_USER_ID, String(userId));
  }

  /**
   * 获取用户名
   */
  static getUserName(): string {
    return this.get(SecurityConstants.DETAILS_USERNAME);
  }

  /**
   * 设置用户名
   */
  static setUserName(username: string): void {
    this.set(SecurityConstants.DETAILS_USERNAME, username);
  }

  /**
   * 获取用户KEY
   */
  static getUserKey(): string {
    return this.get(SecurityConstants.USER_KEY);
  }

  /**
   * 设置用户KEY
   */
  static setUserKey(userKey: string): void {
    this.set(SecurityConstants.USER_KEY, userKey);
  }

  /**
   * 获取权限信息
   */
  static getPermissions(): string[] {
    const permissions = this.get(SecurityConstants.ROLE_PERMISSION);
    return permissions ? permissions.split(',').filter(p => p.trim()) : [];
  }

  /**
   * 设置权限信息
   */
  static setPermissions(permissions: string | string[]): void {
    const permissionStr = Array.isArray(permissions) ? permissions.join(',') : permissions;
    this.set(SecurityConstants.ROLE_PERMISSION, permissionStr);
  }

  /**
   * 获取角色信息
   */
  static getRoles(): string[] {
    const roles = this.get(SecurityConstants.ROLES);
    return roles ? roles.split(',').filter(r => r.trim()) : [];
  }

  /**
   * 设置角色信息
   */
  static setRoles(roles: string | string[]): void {
    const roleStr = Array.isArray(roles) ? roles.join(',') : roles;
    this.set(SecurityConstants.ROLES, roleStr);
  }

  /**
   * 获取部门ID
   */
  static getDeptId(): number {
    const deptId = this.get(SecurityConstants.DEPT_ID);
    return deptId ? parseInt(deptId, 10) : 0;
  }

  /**
   * 设置部门ID
   */
  static setDeptId(deptId: string | number): void {
    this.set(SecurityConstants.DEPT_ID, String(deptId));
  }

  /**
   * 获取完整的用户上下文信息
   */
  static getUserContext(): UserContext {
    return {
      userId: this.getUserId(),
      username: this.getUserName(),
      userKey: this.getUserKey(),
      permissions: this.getPermissions(),
      roles: this.getRoles(),
      deptId: this.getDeptId(),
      dataScope: this.get(SecurityConstants.DATA_SCOPE),
    };
  }

  /**
   * 清除上下文
   */
  static remove(): void {
    const store = this.getLocalMap();
    store.clear();
  }

  /**
   * 从请求头设置用户上下文
   */
  static setFromHeaders(headers: Record<string, string | string[] | undefined>): void {
    const getHeaderValue = (key: string): string => {
      const value = headers[key.toLowerCase()];
      return Array.isArray(value) ? value[0] || '' : value || '';
    };

    // 设置用户基本信息
    const userId = getHeaderValue(SecurityConstants.DETAILS_USER_ID);
    if (userId) this.setUserId(userId);

    const username = getHeaderValue(SecurityConstants.DETAILS_USERNAME);
    if (username) this.setUserName(username);

    const userKey = getHeaderValue(SecurityConstants.USER_KEY);
    if (userKey) this.setUserKey(userKey);

    // 设置权限和角色信息
    const permissions = getHeaderValue(SecurityConstants.ROLE_PERMISSION);
    if (permissions) this.setPermissions(permissions);

    const roles = getHeaderValue(SecurityConstants.ROLES);
    if (roles) this.setRoles(roles);

    // 设置部门信息
    const deptId = getHeaderValue(SecurityConstants.DEPT_ID);
    if (deptId) this.setDeptId(deptId);

    // 设置数据权限
    const dataScope = getHeaderValue(SecurityConstants.DATA_SCOPE);
    if (dataScope) this.set(SecurityConstants.DATA_SCOPE, dataScope);
  }
} 