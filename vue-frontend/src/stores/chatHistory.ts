import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { 
  getChatSessions,
  createChatSession,
  getChatSessionById,
  getChatSessionMessages,
  addChatMessage,
  addChatMessagesBatch,
  updateChatSession,
  deleteChatSession,
  archiveChatSession,
  restoreChatSession,
  getChatStats
} from '@/utils/api'
import type {
  ChatSession,
  ChatMessage,
  CreateSessionDto,
  CreateMessageDto,
  QuerySessionsDto,
  ChatHistoryResponse
} from '@/types'

/**
 * 聊天历史状态管理
 */
export const useChatHistoryStore = defineStore('chatHistory', () => {
  // 状态
  const sessions = ref<ChatSession[]>([])
  const currentSession = ref<ChatSession | null>(null)
  const currentMessages = ref<ChatMessage[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const pagination = ref({
    page: 1,
    limit: 20,
    total: 0,
    totalPages: 0
  })

  // 计算属性
  const activeSessions = computed(() => 
    sessions.value.filter(session => session.status === 'active')
  )

  const archivedSessions = computed(() => 
    sessions.value.filter(session => session.status === 'archived')
  )

  const hasMoreSessions = computed(() => 
    pagination.value.page < pagination.value.totalPages
  )

  /**
   * 清除错误
   */
  const clearError = () => {
    error.value = null
  }

  /**
   * 获取用户的聊天会话列表
   */
  const fetchSessions = async (params: QuerySessionsDto = {}) => {
    try {
      loading.value = true
      clearError()

      const response = await getChatSessions(params)

      if (response.code === 200 && response.data) {
        if (params.page === 1) {
          sessions.value = response.data
        } else {
          sessions.value.push(...response.data)
        }
        
        if (response.pagination) {
          pagination.value = response.pagination
        }
      } else {
        throw new Error(response.msg || '获取会话列表失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取会话列表失败'
      console.error('获取会话列表失败:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建新的聊天会话
   */
  const createSession = async (sessionData: CreateSessionDto): Promise<ChatSession | null> => {
    try {
      loading.value = true
      clearError()

      const response = await createChatSession(sessionData)

      if (response.code === 200 && response.data) {
        const newSession = response.data
        sessions.value.unshift(newSession)
        return newSession
      } else {
        throw new Error(response.msg || '创建会话失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '创建会话失败'
      console.error('创建会话失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取会话详情
   */
  const fetchSessionDetail = async (sessionId: string) => {
    try {
      loading.value = true
      clearError()

      const response = await getChatSessionById(sessionId)

      if (response.code === 200 && response.data) {
        currentSession.value = response.data
        return response.data
      } else {
        throw new Error(response.msg || '获取会话详情失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取会话详情失败'
      console.error('获取会话详情失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取会话的消息列表
   */
  const fetchSessionMessages = async (sessionId: string, page: number = 1, limit: number = 50) => {
    try {
      loading.value = true
      clearError()

      const response = await getChatSessionMessages(sessionId, page, limit)

      if (response.code === 200 && response.data) {
        if (page === 1) {
          currentMessages.value = response.data
        } else {
          currentMessages.value.push(...response.data)
        }
        return response.data
      } else {
        throw new Error(response.msg || '获取消息列表失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取消息列表失败'
      console.error('获取消息列表失败:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * 添加消息到会话
   */
  const addMessage = async (sessionId: string, messageData: Omit<CreateMessageDto, 'sessionId'>): Promise<ChatMessage | null> => {
    try {
      const response = await addChatMessage(sessionId, messageData)

      if (response.code === 200 && response.data) {
        const newMessage = response.data
        currentMessages.value.push(newMessage)
        
        // 更新会话的最后消息时间
        const sessionIndex = sessions.value.findIndex(s => s.id === sessionId)
        if (sessionIndex !== -1) {
          sessions.value[sessionIndex].lastMessageAt = newMessage.createdAt
          sessions.value[sessionIndex].messageCount += 1
        }
        
        return newMessage
      } else {
        throw new Error(response.msg || '添加消息失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '添加消息失败'
      console.error('添加消息失败:', err)
      return null
    }
  }

  /**
   * 批量添加消息（用于保存完整对话）
   */
  const addMessagesBatch = async (messages: CreateMessageDto[]): Promise<ChatMessage[]> => {
    try {
      loading.value = true
      clearError()

      const response = await addChatMessagesBatch(messages)

      if (response.code === 200 && response.data) {
        return response.data
      } else {
        throw new Error(response.msg || '批量添加消息失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '批量添加消息失败'
      console.error('批量添加消息失败:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新会话信息
   */
  const updateSession = async (sessionId: string, updateData: Partial<CreateSessionDto>) => {
    try {
      const response = await updateChatSession(sessionId, updateData)

      if (response.code === 200 && response.data) {
        const updatedSession = response.data
        const sessionIndex = sessions.value.findIndex(s => s.id === sessionId)
        if (sessionIndex !== -1) {
          sessions.value[sessionIndex] = updatedSession
        }
        if (currentSession.value?.id === sessionId) {
          currentSession.value = updatedSession
        }
        return updatedSession
      } else {
        throw new Error(response.msg || '更新会话失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新会话失败'
      console.error('更新会话失败:', err)
      return null
    }
  }

  /**
   * 删除会话
   */
  const deleteSession = async (sessionId: string) => {
    try {
      const response = await deleteChatSession(sessionId)

      if (response.code === 200) {
        sessions.value = sessions.value.filter(s => s.id !== sessionId)
        if (currentSession.value?.id === sessionId) {
          currentSession.value = null
          currentMessages.value = []
        }
        return true
      } else {
        throw new Error(response.msg || '删除会话失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除会话失败'
      console.error('删除会话失败:', err)
      return false
    }
  }

  /**
   * 归档会话
   */
  const archiveSession = async (sessionId: string) => {
    try {
      const response = await archiveChatSession(sessionId)

      if (response.code === 200 && response.data) {
        const updatedSession = response.data
        const sessionIndex = sessions.value.findIndex(s => s.id === sessionId)
        if (sessionIndex !== -1) {
          sessions.value[sessionIndex] = updatedSession
        }
        return updatedSession
      } else {
        throw new Error(response.msg || '归档会话失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '归档会话失败'
      console.error('归档会话失败:', err)
      return null
    }
  }

  /**
   * 恢复会话
   */
  const restoreSession = async (sessionId: string) => {
    try {
      const response = await restoreChatSession(sessionId)

      if (response.code === 200 && response.data) {
        const updatedSession = response.data
        const sessionIndex = sessions.value.findIndex(s => s.id === sessionId)
        if (sessionIndex !== -1) {
          sessions.value[sessionIndex] = updatedSession
        }
        return updatedSession
      } else {
        throw new Error(response.msg || '恢复会话失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '恢复会话失败'
      console.error('恢复会话失败:', err)
      return null
    }
  }

  /**
   * 获取聊天统计信息
   */
  const fetchChatStats = async () => {
    try {
      const response = await getChatStats()

      if (response.code === 200 && response.data) {
        return response.data
      } else {
        throw new Error(response.msg || '获取统计信息失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取统计信息失败'
      console.error('获取统计信息失败:', err)
      return null
    }
  }

  /**
   * 清除当前会话和消息
   */
  const clearCurrentSession = () => {
    currentSession.value = null
    currentMessages.value = []
  }

  /**
   * 重置状态
   */
  const reset = () => {
    sessions.value = []
    currentSession.value = null
    currentMessages.value = []
    loading.value = false
    error.value = null
    pagination.value = {
      page: 1,
      limit: 20,
      total: 0,
      totalPages: 0
    }
  }

  return {
    // 状态
    sessions,
    currentSession,
    currentMessages,
    loading,
    error,
    pagination,
    
    // 计算属性
    activeSessions,
    archivedSessions,
    hasMoreSessions,
    
    // 方法
    clearError,
    fetchSessions,
    createSession,
    fetchSessionDetail,
    fetchSessionMessages,
    addMessage,
    addMessagesBatch,
    updateSession,
    deleteSession,
    archiveSession,
    restoreSession,
    fetchChatStats,
    clearCurrentSession,
    reset
  }
}) 

// 重新导出类型以保持向后兼容性
export type { ChatSession, ChatMessage, CreateSessionDto, CreateMessageDto, QuerySessionsDto } from '@/types' 