# 字段名自动转换功能 - 若依系统标准

## 概述

本系统基于若依微服务架构实现了完整的字段名自动转换功能，严格遵循若依系统的SecurityConstants标准，支持在下划线命名（snake_case）和驼峰命名（camelCase）之间自动转换。

## 若依系统标准字段

### 核心认证字段

| 常量名 | 字段值 | 说明 |
|-------|--------|-----|
| DETAILS_USER_ID | `user_id` | 用户ID字段 |
| DETAILS_USERNAME | `username` | 用户名字段 |
| AUTHORIZATION_HEADER | `Authorization` | 授权信息字段 |
| FROM_SOURCE | `from-source` | 请求来源 |
| INNER | `inner` | 内部请求标识 |
| USER_KEY | `user_key` | 用户标识 |
| LOGIN_USER | `login_user` | 登录用户 |
| ROLE_PERMISSION | `role_permission` | 角色权限 |

### 扩展字段

| 字段名 | 转换后 | 说明 |
|-------|--------|-----|
| `user_id` | `userId` | 用户ID |
| `username` | `username` | 用户名（保持不变） |
| `user_key` | `userKey` | 用户密钥 |
| `role_permission` | `rolePermission` | 角色权限 |
| `dept_id` | `deptId` | 部门ID |
| `data_scope` | `dataScope` | 数据权限范围 |
| `from_source` | `fromSource` | 请求来源 |

## 功能特性

### 1. 若依标准兼容
- 完全遵循若依SecurityConstants规范
- 支持若依网关传递的所有标准请求头
- 与若依微服务架构无缝集成

### 2. 智能字段转换
- **请求体转换**: 前端驼峰 → 后端下划线
- **响应体转换**: 后端下划线 → 前端驼峰
- **请求头多格式支持**: 兼容不同的命名格式

### 3. 兼容性保障
- 支持备选字段名格式
- 向后兼容旧版本接口
- 渐进式迁移支持

## 使用示例

### 基本转换示例

```typescript
// 前端发送 (驼峰格式)
{
  userId: 123,
  username: "admin",
  userKey: "unique_key",
  deptId: 1,
  rolePermission: "admin:view"
}

// 自动转换为后端接收 (若依标准)
{
  user_id: 123,
  username: "admin",        // 保持不变
  user_key: "unique_key",
  dept_id: 1,
  role_permission: "admin:view"
}
```

### 若依网关请求头示例

```http
# 若依网关传递的标准请求头
user_id: 123
username: admin
user_key: unique_key_123
role_permission: admin:view,user:list
from-source: gateway
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### API控制器使用

```typescript
import { DisableFieldTransform, FieldTransformOptions } from '../auth/field-transform.decorator';

@Controller('chat')
export class ChatController {
  
  // 默认启用字段转换
  @Get('sessions')
  getSessions() {
    // 返回数据自动转换：user_id -> userId
    return { user_id: 123, session_id: 456 };
  }

  // 禁用字段转换 (返回若依原始格式)
  @Get('raw-sessions')
  @DisableFieldTransform()
  getRawSessions() {
    // 保持若依标准格式不变
    return { user_id: 123, session_id: 456 };
  }

  // 精细控制转换
  @Post('create')
  @FieldTransformOptions({
    includeFields: ['user_id', 'session_name']
  })
  createSession(@Body() body: any) {
    // 只转换指定字段
    return body;
  }
}
```

## 若依网关集成

### 网关请求头处理

系统会自动处理若依网关传递的请求头：

```typescript
// 支持的请求头格式 (按优先级)
'user_id'      // 若依标准 (优先)
'user-id'      // kebab-case 备选
'userid'       // 紧凑格式 备选

'user_key'     // 若依标准 (优先)  
'user-key'     // kebab-case 备选
'userkey'      // 紧凑格式 备选
```

### 认证守卫集成

```typescript
// AuthGuard 自动处理若依网关认证
@UseGuards(AuthGuard)
@Controller('protected')
export class ProtectedController {
  
