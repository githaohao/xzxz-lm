/**
 * API模块 - 已优化拆分
 * 
 * 此文件已重构为模块化结构，原有功能已拆分到以下模块:
 * - utils/api/client.ts - 核心客户端和错误处理
 * - utils/chat.ts - LM聊天相关API  
 * - utils/api/voice.ts - 语音相关API
 * - utils/api/file.ts - 文件和RAG相关API
 * - utils/api/auth.ts - 用户系统API
 * - utils/api/history.ts - 聊天历史API
 * - utils/api/utils.ts - 工具函数
 * - utils/api/index.ts - 统一导出
 * 
 * 建议新代码直接从 './api/' 目录导入具体模块:
 * import { sendTextMessage } from '@/utils/chat'
 * import { login, logout } from '@/utils/api/auth'
 * 
 * 当前文件保持向后兼容性，重新导出新模块的所有功能
 */

// 重新导出所有API模块，保持向后兼容性
export * from './api/index'

// 默认导出api客户端实例
export { default } from './api/index' 