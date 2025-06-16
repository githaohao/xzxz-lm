import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  Conversation, 
  ConversationData, 
  CreateConversationRequest, 
  Message, 
  RAGDocument,
  ChatSession,
  ChatMessage,
  CreateSessionDto,
  CreateMessageDto,
} from '@/types'
import { generateId } from '@/utils/voice-utils'
import { 
  getChatSessions,
  createChatSession,
  getChatSessionMessages,
  addChatMessage,
  addChatMessagesBatch,
  deleteChatSession,
  getSessionDocuments
} from '@/utils/api'

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
  async function createConversation(request?: CreateConversationRequest): Promise<Conversation> {
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
    await setCurrentConversation(conversation.id)

    // 保存到本地缓存
    saveToCache()

    // 自动创建云端会话（如果启用了历史同步）
    await createRemoteSession(conversation)

    return conversation
  }

  // 创建远程会话
  async function createRemoteSession(conversation: Conversation) {
    try {
      // 动态导入避免循环依赖
      const { useChatStore } = await import('@/stores/chat')
      const chatStore = useChatStore()

      // 检查是否启用了历史同步
      if (!chatStore.isHistorySyncEnabled) {
        return
      }

      // 创建远程会话
      const sessionData: CreateSessionDto = {
        title: conversation.title,
        tags: ['chat', 'ai', 'conversation']
      }

      const remoteSession = await createChatSession(sessionData)
      
      // 将远程会话ID关联到本地对话
      updateConversationHistorySession(conversation.id, remoteSession.id)

    } catch (error) {
      console.error('❌ 创建远程会话时出错:', error)
      console.warn('⚠️ 远程会话创建失败，仅保留本地对话')
      // 即使远程创建失败，也不影响本地对话的使用
    }
  }

  // 创建会话消息DTO
  function createMessageDto(
    message: Message, 
    sessionId: string, 
    role: 'user' | 'assistant' | 'system' = 'user'
  ): CreateMessageDto {
    return {
      sessionId,
      role,
      content: message.content,
      messageType: message.fileInfo ? 'multimodal' : 'text',
      metadata: message.fileInfo ? {
        fileName: message.fileInfo.name,
        fileSize: message.fileInfo.size,
        fileType: message.fileInfo.type,
        ragEnabled: message.fileInfo.rag_enabled,
        docId: message.fileInfo.doc_id,
        ocrCompleted: message.fileInfo.ocrCompleted,
        attachments: message.fileInfo.attachments || []
      } : undefined
    }
  }

  // 保存消息到远程会话
  async function saveMessageToRemote(
    message: Message, 
    sessionId: string, 
    role: 'user' | 'assistant' | 'system' = 'user'
  ): Promise<boolean> {
    try {
      const messageDto = createMessageDto(message, sessionId, role)
      await addChatMessage(sessionId, messageDto)
      return true
    } catch (error) {
      console.error('❌ 保存消息到远程会话失败:', error)
      return false
    }
  }

  // 批量保存消息到远程会话
  async function saveMessagesBatchToRemote(
    messages: { message: Message, role: 'user' | 'assistant' | 'system' }[],
    sessionId: string
  ): Promise<boolean> {
    try {
      const messageDtos = messages.map(({ message, role }) => 
        createMessageDto(message, sessionId, role)
      )
      
      await addChatMessagesBatch(messageDtos)
      console.log(`✅ 批量保存${messages.length}条消息到远程会话成功`)
      return true
    } catch (error) {
      console.error('❌ 批量保存消息到远程会话失败:', error)
      return false
    }
  }



  // 设置当前对话
  async function setCurrentConversation(conversationId: string) {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (conversation) {
      // 将之前的对话设为非活跃状态
      if (currentConversation.value) {
        currentConversation.value.isActive = false
      }
      
      currentConversation.value = conversation
      conversation.isActive = true
      
      // 如果对话有关联的云端会话，且本地消息为空，则从云端加载消息
      await loadMessagesFromRemote(conversationId)
      
      saveToCache()
    }
  }

  // 从云端加载消息到本地对话
  async function loadMessagesFromRemote(conversationId: string) {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (!conversation || !conversation.historySessionId) {
      return // 没有关联的云端会话，跳过
    }

    const data = conversationData.value.get(conversationId)
    if (!data || data.messages.length > 0) {
      return // 已有本地消息，跳过加载
    }

    try {
      console.log('📜 从云端加载会话消息和文档:', conversation.historySessionId)
      
      // 加载消息
      const messages = await getChatSessionMessages(conversation.historySessionId)
      if (messages && messages.length > 0) {
        // 转换并添加消息
        for (const chatMsg of messages) {
          const message = convertChatMessageToMessage(chatMsg)
          data.messages.push(message)
        }
        
        // 更新会话统计
        conversation.messageCount = data.messages.length
        conversation.updatedAt = new Date()
        
        console.log(`✅ 成功加载${messages.length}条历史消息`)
      }
      
      // 加载会话关联的文档
      try {
        const sessionDocs = await getSessionDocuments(conversation.historySessionId)
        if (sessionDocs && sessionDocs.length > 0) {
          // 添加文档到对话
          data.ragDocuments = sessionDocs
          console.log(`📚 成功加载${sessionDocs.length}个关联文档`)
        }
      } catch (docError) {
        console.warn('⚠️ 加载会话文档失败:', docError)
        // 文档加载失败不影响消息加载
      }
      
      saveToCache()
      
    } catch (error) {
      console.error('❌ 加载云端数据失败:', error)
    }
  }

  // 将ChatMessage转换为Message格式
  function convertChatMessageToMessage(chatMsg: ChatMessage): Message {
    const message: Message = {
      id: chatMsg.id,
      content: chatMsg.content,
      isUser: chatMsg.role === 'user',
      timestamp: new Date(chatMsg.created_at),
      isStreaming: false
    }

    // 处理多模态消息的文件信息
    if (chatMsg.message_type === 'multimodal' && chatMsg.metadata) {
      message.fileInfo = {
        name: chatMsg.metadata.fileName || '',
        size: chatMsg.metadata.fileSize || 0,
        type: chatMsg.metadata.fileType || '',
        rag_enabled: chatMsg.metadata.ragEnabled || false,
        doc_id: chatMsg.metadata.docId,
        ocrCompleted: chatMsg.metadata.ocrCompleted || false,
        attachments: chatMsg.metadata.attachments || []
      }
    }

    return message
  }

  // 删除对话
  async function deleteConversation(conversationId: string) {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (!conversation) {
      console.warn('⚠️ 要删除的对话不存在:', conversationId)
      return
    }

    try {
      // 如果对话有关联的远程会话，先删除远程会话
      if (conversation.historySessionId) {
        console.log('🗑️ 正在删除远程会话...', conversation.historySessionId)
        
        try {
          await deleteChatSession(conversation.historySessionId)
          console.log('✅ 远程会话删除成功')
        } catch (remoteError) {
          // 远程删除失败不阻止本地删除（可能会话已经被删除或网络问题）
          console.warn('⚠️ 删除远程会话失败，继续删除本地数据:', remoteError)
        }
      }

      // 删除本地数据
      const index = conversations.value.findIndex(c => c.id === conversationId)
      if (index > -1) {
        conversations.value.splice(index, 1)
        conversationData.value.delete(conversationId)
        
        // 如果删除的是当前对话，切换到其他对话
        if (currentConversation.value?.id === conversationId) {
          if (conversations.value.length > 0) {
            await setCurrentConversation(conversations.value[0].id)
          } else {
            currentConversation.value = null
          }
        }
        
        saveToCache()
        console.log('✅ 本地对话删除成功:', conversation.title)
      }

    } catch (error) {
      console.error('❌ 删除对话时发生错误:', error)
      throw error // 抛出错误以便UI层处理
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
  async function loadFromCache() {
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
          await setCurrentConversation(cacheData.currentConversationId)
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
      const chatStore = useChatStore()
      
      // 检查是否启用了历史同步
      if (!chatStore.isHistorySyncEnabled) {
        console.log('📝 历史同步已禁用，跳过后端同步')
        return false
      }
      
      console.log('🔄 正在从后端同步对话列表...')
      
      // 获取用户的聊天会话列表
      const remoteSessions = await getChatSessions({ page: 1, limit: 100 })
      console.log(`📥 从后端获取到 ${remoteSessions.length} 个会话`)
      
      // 记录同步统计
      let addedCount = 0
      let updatedCount = 0
      let removedCount = 0
      
      // 创建远程会话ID集合，用于后续清理
      const remoteSessionIds = new Set(remoteSessions.map((session: ChatSession) => session.id))
      // 处理远程会话：新增或更新本地对话
      for (const session of remoteSessions) {
        // 检查本地是否已存在相同的对话
        const existingConv = conversations.value.find(c => c.historySessionId === session.id)
        if (!existingConv) {
          // 创建新的本地对话
          const newConversation: Conversation = {
            id: generateId(),
            title: session.title,
            createdAt: new Date(session.created_at),
            updatedAt: new Date(session.updated_at),
            messageCount: session.message_count || 0,
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
          addedCount++
          console.log(`➕ 新增会话: ${session.title} (${session.id})`)
        } else {
          // 检查是否需要更新现有对话
          const remoteUpdatedTime = new Date(session.updated_at).getTime()
          const localUpdatedTime = existingConv.updatedAt.getTime()
          
          if (remoteUpdatedTime > localUpdatedTime || 
              existingConv.title !== session.title ||
              existingConv.messageCount !== (session.message_count || 0)) {
            
            // 更新现有对话的信息
            existingConv.title = session.title
            existingConv.updatedAt = new Date(session.updated_at)
            existingConv.messageCount = session.message_count || 0
            existingConv.lastMessage = session.description
            
            // 更新对话数据中的conversation引用
            const data = conversationData.value.get(existingConv.id)
            if (data) {
              data.conversation = existingConv
            }
            
            updatedCount++
            console.log(`🔄 更新会话: ${session.title} (${session.id})`)
          }
        }
      }
      
      // 处理本地对话：移除云端不存在的所有会话（包括纯本地对话）
      // 选项B：彻底清理所有云端没有的对话
      const conversationsToRemove = conversations.value.filter(conv => {
        // 如果对话有historySessionId，检查云端是否存在
        if (conv.historySessionId) {
          return !remoteSessionIds.has(conv.historySessionId)
        }
        // 如果是纯本地对话（没有historySessionId），也删除
        return true
      })
      
      // 统计要删除的对话类型
      const syncedButMissing = conversationsToRemove.filter(conv => conv.historySessionId)
      const pureLocalConversations = conversationsToRemove.filter(conv => !conv.historySessionId)
      
      console.log(`🧹 将清除所有云端不存在的对话:`)
      console.log(`   - 云端已删除的对话: ${syncedButMissing.length} 个`)
      console.log(`   - 纯本地对话: ${pureLocalConversations.length} 个`)
      
      for (const conv of conversationsToRemove) {
        const reason = conv.historySessionId 
          ? `云端已删除 (${conv.historySessionId})` 
          : '纯本地对话'
        console.log(`🗑️ 移除本地会话 (${reason}): ${conv.title}`)
        
        // 从对话列表中移除
        const index = conversations.value.findIndex(c => c.id === conv.id)
        if (index > -1) {
          conversations.value.splice(index, 1)
        }
        
        // 清理对话数据
        conversationData.value.delete(conv.id)
        
        // 如果删除的是当前对话，需要切换到其他对话
        if (currentConversation.value?.id === conv.id) {
          if (conversations.value.length > 0) {
            await setCurrentConversation(conversations.value[0].id)
          } else {
            currentConversation.value = null
          }
        }
        
        removedCount++
      }
      
      // 按更新时间排序
      conversations.value.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime())
      
      // 立即保存到缓存
      saveToCache()
      
      // 输出同步统计
      const syncedConversations = conversations.value.filter(conv => conv.historySessionId)
      
      console.log(`✅ 对话同步完成 (彻底清理模式)`)
      console.log(`   📊 云端同步: 新增 ${addedCount} | 更新 ${updatedCount} | 清除 ${removedCount}`)
      console.log(`   📁 对话统计: 云端同步 ${syncedConversations.length} 个 | 总计 ${conversations.value.length} 个`)
      console.log(`   🧹 清理详情: 云端已删除 ${syncedButMissing.length} 个 | 纯本地对话 ${pureLocalConversations.length} 个`)
      
      return true
      
    } catch (error) {
      console.error('❌ 从后端同步对话失败:', error)
      return false
    }
  }

  // 强制同步：用户主动触发的完整同步
  async function forceSync(options: { clearLocalOnly?: boolean } = {}) {
    try {
      console.log('🔄 用户触发强制同步...')
      
      // 如果选择清理纯本地对话，先清理
      if (options.clearLocalOnly) {
        const clearResult = await clearLocalOnlyConversations()
        console.log(`🧹 强制同步：已清理 ${clearResult.removedCount} 个纯本地对话`)
      }
      
      const success = await syncFromBackend()
      
      if (success) {
        console.log('✅ 强制同步完成')
        return { success: true, message: '同步成功' }
      } else {
        console.log('❌ 强制同步失败')
        return { success: false, message: '同步失败，请检查网络连接' }
      }
    } catch (error) {
      console.error('❌ 强制同步错误:', error)
      return { 
        success: false, 
        message: error instanceof Error ? error.message : '同步过程中发生未知错误' 
      }
    }
  }

  // 初始化：先从缓存加载数据，然后从后端同步，最后创建
  async function initialize() {
    // 1. 从本地缓存加载
    await loadFromCache()
    console.log(`📁 从缓存加载了 ${conversations.value.length} 个对话`)
    
    // 2. 尝试从后端同步
    const syncSuccess = await syncFromBackend()
    
    // 3. 设置当前对话（如果没有活跃对话）
    if (!currentConversation.value && conversations.value.length > 0) {
      await setCurrentConversation(conversations.value[0].id)
    }
  }

  // 清理纯本地对话（没有同步到云端的对话）
  async function clearLocalOnlyConversations() {
    const localOnlyConversations = conversations.value.filter(conv => !conv.historySessionId)
    
    if (localOnlyConversations.length === 0) {
      console.log('📝 没有需要清理的纯本地对话')
      return { success: true, removedCount: 0 }
    }
    
    let removedCount = 0
    
    for (const conv of localOnlyConversations) {
      console.log(`🗑️ 清理纯本地对话: ${conv.title}`)
      
      // 从对话列表中移除
      const index = conversations.value.findIndex(c => c.id === conv.id)
      if (index > -1) {
        conversations.value.splice(index, 1)
      }
      
      // 清理对话数据
      conversationData.value.delete(conv.id)
      
      // 如果删除的是当前对话，需要切换到其他对话
      if (currentConversation.value?.id === conv.id) {
        if (conversations.value.length > 0) {
          await setCurrentConversation(conversations.value[0].id)
        } else {
          currentConversation.value = null
        }
      }
      
      removedCount++
    }
    
    // 保存到缓存
    saveToCache()
    
    console.log(`✅ 已清理 ${removedCount} 个纯本地对话`)
    return { success: true, removedCount }
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
    clearLocalOnlyConversations,
    syncFromBackend,
    initialize,
    forceSync,
    
    // 远程会话管理方法
    createRemoteSession,
    saveMessageToRemote,
    saveMessagesBatchToRemote,
    createMessageDto,
    
    // 消息加载方法
    loadMessagesFromRemote,
    convertChatMessageToMessage
  }
})