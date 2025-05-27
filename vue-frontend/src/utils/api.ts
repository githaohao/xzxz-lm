import axios from 'axios'
import type { 
  Message, 
  VoiceMessage, 
  BackendMessage, 
  VoiceRecognitionResponse, 
  TTSRequest,
  ProcessedFile,
  RAGSearchRequest,
  RAGSearchResponse
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
  const response = await fetch('/api/chat/multimodal/stream/processed', {
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
        content: fileData.content || null,
        ocr_completed: fileData.ocrCompleted || false,
        doc_id: fileData.doc_id || null,
        rag_enabled: fileData.rag_enabled || false
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
    },
    timeout: 60000  // 语音处理增加到1分钟超时
  })

  return response.data
}

// TTS语音合成API
export async function synthesizeSpeech(params: TTSRequest): Promise<ArrayBuffer> {
  const response = await api.post('/voice/speech/synthesize', params, {
    responseType: 'arraybuffer',
    timeout: 60000  // TTS合成增加到1分钟超时
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

  // 1. 先上传文件
  const uploadResponse = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 60000  // 文件上传增加到1分钟超时
  })

  const uploadResult = uploadResponse.data
  let ocrCompleted = false
  let content: string | undefined = undefined
  let docId: string | undefined = undefined
  let ragEnabled = false

  // 2. 如果是支持OCR的文件类型，进行OCR处理
  const fileExt = file.name.toLowerCase().split('.').pop()
  if (fileExt && ['pdf', 'png', 'jpg', 'jpeg'].includes(fileExt)) {
    try {
      const ocrFormData = new FormData()
      ocrFormData.append('file_path', uploadResult.file_path)

      const ocrResponse = await api.post('/ocr', ocrFormData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 120000  // OCR处理增加到2分钟超时
      })

      content = ocrResponse.data.text // 保存OCR文本用于RAG
      ocrCompleted = true // OCR处理完成

      // 3. 如果OCR成功且有内容，进行RAG文档处理
      if (content && content.trim().length > 50) {
        try {
          docId = await processDocumentForRAG(content, file.name, file.type)
          ragEnabled = true
          console.log('✅ RAG文档处理完成，doc_id:', docId)
        } catch (ragError) {
          console.warn('⚠️ RAG文档处理失败:', ragError)
          // RAG处理失败不影响文件使用
        }
      }
    } catch (ocrError) {
      console.warn('OCR处理失败:', ocrError)
      // OCR失败不影响文件上传，继续处理
      ocrCompleted = false
    }
  } else {
    // 非OCR文件类型，直接标记为完成
    ocrCompleted = true
  }

  return {
    name: file.name,
    size: file.size,
    type: file.type,
    content,
    ocrCompleted,
    processing: !ocrCompleted, // 如果OCR未完成，则仍处于处理中状态
    doc_id: docId,
    rag_enabled: ragEnabled
  }
}

// 健康检查
export async function healthCheck(): Promise<any> {
  const response = await api.get('/health')
  return response.data
}

// 获取所有RAG文档列表
export async function getAllDocuments(): Promise<any> {
  const response = await api.get('/rag/documents')
  return response.data
}

// 删除RAG文档
export async function deleteDocument(docId: string): Promise<boolean> {
  try {
    const response = await api.delete(`/rag/documents/${docId}`)
    return response.status === 200
  } catch (error) {
    console.error('删除文档失败:', error)
    return false
  }
}

// RAG文档检索
export async function searchDocuments(request: RAGSearchRequest): Promise<RAGSearchResponse> {
  const response = await api.post('/rag/search', request)
  return response.data
}

// 处理文档进行RAG索引
export async function processDocumentForRAG(
  content: string,
  filename: string,
  fileType: string
): Promise<string> {
  const formData = new FormData()
  formData.append('content', content)
  formData.append('filename', filename)
  formData.append('file_type', fileType)

  const response = await api.post('/rag/process', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 180000  // RAG处理增加到3分钟超时
  })
  return response.data.doc_id
}

// 获取文档信息
export async function getDocumentInfo(docId: string): Promise<any> {
  const response = await api.get(`/rag/documents/${docId}`)
  return response.data
}



export default api 