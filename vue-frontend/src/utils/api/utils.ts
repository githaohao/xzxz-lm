import type { 
  Message, 
  BackendMessage,
  ChatMessage,
  CreateMessageDto
} from '@/types'

/**
 * 转换消息格式为后端需要的格式
 */
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

/**
 * 将前端Message转换为ChatMessage格式
 */
export function convertToChatMessage(
  message: Message,
  sessionId: string,
  role: 'user' | 'assistant' = 'user'
): Omit<CreateMessageDto, 'sessionId'> {
  return {
    role,
    content: message.content,
    messageType: message.fileInfo ? 'file' : 'text',
    metadata: message.fileInfo ? {
      fileName: message.fileInfo.name,
      fileSize: message.fileInfo.size,
      filePath: message.fileInfo.type
    } : undefined
  }
}

/**
 * 将ChatMessage转换为前端Message格式
 */
export function convertToMessage(chatMessage: ChatMessage): Message {
  return {
    id: chatMessage.id,
    content: chatMessage.content,
    isUser: chatMessage.role === 'user',
    timestamp: new Date(chatMessage.createdAt),
    fileInfo: chatMessage.metadata?.fileName ? {
      name: chatMessage.metadata.fileName,
      size: chatMessage.metadata.fileSize || 0,
      type: chatMessage.metadata.filePath || '',
      rag_enabled: false
    } : undefined
  }
} 