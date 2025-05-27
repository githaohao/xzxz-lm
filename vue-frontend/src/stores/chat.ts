import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Message, ProcessedFile, StreamEvent, RAGSearchRequest } from '@/types'
import { generateId } from '@/utils'
import { sendTextMessage, sendMultimodalMessage, searchDocuments } from '@/utils/api'

export const useChatStore = defineStore('chat', () => {
  // 状态
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const processingStatus = ref('')
  const currentStreamingMessage = ref<Message | null>(null)
  const processedFile = ref<ProcessedFile | null>(null)
  const abortController = ref<AbortController | null>(null)

  // 计算属性
  const hasMessages = computed(() => messages.value.length > 0)
  const canSend = computed(() => !isLoading.value && (processedFile.value || messages.value.length > 0))

  // 添加消息
  function addMessage(message: Omit<Message, 'id' | 'timestamp'>) {
    const newMessage: Message = {
      ...message,
      id: generateId(),
      timestamp: new Date()
    }
    messages.value.push(newMessage)
    return newMessage
  }

  // 更新流式消息
  function updateStreamingMessage(content: string, isComplete: boolean = false) {
    if (currentStreamingMessage.value) {
      currentStreamingMessage.value.content = content
      currentStreamingMessage.value.isStreaming = !isComplete
      
      if (isComplete) {
        messages.value.push({ ...currentStreamingMessage.value })
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
    } finally {
      reader.releaseLock()
    }
  }

  // 发送消息
  async function sendMessage(content: string, file?: ProcessedFile) {
    if (!content.trim() && !file) return

    // 添加用户消息
    const userMessage = addMessage({
      content,
      isUser: true,
      fileInfo: file ? {
        name: file.name,
        size: file.size,
        type: file.type
      } : undefined
    })

    isLoading.value = true
    processingStatus.value = '正在连接...'

    // 创建新的AbortController
    abortController.value = new AbortController()

    try {
      let response: Response

      if (file) {
        console.log('📎 使用多模态接口:', file.name)
        response = await sendMultimodalMessage(
          content,
          messages.value.slice(0, -1), // 不包括刚添加的用户消息
          file,
          0.7,
          2048,
          abortController.value.signal
        )
      } else {
        console.log('💬 使用文本接口')
        response = await sendTextMessage(
          content,
          messages.value.slice(0, -1),
          0.7,
          2048,
          abortController.value.signal
        )
      }

      console.log('✅ 连接成功，开始处理流式响应...')
      processingStatus.value = '开始接收响应...'
      
      await handleStreamResponse(response)

    } catch (error: any) {
      console.error('❌ 发送消息失败:', error)
      
      if (error.name === 'AbortError') {
        console.log('🛑 请求已取消')
        processingStatus.value = '请求已取消'
      } else {
        const errorMessage = addMessage({
          content: `❌ 发送失败: ${error.message}`,
          isUser: false
        })
        processingStatus.value = ''
      }
    } finally {
      isLoading.value = false
      currentStreamingMessage.value = null
      processedFile.value = null
    }
  }

  // 取消请求
  function cancelRequest() {
    if (abortController.value) {
      abortController.value.abort()
      abortController.value = null
    }
    isLoading.value = false
    currentStreamingMessage.value = null
    processingStatus.value = '请求已取消'
  }

  // 清除消息
  function clearMessages() {
    messages.value = []
    currentStreamingMessage.value = null
    processingStatus.value = ''
  }

  // 设置处理的文件
  function setProcessedFile(file: ProcessedFile | null) {
    processedFile.value = file
  }

  // RAG文档检索
  async function searchInDocuments(query: string, docIds?: string[]) {
    try {
      const request: RAGSearchRequest = {
        query,
        doc_ids: docIds,
        top_k: 5,
        min_similarity: 0.6
      }
      
      const response = await searchDocuments(request)
      return response
    } catch (error) {
      console.error('RAG检索失败:', error)
      throw error
    }
  }

  return {
    // 状态
    messages,
    isLoading,
    processingStatus,
    currentStreamingMessage,
    processedFile,
    
    // 计算属性
    hasMessages,
    canSend,
    
    // 方法
    addMessage,
    sendMessage,
    cancelRequest,
    clearMessages,
    setProcessedFile,
    searchInDocuments
  }
}) 