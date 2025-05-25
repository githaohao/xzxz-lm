import axios from 'axios'
import type { 
  Message, 
  VoiceMessage, 
  BackendMessage, 
  VoiceRecognitionResponse, 
  TTSRequest,
  ProcessedFile 
} from '@/types'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 转换消息格式为后端需要的格式
export function convertToBackendMessages(messages: Message[], limit: number = 10): BackendMessage[] {
  const recentMessages = messages.slice(-limit)
  
  return recentMessages.map(msg => ({
    id: msg.id,
    content: msg.content,
    message_type: "text",
    timestamp: msg.timestamp.toISOString(),
    is_user: msg.isUser,
    file_name: msg.fileInfo?.name || null,
    file_size: msg.fileInfo?.size || null
  }))
}

// 文本聊天流式API
export async function sendTextMessage(
  message: string,
  history: Message[],
  temperature: number = 0.7,
  maxTokens: number = 2048,
  signal?: AbortSignal
): Promise<Response> {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message,
      history: convertToBackendMessages(history),
      temperature,
      max_tokens: maxTokens
    }),
    signal
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }

  return response
}

// 多模态聊天流式API
export async function sendMultimodalMessage(
  message: string,
  history: Message[],
  fileData: ProcessedFile,
  temperature: number = 0.7,
  maxTokens: number = 2048,
  signal?: AbortSignal
): Promise<Response> {
  const response = await fetch('/api/chat/multimodal/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message,
      history: convertToBackendMessages(history),
      file_data: {
        name: fileData.name,
        type: fileData.type,
        size: fileData.size,
        ocr_text: fileData.ocrText || null
      },
      temperature,
      max_tokens: maxTokens
    }),
    signal
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }

  return response
}

// 语音聊天API
export async function sendVoiceMessage(
  audioBlob: Blob,
  sessionId: string,
  language: string = 'auto'
): Promise<VoiceRecognitionResponse> {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'voice.wav')
  formData.append('session_id', sessionId)
  formData.append('language', language)

  const response = await api.post<VoiceRecognitionResponse>('/voice/chat', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })

  return response.data
}

// TTS语音合成API
export async function synthesizeSpeech(params: TTSRequest): Promise<ArrayBuffer> {
  const response = await api.post('/voice/speech/synthesize', params, {
    responseType: 'arraybuffer'
  })

  return response.data
}

// 检查FunAudioLLM服务状态
export async function checkFunAudioStatus(): Promise<boolean> {
  try {
    const response = await api.get('/voice/engine')
    // 处理后端返回的嵌套数据结构
    if (response.data.success && response.data.engine && response.data.engine.status) {
      return response.data.engine.status.available || false
    }
    // 兼容旧的数据结构
    return response.data.available || false
  } catch (error) {
    console.error('检查FunAudioLLM状态失败:', error)
    return false
  }
}

// 清除对话历史
export async function clearConversationHistory(sessionId: string): Promise<boolean> {
  try {
    await api.delete(`/voice/conversation/${sessionId}`)
    return true
  } catch (error) {
    console.error('清除对话历史失败:', error)
    return false
  }
}

// 文件上传和处理
export async function uploadFile(file: File): Promise<ProcessedFile> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/chat/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })

  return {
    name: file.name,
    size: file.size,
    type: file.type,
    ocrText: response.data.ocr_text,
    processing: false
  }
}

// 健康检查
export async function healthCheck(): Promise<any> {
  const response = await api.get('/health')
  return response.data
}

export default api 