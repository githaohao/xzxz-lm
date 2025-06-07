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
export async function createChatSession(sessionData: CreateSessionDto): Promise<ChatHistoryResponse<ChatSession>> {
  return api.post<ChatHistoryResponse<ChatSession>>(
    API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSIONS,
    sessionData
  )
}

/**
 * 获取用户聊天会话列表
 */
export async function getChatSessions(queryParams?: QuerySessionsDto): Promise<ChatHistoryResponse<ChatSession[]>> {
  return api.get<ChatHistoryResponse<ChatSession[]>>(
    API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSIONS,
    queryParams
  )
}

/**
 * 获取聊天会话详情
 */
export async function getChatSessionById(sessionId: string): Promise<ChatHistoryResponse<ChatSession>> {
  return api.get<ChatHistoryResponse<ChatSession>>(
    `${API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSION_DETAIL}/${sessionId}`
  )
}

/**
 * 更新聊天会话
 */
export async function updateChatSession(
  sessionId: string, 
  updateData: Partial<CreateSessionDto>
): Promise<ChatHistoryResponse<ChatSession>> {
  return api.put<ChatHistoryResponse<ChatSession>>(
    `${API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSION_DETAIL}/${sessionId}`,
    updateData
  )
}

/**
 * 删除聊天会话
 */
export async function deleteChatSession(sessionId: string): Promise<ChatHistoryResponse> {
  return api.delete<ChatHistoryResponse>(
    `${API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSION_DETAIL}/${sessionId}`
  )
}

/**
 * 归档聊天会话
 */
export async function archiveChatSession(sessionId: string): Promise<ChatHistoryResponse<ChatSession>> {
  return api.put<ChatHistoryResponse<ChatSession>>(
    `${API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSION_DETAIL}/${sessionId}/archive`,
    {}
  )
}

/**
 * 恢复聊天会话
 */
export async function restoreChatSession(sessionId: string): Promise<ChatHistoryResponse<ChatSession>> {
  return api.put<ChatHistoryResponse<ChatSession>>(
    `${API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSION_DETAIL}/${sessionId}/restore`,
    {}
  )
}

/**
 * 获取会话消息列表
 */
export async function getChatSessionMessages(
  sessionId: string,
  page?: number,
  limit?: number
): Promise<ChatHistoryResponse<ChatMessage[]>> {
  const params: Record<string, any> = {}
  if (page !== undefined) params.page = page
  if (limit !== undefined) params.limit = limit

  return api.get<ChatHistoryResponse<ChatMessage[]>>(
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
): Promise<ChatHistoryResponse<ChatMessage>> {
  return api.post<ChatHistoryResponse<ChatMessage>>(
    `${API_CONFIG.ENDPOINTS.CHAT_HISTORY_SESSION_MESSAGES}/${sessionId}/messages`,
    messageData
  )
}

/**
 * 批量添加消息
 */
export async function addChatMessagesBatch(
  messages: CreateMessageDto[]
): Promise<ChatHistoryResponse<ChatMessage[]>> {
  return api.post<ChatHistoryResponse<ChatMessage[]>>(
    API_CONFIG.ENDPOINTS.CHAT_HISTORY_MESSAGES_BATCH,
    messages
  )
}

/**
 * 删除消息
 */
export async function deleteChatMessage(messageId: string): Promise<ChatHistoryResponse> {
  return api.delete<ChatHistoryResponse>(
    `${API_CONFIG.ENDPOINTS.CHAT_HISTORY_MESSAGES_BATCH.replace('/batch', '')}/${messageId}`
  )
}

/**
 * 获取用户聊天统计信息
 */
export async function getChatStats(): Promise<ChatHistoryResponse<ChatStatsResponse>> {
  return api.get<ChatHistoryResponse<ChatStatsResponse>>(
    API_CONFIG.ENDPOINTS.CHAT_HISTORY_STATS
  )
}

/**
 * 检查聊天历史服务健康状态
 */
export async function checkChatHistoryHealth(): Promise<ChatHistoryResponse> {
  return api.get<ChatHistoryResponse>(
    API_CONFIG.ENDPOINTS.CHAT_HISTORY_HEALTH
  )
} 