import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Message, ProcessedFile, StreamEvent, RAGSearchRequest } from '@/types'
import { generateId } from '@/utils/voice-utils'
import { sendTextMessage, sendMultimodalMessage, searchDocuments } from '@/utils/api'
import { useConversationStore } from './conversation'

export const useChatStore = defineStore('chat', () => {
  const conversationStore = useConversationStore()

  // 状态
  const isLoading = ref(false)
  const processingStatus = ref('')
  const currentStreamingMessage = ref<Message | null>(null)
  const processedFile = ref<ProcessedFile | null>(null)
  const abortController = ref<AbortController | null>(null)
  const isHistorySyncEnabled = ref(true) // 控制是否同步到聊天历史服务

  // 计算属性 - 使用对话store中的消息
  const messages = computed(() => conversationStore.currentConversationMessages)
  const hasMessages = computed(() => messages.value.length > 0)
  const canSend = computed(() => !isLoading.value && conversationStore.currentConversation)

  // 添加消息到本地对话
  function addMessage(message: Omit<Message, 'id' | 'timestamp'>) {
    const newMessage: Message = {
      ...message,
      id: generateId(),
      timestamp: new Date()
    }
    
    // 添加到当前对话
    if (conversationStore.currentConversation) {
      conversationStore.addMessageToConversation(conversationStore.currentConversation.id, newMessage)
    }
    
    return newMessage
  }

  // 保存消息到聊天历史服务
  async function saveMessageToHistory(
    message: Message, 
    sessionId: string, 
    role: 'user' | 'assistant' | 'system' = 'user'
  ): Promise<boolean> {
    if (!isHistorySyncEnabled.value) {
      console.log('🔄 聊天历史同步已禁用，跳过保存')
      return true
    }

    return conversationStore.saveMessageToRemote(message, sessionId, role)
  }

  // 批量保存消息到聊天历史服务
  async function saveMessagesBatchToHistory(
    messages: { message: Message, role: 'user' | 'assistant' | 'system' }[],
    sessionId: string
  ): Promise<boolean> {
    if (!isHistorySyncEnabled.value) {
      console.log('🔄 聊天历史同步已禁用，跳过批量保存')
      return true
    }

    return conversationStore.saveMessagesBatchToRemote(messages, sessionId)
  }

  // 确保有活跃的聊天会话
  async function ensureActiveSession(): Promise<string | null> {
    // 如果当前对话有对应的历史会话，直接返回
    if (conversationStore.currentConversation?.historySessionId) {
      console.log('📝 使用现有聊天历史会话:', conversationStore.currentConversation.historySessionId)
      return conversationStore.currentConversation.historySessionId
    }

    // 如果禁用了历史同步，不创建会话
    if (!isHistorySyncEnabled.value) {
      console.log('🔄 聊天历史同步已禁用，跳过会话创建')
      return null
    }

    // 创建新的聊天历史会话（通过conversation store处理）
    try {
      const currentConv = conversationStore.currentConversation
      if (currentConv) {
        console.log('🆕 为当前对话创建远程会话...')
        await conversationStore.createRemoteSession(currentConv)
        
        // 如果创建成功，返回会话ID
        if (currentConv.historySessionId) {
          // 如果当前对话已有消息，批量保存到历史记录
          if (messages.value.length > 0) {
            console.log(`🔄 当前对话已有${messages.value.length}条消息，准备同步到历史服务...`)
            await syncExistingMessagesToHistory(currentConv.historySessionId)
          }
          return currentConv.historySessionId
        }
      }
    } catch (error) {
      console.error('❌ 创建聊天历史会话失败:', error)
    }

    return null
  }

  // 同步现有消息到聊天历史服务
  async function syncExistingMessagesToHistory(sessionId: string) {
    if (messages.value.length === 0) return

    try {
      const messagesToSync = messages.value.map(msg => ({
        message: msg,
        role: (msg.isUser ? 'user' : 'assistant') as 'user' | 'assistant'
      }))

      const success = await saveMessagesBatchToHistory(messagesToSync, sessionId)
      if (success) {
        console.log(`✅ 成功同步${messages.value.length}条现有消息到聊天历史服务`)
      }
    } catch (error) {
      console.error('❌ 同步现有消息到聊天历史服务失败:', error)
    }
  }

  // 更新会话标题（如果需要）
  async function updateSessionTitle(sessionId: string, newTitle: string) {
    if (!isHistorySyncEnabled.value) return

    try {
      const success = await conversationStore.updateRemoteSession(sessionId, { title: newTitle })
      if (success) {
        console.log('✅ 会话标题已更新:', newTitle)
      }
    } catch (error) {
      console.error('❌ 更新会话标题失败:', error)
    }
  }

  // 更新流式消息
  function updateStreamingMessage(content: string, isComplete: boolean = false) {
    if (currentStreamingMessage.value) {
      currentStreamingMessage.value.content = content
      currentStreamingMessage.value.isStreaming = !isComplete
      
      if (isComplete) {
        // 将完成的流式消息添加到消息列表
        const completedMessage = { ...currentStreamingMessage.value }
        addMessage({
          content: completedMessage.content,
          isUser: false,
          fileInfo: completedMessage.fileInfo
        })
        
        // 不再需要手动保存AI回复，后端stream接口会自动处理
        
        currentStreamingMessage.value = null
      }
    }
  }

  // 处理流式响应
  async function handleStreamResponse(response: Response) {
    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('无法读取响应流')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    // 创建流式消息
    currentStreamingMessage.value = {
      id: generateId(),
      content: '',
      isUser: false,
      timestamp: new Date(),
      isStreaming: true
    }

    try {
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            
            if (data === '[DONE]') {
              updateStreamingMessage(currentStreamingMessage.value?.content || '', true)
              processingStatus.value = ''
              return
            }

            try {
              const event: StreamEvent = JSON.parse(data)
              
              switch (event.type) {
                case 'file_processing':
                  processingStatus.value = `📄 ${event.message}`
                  break
                  
                case 'ocr_processing':
                  processingStatus.value = `🔍 ${event.message}`
                  break
                  
                case 'thinking':
                  processingStatus.value = '🤔 AI正在思考...'
                  break
                  
                case 'content':
                  if (event.content) {
                    const newContent = (currentStreamingMessage.value?.content || '') + event.content
                    updateStreamingMessage(newContent)
                  }
                  break
                  
                case 'complete':
                  updateStreamingMessage(currentStreamingMessage.value?.content || '', true)
                  processingStatus.value = ''
                  return
                  
                case 'error':
                  updateStreamingMessage(`❌ ${event.message}`, true)
                  processingStatus.value = ''
                  console.error('流式响应错误:', event.message)
                  return
              }
            } catch (e) {
              console.warn('解析流式数据失败:', data, e)
            }
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('流式响应被用户中断')
        processingStatus.value = '已取消'
      } else {
        console.error('处理流式响应时出错:', error)
        updateStreamingMessage('❌ 处理响应时出错', true)
      }
      processingStatus.value = ''
    } finally {
      if (!reader.closed) {
        await reader.cancel()
      }
    }
  }

  // 发送消息
  async function sendMessage(content: string, file?: ProcessedFile) {
    if (!canSend.value || (!content.trim() && !file)) {
      console.warn('发送条件不满足')
      return
    }

    isLoading.value = true
    processingStatus.value = '准备发送...'
    
    try {
      // 确保有活跃的会话
      const sessionId = await ensureActiveSession()
      
      // 添加用户消息到本地
      const userMessage = addMessage({
        content: content.trim() || '文件上传',
        isUser: true,
        fileInfo: file
      })

      // 创建中断控制器
      abortController.value = new AbortController()
      
      let response: Response
      
      if (file && file.ocrCompleted) {
        // 多模态消息
        processingStatus.value = '🔄 发送多模态消息...'
        console.log('📤 发送多模态消息，文件:', file.name)
        
        response = await sendMultimodalMessage(
          content.trim() || '请分析这个文件',
          messages.value.slice(0, -1), // 排除刚添加的用户消息
          file,
          0.7,
          2048,
          abortController.value.signal,
          sessionId || undefined  // 传入sessionId，让后端自动保存
        )
      } else {
        // 纯文本消息
        processingStatus.value = '🔄 发送文本消息...'
        console.log('📤 发送文本消息:', content.substring(0, 50))
        
        response = await sendTextMessage(
          content,
          messages.value.slice(0, -1), // 排除刚添加的用户消息
          0.7,
          2048,
          abortController.value.signal,
          sessionId || undefined  // 传入sessionId，让后端自动保存
        )
      }

      if (!response.ok) {
        throw new Error(`HTTP错误 ${response.status}: ${response.statusText}`)
      }

      // 处理流式响应
      await handleStreamResponse(response)
      
      // 清除处理完的文件
      if (file) {
        setProcessedFile(null)
      }

    } catch (error: any) {
      console.error('发送消息失败:', error)
      
      if (error.name === 'AbortError') {
        processingStatus.value = '已取消'
        console.log('消息发送被用户取消')
      } else {
        processingStatus.value = ''
        const errorMessage = error.message || '发送失败'
        
        // 添加错误消息
        addMessage({
          content: `❌ ${errorMessage}`,
          isUser: false
        })
      }
    } finally {
      isLoading.value = false
      abortController.value = null
      
      // 延迟清除状态，让用户看到完成状态
      setTimeout(() => {
        if (processingStatus.value === '已取消') {
          processingStatus.value = ''
        }
      }, 2000)
    }
  }

  // 取消请求
  function cancelRequest() {
    if (abortController.value) {
      abortController.value.abort()
      isLoading.value = false
      processingStatus.value = '正在取消...'
    }
  }

  // 清除消息
  function clearMessages() {
    if (conversationStore.currentConversation) {
      conversationStore.clearConversationMessages(conversationStore.currentConversation.id)
    }
    currentStreamingMessage.value = null
    console.log('🧹 消息列表已清除')
  }

  // 设置处理的文件
  function setProcessedFile(file: ProcessedFile | null) {
    processedFile.value = file
  }

  // 文档搜索
  async function searchInDocuments(query: string, docIds?: string[]) {
    if (!query.trim()) return []

    try {
      processingStatus.value = '🔍 搜索文档...'
      
      const searchRequest: RAGSearchRequest = {
        query: query.trim(),
        top_k: 5,
        similarity_threshold: 0.3,
        doc_ids: docIds
      }

      const response = await searchDocuments(searchRequest)
      console.log(`🔍 文档搜索完成，找到${response.chunks ? response.chunks.length : 0}个结果`)
      
      return response.chunks || []
    } catch (error) {
      console.error('文档搜索失败:', error)
      return []
    } finally {
      processingStatus.value = ''
    }
  }

  // 加载聊天历史会话的消息
  async function loadSessionMessages(sessionId: string, page: number = 1, limit: number = 50) {
    try {
      console.log('📜 加载聊天历史会话消息:', sessionId)
      const historyMessages = await conversationStore.fetchRemoteSessionMessages(sessionId, page, limit)
      
      if (historyMessages && historyMessages.length > 0) {
        // 清除当前消息
        clearMessages()
        
        // 将历史消息转换为本地消息格式并添加
        for (const historyMsg of historyMessages) {
          const localMessage: Message = {
            id: historyMsg.id,
            content: historyMsg.content,
            isUser: historyMsg.role === 'user',
            timestamp: new Date(historyMsg.created_at),
            fileInfo: historyMsg.metadata ? {
              name: historyMsg.metadata.fileName || '',
              size: historyMsg.metadata.fileSize || 0,
              type: historyMsg.metadata.fileType || '',
              rag_enabled: historyMsg.metadata.ragEnabled || false,
              doc_id: historyMsg.metadata.docId,
              ocrCompleted: historyMsg.metadata.ocrCompleted || false,
              content: '',
              attachments: historyMsg.metadata.attachments || []
            } : undefined
          }
          
          // 添加到当前对话（不触发保存到历史服务）
          if (conversationStore.currentConversation) {
            conversationStore.addMessageToConversation(conversationStore.currentConversation.id, localMessage)
          }
        }
        
        console.log(`✅ 成功加载${historyMessages.length}条历史消息`)
      }
    } catch (error) {
      console.error('❌ 加载会话消息失败:', error)
    }
  }

  // 切换聊天历史同步状态
  function toggleHistorySync(enabled: boolean) {
    isHistorySyncEnabled.value = enabled
    console.log(`🔄 聊天历史同步${enabled ? '已启用' : '已禁用'}`)
  }

  return {
    // 状态
    isLoading: computed(() => isLoading.value),
    processingStatus: computed(() => processingStatus.value),
    currentStreamingMessage: computed(() => currentStreamingMessage.value),
    processedFile: computed(() => processedFile.value),
    messages,
    hasMessages,
    canSend,
    isHistorySyncEnabled: computed(() => isHistorySyncEnabled.value),
    
    // 方法
    addMessage,
    sendMessage,
    cancelRequest,
    clearMessages,
    setProcessedFile,
    searchInDocuments,
    
    // 聊天历史相关方法
    saveMessageToHistory,
    saveMessagesBatchToHistory,
    ensureActiveSession,
    syncExistingMessagesToHistory,
    updateSessionTitle,
    loadSessionMessages,
    toggleHistorySync
  }
})