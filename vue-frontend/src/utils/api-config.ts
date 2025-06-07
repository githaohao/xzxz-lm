// API配置文件
export const API_CONFIG = {
  // 基础URL配置
  BASE_URL: "/api",  // 不使用基础URL，直接使用完整路径
  
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
    CHAT_STREAM: '/lm/chat/stream',
    MULTIMODAL_STREAM: '/lm/chat/multimodal/stream/processed',
    
    // LM语音相关
    VOICE_CHAT: '/lm/voice/chat',
    VOICE_TTS: '/lm/voice/speech/synthesize',
    VOICE_ENGINE: '/lm/voice/engine',
    VOICE_CONVERSATION: '/lm/voice/conversation',
    
    // LM文件相关
    UPLOAD: '/lm/upload',
    OCR: '/lm/ocr',
    
    // LM RAG相关
    RAG_DOCUMENTS: '/lm/rag/documents',
    RAG_SEARCH: '/lm/rag/search',
    RAG_PROCESS: '/lm/rag/process',
    
    // LM系统相关
    HEALTH: '/lm/health',
    
    // 若依微服务用户系统 (使用/api/system前缀)
    SYSTEM_LOGIN: '/auth/login',
    SYSTEM_LOGOUT: '/system/logout',
    SYSTEM_USER_PROFILE: '/system/user/profile',
    SYSTEM_USER_AVATAR: '/system/user/avatar',
    SYSTEM_MENU_LIST: '/system/menu/list',
    SYSTEM_REFRESH_TOKEN: '/system/refresh',
    SYSTEM_CAPTCHA: '/system/captcha',
    SYSTEM_USER_INFO: '/system/getInfo',
    SYSTEM_ROUTER_LIST: '/system/getRouters',
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