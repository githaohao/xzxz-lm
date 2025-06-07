# 网关认证集成指南

本文档说明了如何将NestJS聊天历史服务与若依微服务网关进行认证集成。

## 概述

NestJS聊天历史服务现已修改为从网关传递的请求头中直接获取用户信息，无需在服务内部进行JWT验证。这种架构模式符合微服务最佳实践，将认证职责集中在网关层。

## 架构说明

```
客户端 → 网关(JWT验证) → 微服务(请求头认证)
```

1. **客户端**：发送带有JWT Token的请求
2. **网关**：验证JWT Token，将用户信息放入请求头
3. **微服务**：从请求头获取用户信息，无需JWT验证

## 请求头格式

网关需要在转发请求时添加以下请求头：

| 请求头名称 | 描述 | 示例值 | 必需 |
|------------|------|--------|------|
| `user-id` | 用户ID | `1` | 是 |
| `username` | 用户名 | `admin` | 是 |
| `user-key` | 用户唯一标识 | `uuid-string` | 否 |
| `roles` | 用户角色(逗号分隔) | `admin,user` | 否 |
| `role-permission` | 用户权限(逗号分隔) | `system:user:list,system:role:list` | 否 |
| `dept-id` | 部门ID | `100` | 否 |
| `data-scope` | 数据权限范围 | `1` | 否 |

## 使用方法

### 1. SecurityContextHolder 静态方法

类似于若依的SecurityContextHolder，可以在任何地方获取当前用户信息：

```typescript
import { SecurityContextHolder } from '../auth/security-context';

// 获取用户ID
const userId = SecurityContextHolder.getUserId();

// 获取用户名
const username = SecurityContextHolder.getUserName();

// 获取用户权限
const permissions = SecurityContextHolder.getPermissions();

// 获取用户角色
const roles = SecurityContextHolder.getRoles();

// 获取完整用户上下文
const userContext = SecurityContextHolder.getUserContext();
```

### 2. 控制器中使用请求对象

在控制器方法中，仍可以通过请求对象获取用户信息：

```typescript
@Get('sessions')
async getUserSessions(@Request() req: { user: UserInfo }) {
  const userId = req.user.userId;
  const username = req.user.username;
  const roles = req.user.roles;
  const permissions = req.user.permissions;
  
  // 业务逻辑...
}
```

### 3. 服务层中使用

在服务层中，可以直接使用SecurityContextHolder：

```typescript
import { SecurityContextHolder } from '../auth/security-context';

@Injectable()
export class ChatService {
  async createSession(sessionData: CreateSessionDto) {
    // 从上下文获取当前用户ID
    const currentUserId = SecurityContextHolder.getUserId();
    
    // 业务逻辑...
  }
}
```

## 测试端点

提供了测试端点用于验证认证集成：

```bash
# 测试网关认证（需要在请求头中包含用户信息）
curl -X GET http://localhost:3002/chat/test-auth \
  -H "user-id: 1" \
  -H "username: admin" \
  -H "roles: admin,user" \
  -H "role-permission: system:user:list,system:role:list"
```

## 网关配置示例

### Spring Cloud Gateway 配置

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: chat-service
          uri: http://localhost:3002
          predicates:
            - Path=/chat/**
          filters:
            - name: GatewayFilter
              args:
                add-request-header: |
                  user-id: #{claims['user_id']}
                  username: #{claims['username']}
                  roles: #{claims['roles']}
                  role-permission: #{claims['permissions']}
```

### HeaderInterceptor 示例

若依系统中的HeaderInterceptor实现：

```java
@Component
public class HeaderInterceptor implements HandlerInterceptor {
    
    @Override
    public boolean preHandle(HttpServletRequest request, 
                           HttpServletResponse response, 
                           Object handler) throws Exception {
        
        // 从JWT中获取用户信息
        String userId = SecurityUtils.getUserId().toString();
        String username = SecurityUtils.getUsername();
        String roles = String.join(",", SecurityUtils.getRoles());
        String permissions = String.join(",", SecurityUtils.getPermissions());
        
        // 设置到请求头中
        request.setAttribute("user-id", userId);
        request.setAttribute("username", username);
        request.setAttribute("roles", roles);
        request.setAttribute("role-permission", permissions);
        
        return true;
    }
}
```

## 错误处理

### 认证失败

如果请求头中没有必需的用户信息，将返回：

```json
{
  "statusCode": 401,
  "message": "网关未传递用户身份信息，请检查网关配置",
  "timestamp": "2025-01-01T12:00:00.000Z"
}
```

### 调试信息

认证成功时，控制台会输出调试信息：

```
用户认证成功: {
  userId: 1,
  username: 'admin',
  roles: ['admin', 'user'],
  permissions: ['system:user:list'],
  source: '网关请求头',
  timestamp: '2025-01-01T12:00:00.000Z'
}
```

## 迁移指南

### 从JWT认证迁移

1. 移除JWT相关依赖和配置
2. 修改AuthGuard使用SecurityContextHolder
3. 确保网关正确传递用户信息
4. 更新测试用例

### 向后兼容性

- `req.user` 对象仍然可用，包含所有用户信息
- UserInfo接口保持兼容，添加了可选字段
- 所有现有的控制器方法无需修改

## 最佳实践

1. **安全性**：确保只有网关能访问微服务，使用网络隔离
2. **验证**：在网关层进行充分的JWT验证
3. **监控**：记录认证失败和异常情况
4. **缓存**：合理缓存用户信息，减少网关压力

## 故障排除

### 常见问题

1. **用户信息为空**
   - 检查网关是否正确传递请求头
   - 验证请求头名称是否正确（小写）

2. **权限验证失败**
   - 确认权限字符串格式正确（逗号分隔）
   - 检查角色信息是否完整

3. **上下文丢失**
   - 确保在异步操作中正确传递上下文
   - 使用SecurityContextHolder的run方法

### 调试步骤

1. 检查请求头：访问 `/chat/test-auth` 端点
2. 查看日志：观察认证成功/失败日志
3. 验证网关：确认网关正确解析JWT并设置请求头 