  @Get('user-info')
  getUserInfo(@Request() req) {
    // 自动获取若依网关传递的用户信息
    return {
      userId: req.user.userId,           // 来自 user_id 请求头
      username: req.user.username,       // 来自 username 请求头  
      userKey: req.user.userKey,         // 来自 user_key 请求头
      permissions: req.user.permissions, // 来自 role_permission 请求头
    };
  }
}
```

## 配置选项

### 1. 全局配置

字段转换已在 `app.module.ts` 中全局启用：

```typescript
providers: [
  {
    provide: APP_INTERCEPTOR,
    useClass: FieldTransformInterceptor,
  },
]
```

### 2. 装饰器控制

```typescript
// 完全禁用转换
@DisableFieldTransform()

// 仅转换响应，不转换请求
@FieldTransformOptions({
  disableRequestTransform: true
})

// 仅转换指定字段
@FieldTransformOptions({
  includeFields: ['user_id', 'session_name']
})

// 排除特定字段
@FieldTransformOptions({
  excludeFields: ['metadata', 'raw_config']
})
```

## 调试信息

开发环境下会输出详细的转换日志：

```
请求头字段匹配结果（若依标准）: {
  user_id: '123',
  username: 'admin', 
  user_key: 'unique_key_123',
  role_permission: 'admin:view,user:list',
  from_source: 'gateway',
  Authorization: 'Bearer eyJhbGciOiJIUzI1NiIs...',
  originalHeaders: ['user_id', 'username', 'authorization', ...]
}

响应体字段转换（下划线->驼峰）: {
  original: ['user_id', 'session_id', 'created_at'],
  transformed: ['userId', 'sessionId', 'createdAt']
}
```

## 最佳实践

### 1. 遵循若依标准
- 后端统一使用若依SecurityConstants定义的字段名
- 前端使用驼峰命名，让系统自动转换
- 网关请求头使用若依标准格式

### 2. 性能优化
- 仅在必要时禁用转换
- 生产环境关闭详细日志
- 优先使用字段包含而非排除

### 3. 兼容性考虑
- 保持与若依系统的一致性
- 测试多种请求头格式的兼容性
- 验证嵌套对象和数组的转换

## 故障排除

### 常见问题

1. **获取不到用户信息**
   ```bash
   # 检查若依网关是否正确传递请求头
   curl -H "user_id: 123" -H "username: admin" http://localhost:3002/api/protected
   ```

2. **字段转换不生效**
   - 确认没有使用 `@DisableFieldTransform`
   - 检查字段是否在映射表中
   - 查看控制台调试日志

3. **与若依系统不兼容**
   - 验证SecurityConstants是否与若依一致
   - 检查网关配置和请求头传递
   - 确认字段名格式符合若依标准

### 调试命令

```bash
# 启动服务并查看日志
cd nestjs-chat-service
npm run start:dev

# 测试字段转换
curl -X POST http://localhost:3002/api/test \
  -H "Content-Type: application/json" \
  -H "user_id: 123" \
  -H "username: admin" \
  -d '{"userId": 123, "sessionName": "test"}'
```

## 扩展开发

### 添加新字段映射

在 `field-transformer.ts` 中添加新的字段映射：

```typescript
static readonly FIELD_MAPPING = {
  // 现有映射...
  
  // 新增若依业务字段
  'business_id': 'businessId',
  'tenant_id': 'tenantId',
  'org_id': 'orgId',
  
  // 反向映射
  'businessId': 'business_id',
  'tenantId': 'tenant_id', 
  'orgId': 'org_id',
};
```

### 自定义转换逻辑

```typescript
// 继承并扩展字段转换器
export class CustomFieldTransformer extends FieldTransformer {
  static customTransform(obj: any): any {
    // 自定义转换逻辑
    return super.mapObjectKeys(obj, 'toCamel');
  }
}
```

这样，您的NestJS服务现在完全遵循若依系统的标准，能够无缝集成到若依微服务架构中！ 