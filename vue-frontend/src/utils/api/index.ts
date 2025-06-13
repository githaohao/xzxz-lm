/**
 * API模块统一导出
 * 拆分后的模块化API接口，保持向后兼容性
 */

// 核心客户端
export { api, ApiClient, ApiError } from './client'

// 工具函数
export { 
  convertToBackendMessages, 
  convertToChatMessage, 
  convertToMessage 
} from './utils'

// LM聊天相关
export { 
  sendTextMessage, 
  sendMultimodalMessage, 
  healthCheck 
} from './chat'

// 语音相关
export { 
  sendVoiceMessage, 
  synthesizeSpeech, 
  checkFunAudioStatus, 
  clearConversationHistory 
} from './voice'

// 文件和RAG相关
export { 
  uploadFile, 
  getAllDocuments, 
  deleteDocument, 
  searchDocuments, 
  processDocumentForRAG, 
  getDocumentInfo,
  getDocumentChunks,
  getSessionDocuments,
  // 知识库管理
  createKnowledgeBase,
  getAllKnowledgeBases,
  getKnowledgeBase,
  updateKnowledgeBase,
  deleteKnowledgeBase,
  addDocumentsToKnowledgeBase,
  removeDocumentsFromKnowledgeBase,
  getKnowledgeBaseDocuments
} from './file'

// 用户系统相关
export { 
  getCaptcha, 
  login, 
  logout, 
  getUserInfo, 
  getUserProfile, 
  updateUserProfile, 
  uploadAvatar, 
  getMenuList, 
  getRouterList, 
  refreshToken, 
  checkPermission, 
  checkRole, 
  checkAdmin, 
  getCurrentUser, 
  checkLogin 
} from './auth'

// 聊天历史相关
export { 
  createChatSession, 
  getChatSessions, 
  getChatSessionById, 
  updateChatSession, 
  deleteChatSession, 
  archiveChatSession, 
  restoreChatSession, 
  getChatSessionMessages, 
  addChatMessage, 
  addChatMessagesBatch, 
  deleteChatMessage, 
  getChatStats, 
  checkChatHistoryHealth 
} from './history'

// 重新导入api实例用于默认导出
import { api } from './client'

// 默认导出api客户端实例
export default api 