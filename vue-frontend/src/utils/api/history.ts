import type { 
  ChatSession, 
  ChatMessage, 
  CreateSessionDto, 
  CreateMessageDto, 
  QuerySessionsDto, 
  ChatHistoryResponse, 
  ChatStatsResponse 
} from '@/types'
import { API_CONFIG } from '../api-config'
import { api } from './client'

/**
 * 创建聊天会话
 */
export async function createChatSession(sessionData: CreateSessionDto): Promise<ChatSession> {
  return api.postWithStandardResponse<ChatSession>(
    API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSIONS,
    sessionData
  )
}

/**
 * 获取用户聊天会话列表
 */
export async function getChatSessions(queryParams?: QuerySessionsDto): Promise<ChatSession[]> {
  return api.getWithStandardResponse<ChatSession[]>(
    API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSIONS,
    queryParams
  )
}

/**
 * 获取聊天会话详情
 */
export async function getChatSessionById(sessionId: string): Promise<ChatSession> {
  return api.getWithStandardResponse<ChatSession>(
    `${API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSION_DETAIL}/${sessionId}`
  )
}

/**
 * 更新聊天会话
 */
export async function updateChatSession(
  sessionId: string, 
  updateData: Partial<CreateSessionDto>
): Promise<ChatSession> {
  return api.putWithStandardResponse<ChatSession>(
    `${API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSION_DETAIL}/${sessionId}`,
    updateData
  )
}

/**
 * 删除聊天会话
 */
export async function deleteChatSession(sessionId: string): Promise<void> {
  await api.deleteWithStandardResponse<void>(
    `${API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSION_DETAIL}/${sessionId}`
  )
}


/**
 * 获取会话消息列表
 */
export async function getChatSessionMessages(
  sessionId: string,
  page?: number,
  limit?: number
): Promise<ChatMessage[]> {
  const params: Record<string, any> = {}
  if (page !== undefined) params.page = page
  if (limit !== undefined) params.limit = limit

  return api.getWithStandardResponse<ChatMessage[]>(
    `${API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSION_MESSAGES}/${sessionId}/messages`,
    params
  )
}

/**
 * 添加消息到会话
 */
export async function addChatMessage(
  sessionId: string,
  messageData: Omit<CreateMessageDto, 'sessionId'>
): Promise<ChatMessage> {
  return api.postWithStandardResponse<ChatMessage>(
    `${API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSION_MESSAGES}/${sessionId}/messages`,
    messageData
  )
}

/**
 * 批量添加消息
 */
export async function addChatMessagesBatch(
  messages: CreateMessageDto[]
): Promise<ChatMessage[]> {
  return api.postWithStandardResponse<ChatMessage[]>(
    API_CONFIG.ENDPOINTS.CHAT_HISTORY_MESSAGES_BATCH,
    messages
  )
}

/**
 * 删除消息
 */
export async function deleteChatMessage(messageId: string): Promise<void> {
  await api.deleteWithStandardResponse<void>(
    `${API_CONFIG.ENDPOINTS.CHAT_HISTORY_MESSAGES_BATCH.replace('/batch', '')}/${messageId}`
  )
}

/**
 * 获取用户聊天统计信息
 */
export async function getChatStats(): Promise<ChatStatsResponse> {
  return api.getWithStandardResponse<ChatStatsResponse>(
    API_CONFIG.ENDPOINTS.CHAT_HISTORY_STATS
  )
}

/**
 * 检查聊天历史服务健康状态
 */
export async function checkChatHistoryHealth(): Promise<void> {
  await api.getWithStandardResponse<void>(
    API_CONFIG.ENDPOINTS.CHAT_HISTORY_HEALTH
  )
}

/**
 * 获取会话关联的文档列表
 */
export async function getSessionDocuments(sessionId: string): Promise<any[]> {
  return api.getWithStandardResponse<any[]>(
    `${API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSION_DETAIL}/${sessionId}/documents`
  )
} 