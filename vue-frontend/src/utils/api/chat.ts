import type { Message, ProcessedFile } from '@/types'
import { API_CONFIG } from '../api-config'
import { api } from './client'
import { convertToBackendMessages } from './utils'

/**
 * 文本聊天流式API
 */
export async function sendTextMessage(
  message: string,
  history: Message[],
  temperature: number = 0.7,
  maxTokens: number = 2048,
  signal?: AbortSignal,
  sessionId?: string
): Promise<Response> {
  return api.stream(API_CONFIG.ENDPOINTS.CHAT_STREAM, {
    message,
    history: convertToBackendMessages(history),
    temperature,
    max_tokens: maxTokens,
    session_id: sessionId
  }, signal)
}

/**
 * 多模态聊天流式API
 */
export async function sendMultimodalMessage(
  message: string,
  history: Message[],
  fileData: ProcessedFile,
  temperature: number = 0.7,
  maxTokens: number = 2048,
  signal?: AbortSignal,
  sessionId?: string
): Promise<Response> {
  return api.stream(API_CONFIG.ENDPOINTS.MULTIMODAL_STREAM, {
    message,
    history: convertToBackendMessages(history),
    file_data: {
      name: fileData.name,
      type: fileData.type,
      size: fileData.size,
      content: fileData.content || null,
      ocr_completed: fileData.ocrCompleted || false,
      doc_id: fileData.doc_id || null,
      knowledge_base_id: fileData.knowledge_base_id || null,
      rag_enabled: fileData.rag_enabled || false
    },
    temperature,
    max_tokens: maxTokens,
    session_id: sessionId
  }, signal)
}

/**
 * 健康检查
 */
export async function healthCheck(): Promise<any> {
  return api.get(API_CONFIG.ENDPOINTS.HEALTH)
} 