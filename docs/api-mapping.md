# API地址对照表

本文档说明前端API配置与后端路由的对应关系，确保前后端接口调用的准确性。

## 📁 文件位置

- 前端配置：`vue-frontend/src/utils/api-config.ts`
- 后端路由：`backend/app/routes/`

## 🔄 地址对应关系

### 1. LM Studio聊天服务
| 前端配置 | 后端路由 | 说明 |
|---------|---------|------|
| `/api/lm/chat/stream` | `chat.router` | 流式文本聊天 |
| `/api/lm/chat/multimodal/stream/processed` | `chat.router` | 多模态流式聊天 |
| `/api/lm/upload` | `chat.router` | 文件上传 |
| `/api/lm/ocr` | `chat.router` | OCR文字识别 |
| `/api/lm/rag/*` | `chat.router` | RAG文档处理 |
| `/api/lm/health` | `health.router` | 系统健康检查 |

### 2. 语音服务
| 前端配置 | 后端路由 | 说明 |
|---------|---------|------|
| `/voice/chat` | `voice.router` (prefix="/voice") | 语音对话 |
| `/voice/speech/synthesize` | `voice.router` (prefix="/voice") | 语音合成 |
| `/voice/engine` | `voice.router` (prefix="/voice") | 语音引擎状态 |
| `/voice/conversation/{id}` | `voice.router` (prefix="/voice") | 对话管理 |
| `/voice/ws/voice` | `voice.router` (prefix="/voice") | WebSocket连接 |

### 3. 用户聊天历史服务
| 前端配置 | 后端路由 | 说明 |
|---------|---------|------|
| `/api/user/chat/sessions` | `chat_history.router` (prefix="/api/user/chat") | 会话管理 |
| `/api/user/chat/sessions/{id}` | `chat_history.router` | 会话详情 |
| `/api/user/chat/sessions/{id}/messages` | `chat_history.router` | 消息管理 |
| `/api/user/chat/messages/batch` | `chat_history.router` | 批量消息处理 |
| `/api/user/chat/stats` | `chat_history.router` | 聊天统计 |
| `/api/user/chat/health` | `chat_history.router` | 服务健康检查 |

### 4. 用户知识库服务
| 前端配置 | 后端路由 | 说明 |
|---------|---------|------|
| `/api/user/rag/documents/upload` | `user_rag.router` (prefix="/api/user/rag") | 文档上传 |
| `/api/user/rag/documents` | `user_rag.router` | 文档列表 |
| `/api/user/rag/search` | `user_rag.router` | 文档搜索 |
| `/api/user/rag/documents/{id}/chunks` | `user_rag.router` | 文档分块 |
| `/api/user/rag/stats` | `user_rag.router` | RAG统计 |
| `/api/user/rag/health` | `user_rag.router` | 服务健康检查 |

### 5. 若依用户系统
| 前端配置 | 后端路由 | 说明 |
|---------|---------|------|
| `/api/auth/login` | 若依Gateway | 用户登录 |
| `/api/auth/captcha` | 若依Gateway | 验证码 |
| `/api/system/*` | 若依Gateway | 系统管理 |

## 🔧 路由注册（backend/app/main.py）

```python
# 注册路由
app.include_router(chat.router)                    # LM Studio聊天服务
app.include_router(health.router)                  # 健康检查服务
app.include_router(voice.router, prefix="/voice", tags=["voice"])    # 语音服务
app.include_router(chat_history.router)            # 用户聊天历史服务
app.include_router(user_rag.router)               # 用户知识库服务
```

## ✅ 验证方法

### 1. 健康检查端点测试
```bash
# 测试LM服务
curl http://localhost:8000/api/lm/health

# 测试语音服务
curl http://localhost:8000/voice/engine

# 测试用户聊天历史服务
curl http://localhost:8000/api/user/chat/health

# 测试用户知识库服务
curl http://localhost:8000/api/user/rag/health
```

### 2. API文档访问
```bash
# 访问API文档
http://localhost:8000/docs

# 查看路由信息
http://localhost:8000/openapi.json
```

## 🚨 常见问题

### 1. 404错误
- 检查前端配置的API路径是否与后端路由匹配
- 确认路由前缀设置正确
- 验证路由是否在main.py中正确注册

### 2. CORS问题
- 检查`app/config.py`中的`allowed_origins`配置
- 确认前端开发服务器地址在允许列表中

### 3. 认证问题
- 确认用户认证中间件正确配置
- 检查请求头中是否包含正确的认证信息

## 📝 更新流程

当需要修改API地址时：

1. **后端变更**：
   - 修改`backend/app/routes/`下的对应路由文件
   - 更新`backend/app/main.py`中的路由注册

2. **前端变更**：
   - 更新`vue-frontend/src/utils/api-config.ts`中的端点配置
   - 修改相关的API客户端文件

3. **文档更新**：
   - 更新本文档的对照表
   - 更新README.md中的API接口说明

4. **测试验证**：
   - 运行健康检查测试
   - 验证前端调用是否正常
   - 确认API文档更新 