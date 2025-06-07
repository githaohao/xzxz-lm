// API配置文件
export const API_CONFIG = {
  // 基础URL配置
  BASE_URL: "",  // 不使用基础URL，直接使用完整路径
  
  // 超时配置
  TIMEOUT: {
    DEFAULT: 30000,      // 默认30秒
    UPLOAD: 60000,       // 文件上传60秒
    OCR: 99999999,       // OCR处理不限时
    RAG: 180000,         // RAG处理3分钟
    TTS: 60000,          // TTS合成60秒
    VOICE: 60000,        // 语音处理60秒
  },
  
  // API端点配置
  ENDPOINTS: {
    // LM聊天相关 (使用/api/lm前缀)
    CHAT_STREAM: '/api/lm/chat/stream',
    MULTIMODAL_STREAM: '/api/lm/chat/multimodal/stream/processed',
    
    // LM语音相关
    VOICE_CHAT: '/api/lm/voice/chat',
    VOICE_TTS: '/api/lm/voice/speech/synthesize',
    VOICE_ENGINE: '/api/lm/voice/engine',
    VOICE_CONVERSATION: '/api/lm/voice/conversation',
    
    // LM文件相关
    UPLOAD: '/api/lm/upload',
    OCR: '/api/lm/ocr',
    
    // LM RAG相关
    RAG_DOCUMENTS: '/api/lm/rag/documents',
    RAG_SEARCH: '/api/lm/rag/search',
    RAG_PROCESS: '/api/lm/rag/process',
    
    // LM系统相关
    HEALTH: '/api/lm/health',
    
    // 若依微服务用户系统 (直接使用完整路径)
    SYSTEM_LOGIN: '/api/auth/login',
    SYSTEM_LOGOUT: '/api/system/logout',
    SYSTEM_USER_PROFILE: '/api/system/user/profile',
    SYSTEM_USER_AVATAR: '/api/system/user/avatar',
    SYSTEM_MENU_LIST: '/api/system/menu/list',
    SYSTEM_REFRESH_TOKEN: '/api/system/refresh',
    SYSTEM_CAPTCHA: '/api/auth/captcha',
    SYSTEM_USER_INFO: '/api/system/user/getInfo',
    SYSTEM_ROUTER_LIST: '/api/system/getRouters',
    
    // 聊天历史服务 (使用/chat前缀)
    CHAT_HISTORY_SESSIONS: '/api/chat/sessions',
    CHAT_HISTORY_SESSION_DETAIL: '/api/chat/sessions',
    CHAT_HISTORY_SESSION_MESSAGES: '/api/chat/sessions',
    CHAT_HISTORY_MESSAGES_BATCH: '/api/chat/messages/batch',
    CHAT_HISTORY_STATS: '/api/chat/stats',
    CHAT_HISTORY_HEALTH: '/api/chat/health',
  },
  
  // 请求头配置
  HEADERS: {
    JSON: { 'Content-Type': 'application/json' },
    STREAM: { 'Accept': 'text/event-stream' },
    BINARY: { 'Accept': 'application/octet-stream' },
  },
  
  // 错误消息配置
  ERROR_MESSAGES: {
    TIMEOUT: '请求超时',
    NETWORK: '网络连接失败，请检查网络状态',
    UPLOAD_TIMEOUT: '文件上传超时',
    UPLOAD_FAILED: '文件上传失败',
    UNKNOWN: '未知错误',
  }
} as const

// 导出类型
export type ApiConfig = typeof API_CONFIG
export type ApiEndpoint = keyof typeof API_CONFIG.ENDPOINTS
export type ApiTimeout = keyof typeof API_CONFIG.TIMEOUT 