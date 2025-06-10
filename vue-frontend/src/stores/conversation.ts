import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Conversation, ConversationData, CreateConversationRequest, Message, RAGDocument } from '@/types'
import { generateId } from '@/utils/voice-utils'

export const useConversationStore = defineStore('conversation', () => {
  // 状态
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const conversationData = ref<Map<string, ConversationData>>(new Map())

  // 计算属性
  const hasConversations = computed(() => conversations.value.length > 0)
  const activeConversationId = computed(() => currentConversation.value?.id)
  const currentConversationMessages = computed(() => {
    if (!currentConversation.value) return []
    return conversationData.value.get(currentConversation.value.id)?.messages || []
  })
  const currentConversationRagDocs = computed(() => {
    if (!currentConversation.value) return []
    return conversationData.value.get(currentConversation.value.id)?.ragDocuments || []
  })

  // 生成对话标题
  function generateConversationTitle(firstMessage?: string): string {
    if (firstMessage) {
      // 取前30个字符作为标题
      return firstMessage.length > 30 
        ? firstMessage.substring(0, 30) + '...' 
        : firstMessage
    }
    
    const now = new Date()
    const timeStr = now.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
    return `新对话 ${timeStr}`
  }

  // 创建新对话
  function createConversation(request?: CreateConversationRequest): Conversation {
    const now = new Date()
    const conversation: Conversation = {
      id: generateId(),
      title: request?.title || generateConversationTitle(request?.initialMessage),
      createdAt: now,
      updatedAt: now,
      messageCount: 0,
      isActive: true
    }

    conversations.value.unshift(conversation)
    
    // 初始化对话数据
    conversationData.value.set(conversation.id, {
      conversation,
      messages: [],
      ragDocuments: []
    })

    // 设置为当前对话
    setCurrentConversation(conversation.id)

    // 保存到本地缓存
    saveToCache()

    return conversation
  }

  // 设置当前对话
  function setCurrentConversation(conversationId: string) {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (conversation) {
      // 将之前的对话设为非活跃状态
      if (currentConversation.value) {
        currentConversation.value.isActive = false
      }
      
      currentConversation.value = conversation
      conversation.isActive = true
      
      saveToCache()
    }
  }

  // 删除对话
  function deleteConversation(conversationId: string) {
    const index = conversations.value.findIndex(c => c.id === conversationId)
    if (index > -1) {
      conversations.value.splice(index, 1)
      conversationData.value.delete(conversationId)
      
      // 如果删除的是当前对话，切换到其他对话
      if (currentConversation.value?.id === conversationId) {
        if (conversations.value.length > 0) {
          setCurrentConversation(conversations.value[0].id)
        } else {
          currentConversation.value = null
        }
      }
      
      saveToCache()
    }
  }

  // 更新对话标题
  function updateConversationTitle(conversationId: string, title: string) {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (conversation) {
      conversation.title = title
      conversation.updatedAt = new Date()
      
      // 更新对话数据中的conversation引用
      const data = conversationData.value.get(conversationId)
      if (data) {
        data.conversation = conversation
      }
      
      saveToCache()
    }
  }

  // 更新对话的聊天历史会话ID
  function updateConversationHistorySession(conversationId: string, historySessionId: string) {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (conversation) {
      conversation.historySessionId = historySessionId
      conversation.updatedAt = new Date()
      
      // 更新对话数据中的conversation引用
      const data = conversationData.value.get(conversationId)
      if (data) {
        data.conversation = conversation
      }
      
      saveToCache()
      console.log(`✅ 对话 ${conversationId} 已关联聊天历史会话 ${historySessionId}`)
    }
  }

  // 添加消息到当前对话
  function addMessageToConversation(conversationId: string, message: Message) {
    const data = conversationData.value.get(conversationId)
    if (data) {
      data.messages.push(message)
      data.conversation.messageCount = data.messages.length
      data.conversation.updatedAt = new Date()
      data.conversation.lastMessage = message.isUser 
        ? message.content 
        : message.content.substring(0, 50) + (message.content.length > 50 ? '...' : '')
      
      saveToCache()
    }
  }

  // 获取对话消息
  function getConversationMessages(conversationId: string): Message[] {
    return conversationData.value.get(conversationId)?.messages || []
  }

  // 清空对话消息
  function clearConversationMessages(conversationId: string) {
    const data = conversationData.value.get(conversationId)
    if (data) {
      data.messages = []
      data.conversation.messageCount = 0
      data.conversation.lastMessage = undefined
      data.conversation.updatedAt = new Date()
      
      saveToCache()
    }
  }

  // 添加RAG文档到对话
  function addRagDocumentToConversation(conversationId: string, document: RAGDocument) {
    const data = conversationData.value.get(conversationId)
    if (data) {
      // 检查文档是否已存在
      const exists = data.ragDocuments.find(doc => doc.doc_id === document.doc_id)
      if (!exists) {
        data.ragDocuments.push(document)
        saveToCache()
      }
    }
  }

  // 从对话中移除RAG文档
  function removeRagDocumentFromConversation(conversationId: string, docId: string) {
    const data = conversationData.value.get(conversationId)
    if (data) {
      const index = data.ragDocuments.findIndex(doc => doc.doc_id === docId)
      if (index > -1) {
        data.ragDocuments.splice(index, 1)
        saveToCache()
      }
    }
  }

  // 保存到本地缓存
  function saveToCache() {
    try {
      const cacheData = {
        conversations: conversations.value,
        currentConversationId: currentConversation.value?.id,
        conversationData: Array.from(conversationData.value.entries()).map(([id, data]) => ({
          id,
          data: {
            ...data,
            // 转换Date对象为字符串以便JSON序列化
            conversation: {
              ...data.conversation,
              createdAt: data.conversation.createdAt.toISOString(),
              updatedAt: data.conversation.updatedAt.toISOString()
            },
            messages: data.messages.map(msg => ({
              ...msg,
              timestamp: msg.timestamp.toISOString()
            }))
          }
        }))
      }
      
      localStorage.setItem('conversations', JSON.stringify(cacheData))
    } catch (error) {
      console.error('保存对话到缓存失败:', error)
    }
  }

  // 从本地缓存加载
  function loadFromCache() {
    try {
      const cached = localStorage.getItem('conversations')
      if (cached) {
        const cacheData = JSON.parse(cached)
        
        // 恢复对话列表
        conversations.value = cacheData.conversations.map((conv: any) => ({
          ...conv,
          createdAt: new Date(conv.createdAt),
          updatedAt: new Date(conv.updatedAt),
          isActive: false
        }))
        
        // 恢复对话数据
        conversationData.value.clear()
        if (cacheData.conversationData) {
          cacheData.conversationData.forEach(({ id, data }: any) => {
            conversationData.value.set(id, {
              conversation: {
                ...data.conversation,
                createdAt: new Date(data.conversation.createdAt),
                updatedAt: new Date(data.conversation.updatedAt),
                isActive: false
              },
              messages: data.messages.map((msg: any) => ({
                ...msg,
                timestamp: new Date(msg.timestamp)
              })),
              ragDocuments: data.ragDocuments || []
            })
          })
        }
        
        // 恢复当前对话
        if (cacheData.currentConversationId) {
          setCurrentConversation(cacheData.currentConversationId)
        }
        
        console.log(`✅ 从缓存加载了 ${conversations.value.length} 个对话`)
      }
    } catch (error) {
      console.error('从缓存加载对话失败:', error)
    }
  }

  // 清空所有对话
  function clearAllConversations() {
    conversations.value = []
    conversationData.value.clear()
    currentConversation.value = null
    localStorage.removeItem('conversations')
  }

  // 从后端同步对话列表
  async function syncFromBackend() {
    try {
      const { useChatStore } = await import('@/stores/chat')
      const { useChatHistoryStore } = await import('@/stores/chatHistory')
      
      const chatStore = useChatStore()
      const chatHistoryStore = useChatHistoryStore()
      
      // 检查是否启用了历史同步
      if (!chatStore.isHistorySyncEnabled) {
        console.log('📝 历史同步已禁用，跳过后端同步')
        return false
      }
      
      console.log('🔄 正在从后端同步对话列表...')
      
      // 获取用户的聊天会话列表
      await chatHistoryStore.fetchSessions({ page: 1, limit: 100 })
      
      const remoteSessions = chatHistoryStore.sessions
      console.log(`📥 从后端获取到 ${remoteSessions.length} 个会话`)
      
      // 将后端会话转换为本地对话格式
      for (const session of remoteSessions) {
        // 检查本地是否已存在相同的对话
        const existingConv = conversations.value.find(c => c.historySessionId === session.id)
        
        if (!existingConv) {
          // 创建新的本地对话
          const newConversation: Conversation = {
            id: generateId(),
            title: session.title,
            createdAt: new Date(session.createdAt),
            updatedAt: new Date(session.updatedAt),
            messageCount: session.messageCount || 0,
            isActive: false,
            historySessionId: session.id,
            lastMessage: session.description
          }
          
          conversations.value.push(newConversation)
          
          // 初始化对话数据
          conversationData.value.set(newConversation.id, {
            conversation: newConversation,
            messages: [],
            ragDocuments: []
          })
          
          console.log(`✅ 同步会话: ${session.title} (${session.id})`)
        } else {
          // 更新现有对话的信息
          existingConv.title = session.title
          existingConv.updatedAt = new Date(session.updatedAt)
          existingConv.messageCount = session.messageCount || 0
          
          // 更新对话数据中的conversation引用
          const data = conversationData.value.get(existingConv.id)
          if (data) {
            data.conversation = existingConv
          }
        }
      }
      
      // 按更新时间排序
      conversations.value.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime())
      
      console.log(`✅ 对话同步完成，总计 ${conversations.value.length} 个对话`)
      return true
      
    } catch (error) {
      console.error('❌ 从后端同步对话失败:', error)
      return false
    }
  }

  // 初始化：先从缓存加载数据，然后从后端同步，最后创建默认对话
  async function initialize() {
    // 1. 从本地缓存加载
    loadFromCache()
    console.log(`📁 从缓存加载了 ${conversations.value.length} 个对话`)
    
    // 2. 尝试从后端同步
    const syncSuccess = await syncFromBackend()
    
    // 3. 如果没有对话，创建默认对话
    if (conversations.value.length === 0) {
      createConversation({ title: '默认对话' })
      console.log('📝 创建了默认对话')
    } else if (syncSuccess) {
      // 同步成功后保存到缓存
      saveToCache()
    }
    
    // 4. 设置当前对话（如果没有活跃对话）
    if (!currentConversation.value && conversations.value.length > 0) {
      setCurrentConversation(conversations.value[0].id)
    }
  }

  return {
    // 状态
    conversations,
    currentConversation,
    conversationData,
    
    // 计算属性
    hasConversations,
    activeConversationId,
    currentConversationMessages,
    currentConversationRagDocs,
    
    // 方法
    createConversation,
    setCurrentConversation,
    deleteConversation,
    updateConversationTitle,
    updateConversationHistorySession,
    addMessageToConversation,
    getConversationMessages,
    clearConversationMessages,
    addRagDocumentToConversation,
    removeRagDocumentFromConversation,
    saveToCache,
    loadFromCache,
    clearAllConversations,
    syncFromBackend,
    initialize
  }
}) 