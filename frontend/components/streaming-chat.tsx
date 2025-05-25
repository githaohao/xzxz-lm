'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Textarea } from '@/components/ui/textarea'
import { formatTime, formatFileSize } from '@/lib/utils'
import { Send, Paperclip, Bot, User, FileText, Image, Loader2 } from 'lucide-react'
import { CollapsibleThink, hasThinkTag } from '@/components/ui/collapsible-think'

interface Message {
  id: string
  content: string
  isUser: boolean
  timestamp: Date
  fileInfo?: {
    name: string
    size: number
    type: string
  }
  isStreaming?: boolean
}

interface StreamEvent {
  type: 'file_processing' | 'ocr_processing' | 'ocr_complete' | 'ocr_error' | 'thinking' | 'content' | 'complete' | 'error'
  message?: string
  content?: string
  file_info?: any
}

interface ProcessedFile {
  id: string
  name: string
  size: number
  type: string
  content?: string
  ocrText?: string
  uploadTime: Date
  processing: boolean
  error?: string
}

export default function StreamingChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [processedFile, setProcessedFile] = useState<ProcessedFile | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState<Message | null>(null)
  const [processingStatus, setProcessingStatus] = useState<string>('')
  const [fileProcessingStatus, setFileProcessingStatus] = useState<string>('')
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, currentStreamingMessage, scrollToBottom])

  // 处理流式响应
  const handleStreamResponse = async (response: Response) => {
    const reader = response.body?.getReader()
    if (!reader) throw new Error('无法读取响应流')

    const decoder = new TextDecoder()
    let streamingMessage: Message = {
      id: Date.now().toString(),
      content: '',
      isUser: false,
      timestamp: new Date(),
      isStreaming: true
    }

    setCurrentStreamingMessage(streamingMessage)
    setProcessingStatus('') // 清除"正在连接..."状态

    try {
      let buffer = '' // 用于处理不完整的JSON

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        // 立即解码chunk，不等待
        const chunk = decoder.decode(value, { stream: true })
        buffer += chunk
        
        // 按行分割并处理
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 保留最后一行（可能不完整）

        for (const line of lines) {
          if (line.trim() === '') continue
          
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            
            if (data === '[DONE]') {
              // 流式响应完成
              streamingMessage.isStreaming = false
              setMessages(prev => [...prev, streamingMessage])
              setCurrentStreamingMessage(null)
              setProcessingStatus('')
              console.log('✅ 流式响应完成')
              return
            }

            try {
              const event: StreamEvent = JSON.parse(data)
              console.log('📨 接收到事件:', event.type, event.content?.slice(0, 20) + '...')
              
              switch (event.type) {
                case 'file_processing':
                case 'ocr_processing':
                case 'thinking':
                  setProcessingStatus(event.message || '')
                  break
                
                case 'ocr_complete':
                case 'ocr_error':
                  setProcessingStatus(event.message || '')
                  setTimeout(() => setProcessingStatus(''), 2000)
                  break
                
                case 'content':
                  if (event.content) {
                    streamingMessage.content += event.content
                    // 立即更新UI，创建新对象确保React重新渲染
                    setCurrentStreamingMessage({ 
                      ...streamingMessage,
                      content: streamingMessage.content 
                    })
                  }
                  break
                
                case 'complete':
                  streamingMessage.isStreaming = false
                  setMessages(prev => [...prev, streamingMessage])
                  setCurrentStreamingMessage(null)
                  setProcessingStatus('')
                  console.log('✅ 对话完成')
                  return
                
                case 'error':
                  streamingMessage.content = `❌ ${event.message}`
                  streamingMessage.isStreaming = false
                  setMessages(prev => [...prev, streamingMessage])
                  setCurrentStreamingMessage(null)
                  setProcessingStatus('')
                  console.error('❌ 流式响应错误:', event.message)
                  return
              }
            } catch (e) {
              console.warn('⚠️ 解析流式数据失败:', data, e)
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }

  // 转换消息格式为后端需要的ChatMessage格式
  const convertToBackendMessages = (messages: Message[], limit: number = 10) => {
    // 只取最近的消息，避免token过多
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

  // 发送消息
  const sendMessage = async () => {
    if (!inputMessage.trim() && !processedFile) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      isUser: true,
      timestamp: new Date(),
      fileInfo: processedFile ? {
        name: processedFile.name,
        size: processedFile.size,
        type: processedFile.type
      } : undefined
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)
    setProcessingStatus('正在连接...')

    // 创建新的AbortController
    abortControllerRef.current = new AbortController()

    console.log('🚀 开始发送消息:', inputMessage.slice(0, 50) + '...')

    try {
      let response: Response

      // 准备对话历史（不包括刚添加的用户消息，因为当前消息会单独发送）
      const history = convertToBackendMessages(messages)

      if (processedFile) {
        // 使用已处理的文件数据发送消息
        console.log('📎 使用已处理文件数据:', processedFile.name)
        
        const requestData = {
          message: inputMessage,
          history: history,
          file_data: {
            name: processedFile.name,
            type: processedFile.type,
            size: processedFile.size,
            ocr_text: processedFile.ocrText || null
          },
          temperature: 0.7,
          max_tokens: 2048
        }

        response = await fetch('/api/chat/multimodal/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestData),
          signal: abortControllerRef.current.signal
        })
      } else {
        // 纯文本时使用文本流式接口
        console.log('💬 使用文本流式接口')
        response = await fetch('/api/chat/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            message: inputMessage,
            history: history,
            temperature: 0.7,
            max_tokens: 2048
          }),
          signal: abortControllerRef.current.signal
        })
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      console.log('✅ 连接成功，开始处理流式响应...')
      setProcessingStatus('开始接收响应...')
      
      await handleStreamResponse(response)

    } catch (error) {
      console.error('发送消息失败:', error)
      
      let errorMessage = '发送消息失败，请稍后重试'
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorMessage = '请求已取消'
        } else if (error.message.includes('网络')) {
          errorMessage = '网络连接失败，请检查网络连接后重试'
        } else {
          errorMessage = error.message
        }
      }
      
      const errorAiMessage: Message = {
        id: Date.now().toString(),
        content: `❌ ${errorMessage}`,
        isUser: false,
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, errorAiMessage])
      setCurrentStreamingMessage(null)
      setProcessingStatus('')
    } finally {
      setIsLoading(false)
      setSelectedFile(null)
      setProcessedFile(null)
      setFileProcessingStatus('')
      abortControllerRef.current = null
    }
  }

  // 取消请求
  const cancelRequest = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setIsLoading(false)
      setCurrentStreamingMessage(null)
      setProcessingStatus('')
    }
  }

  // 立即处理文件（上传并OCR）
  const processFileImmediately = async (file: File) => {
    console.log('🚀 开始立即处理文件:', file.name)
    
    const fileId = Date.now().toString()
    const newProcessedFile: ProcessedFile = {
      id: fileId,
      name: file.name,
      size: file.size,
      type: file.type,
      uploadTime: new Date(),
      processing: true
    }
    
    setProcessedFile(newProcessedFile)
    setFileProcessingStatus('正在上传文件...')

    try {
      // 创建FormData上传文件
      const formData = new FormData()
      formData.append('file', file)

      // 上传文件
      const uploadResponse = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })

      if (!uploadResponse.ok) {
        throw new Error(`文件上传失败: ${uploadResponse.statusText}`)
      }

      const uploadResult = await uploadResponse.json()
      console.log('✅ 文件上传成功:', uploadResult)

      // 如果是支持OCR的文件类型，进行OCR处理
      const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
      if (['.pdf', '.png', '.jpg', '.jpeg'].includes(fileExt)) {
        setFileProcessingStatus('正在识别文件内容...')
        
        // 调用OCR API
        const ocrFormData = new FormData()
        ocrFormData.append('file_path', uploadResult.file_path)

        const ocrResponse = await fetch('/api/ocr', {
          method: 'POST',
          body: ocrFormData
        })

        if (!ocrResponse.ok) {
          throw new Error(`OCR处理失败: ${ocrResponse.statusText}`)
        }

        const ocrResult = await ocrResponse.json()
        console.log('✅ OCR处理完成，提取文本长度:', ocrResult.text?.length || 0)

        // 更新处理结果
        setProcessedFile(prev => prev ? {
          ...prev,
          ocrText: ocrResult.text,
          processing: false
        } : null)
        setFileProcessingStatus(`文件处理完成，提取了 ${ocrResult.text?.length || 0} 字符`)
      } else {
        // 非OCR文件，直接标记为完成
        setProcessedFile(prev => prev ? {
          ...prev,
          processing: false
        } : null)
        setFileProcessingStatus('文件上传完成')
      }

    } catch (error) {
      console.error('❌ 文件处理失败:', error)
      const errorMessage = error instanceof Error ? error.message : '文件处理失败'
      setProcessedFile(prev => prev ? {
        ...prev,
        processing: false,
        error: errorMessage
      } : null)
      setFileProcessingStatus(`处理失败: ${errorMessage}`)
    }
  }

  // 文件上传处理
  const handleFileSelect = async (file: File) => {
    const maxSize = 50 * 1024 * 1024 // 50MB
    if (file.size > maxSize) {
      alert('文件大小不能超过50MB')
      return
    }

    const allowedTypes = ['.pdf', '.png', '.jpg', '.jpeg', '.wav', '.mp3']
    const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    
    if (!allowedTypes.some(type => type === fileExt)) {
      alert('不支持的文件类型')
      return
    }

    setSelectedFile(file)
    // 立即处理文件（上传并OCR）
    await processFileImmediately(file)
  }

  // 拖拽处理
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  // 键盘事件处理
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!isLoading) {
        sendMessage()
      }
    }
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* 聊天区域 */}
      <div 
        className={`flex-1 overflow-hidden p-4 transition-colors ${
          isDragOver ? 'bg-accent/50 border-2 border-dashed border-primary' : ''
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <ScrollArea className="h-full">
          <div className="space-y-4 pb-4">
            {messages.length === 0 && !currentStreamingMessage && (
              <div className="flex items-center justify-center h-full min-h-[400px]">
                <Card className="w-96">
                  <CardHeader>
                    <CardTitle className="text-center">欢迎使用TZ-LM助手</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm text-muted-foreground">
                    <div className="flex items-center space-x-2">
                      <FileText className="h-4 w-4" />
                      <span>支持PDF文档扫描识别</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Image className="h-4 w-4" />
                      <span>支持图片文字提取</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Bot className="h-4 w-4" />
                      <span>基于Qwen3-32B模型</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Loader2 className="h-4 w-4" />
                      <span>实时流式响应</span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 max-w-4xl ${message.isUser ? 'ml-auto flex-row-reverse' : ''}`}
              >
                <Avatar className="flex-shrink-0">
                  <AvatarFallback>
                    {message.isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </AvatarFallback>
                </Avatar>

                <div className={`flex flex-col gap-2 max-w-[80%] ${message.isUser ? 'items-end' : 'items-start'}`}>
                  {message.fileInfo && (
                    <Card className="p-2">
                      <div className="flex items-center gap-2 text-sm">
                        <Paperclip className="h-4 w-4" />
                        <span>{message.fileInfo.name}</span>
                        <Badge variant="outline" className="text-xs">
                          {formatFileSize(message.fileInfo.size)}
                        </Badge>
                      </div>
                    </Card>
                  )}

                  <Card className={message.isUser ? 'bg-primary text-primary-foreground' : ''}>
                    <CardContent className="p-3">
                      {!message.isUser && hasThinkTag(message.content) ? (
                        <CollapsibleThink content={message.content} isStreaming={false} />
                      ) : (
                        <div className="whitespace-pre-wrap break-words">
                          {message.content}
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  <div className="text-xs text-muted-foreground">
                    {formatTime(message.timestamp)}
                  </div>
                </div>
              </div>
            ))}

            {/* 当前流式消息 */}
            {currentStreamingMessage && (
              <div className="flex gap-3 max-w-4xl">
                <Avatar className="flex-shrink-0">
                  <AvatarFallback>
                    <Bot className="h-4 w-4" />
                  </AvatarFallback>
                </Avatar>

                <div className="flex flex-col gap-2 max-w-[80%]">
                  <Card>
                    <CardContent className="p-3">
                      {hasThinkTag(currentStreamingMessage.content) ? (
                        <CollapsibleThink 
                          content={currentStreamingMessage.content} 
                          isStreaming={currentStreamingMessage.isStreaming || false} 
                        />
                      ) : (
                        <div className="whitespace-pre-wrap break-words">
                          {currentStreamingMessage.content}
                        </div>
                      )}
                      {currentStreamingMessage.isStreaming && !hasThinkTag(currentStreamingMessage.content) && (
                        <span className="inline-block w-2 h-5 bg-primary ml-1 animate-pulse" />
                      )}
                    </CardContent>
                  </Card>

                  <div className="text-xs text-muted-foreground">
                    {formatTime(currentStreamingMessage.timestamp)}
                  </div>
                </div>
              </div>
            )}

            {/* 处理状态 */}
            {processingStatus && (
              <div className="flex gap-3">
                <Avatar className="flex-shrink-0">
                  <AvatarFallback>
                    <Bot className="h-4 w-4" />
                  </AvatarFallback>
                </Avatar>
                <Card>
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>{processingStatus}</span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
      </div>

      {/* 输入区域 */}
      <Card className="rounded-none border-t">
        <CardContent className="p-4">
          {/* 文件预览和处理状态 */}
          {(selectedFile || processedFile) && (
            <Card className="mb-3 bg-accent/50">
              <CardContent className="p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Paperclip className="h-4 w-4" />
                    <span className="text-sm">{selectedFile?.name || processedFile?.name}</span>
                    <Badge variant="outline" className="text-xs">
                      {formatFileSize(selectedFile?.size || processedFile?.size || 0)}
                    </Badge>
                    {processedFile && !processedFile.processing && !processedFile.error && (
                      <Badge variant="default" className="text-xs">
                        已处理
                      </Badge>
                    )}
                    {processedFile?.processing && (
                      <Badge variant="secondary" className="text-xs">
                        <Loader2 className="h-3 w-3 animate-spin mr-1" />
                        处理中
                      </Badge>
                    )}
                    {processedFile?.error && (
                      <Badge variant="destructive" className="text-xs">
                        错误
                      </Badge>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSelectedFile(null)
                      setProcessedFile(null)
                      setFileProcessingStatus('')
                    }}
                  >
                    ✕
                  </Button>
                </div>
                
                {/* 文件处理状态显示 */}
                {fileProcessingStatus && (
                  <div className="mt-2 text-xs text-muted-foreground">
                    {fileProcessingStatus}
                  </div>
                )}
                
                {/* OCR文本预览 */}
                {processedFile?.ocrText && (
                  <div className="mt-2 p-2 bg-background rounded text-xs">
                    <div className="text-muted-foreground mb-1">提取的文本内容:</div>
                    <div className="max-h-20 overflow-y-auto text-foreground">
                      {processedFile.ocrText.substring(0, 200)}
                      {processedFile.ocrText.length > 200 && '...'}
                    </div>
                  </div>
                )}
                
                {/* 错误信息显示 */}
                {processedFile?.error && (
                  <div className="mt-2 p-2 bg-destructive/10 border border-destructive/20 rounded text-xs text-destructive">
                    {processedFile.error}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 输入框 */}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Textarea
                ref={textareaRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入消息，支持拖拽文件..."
                className="min-h-[52px] max-h-32 resize-none pr-12"
                disabled={isLoading}
              />
              
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.wav,.mp3"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) handleFileSelect(file)
                  e.target.value = ''
                }}
                className="hidden"
              />
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-2 top-2 h-8 w-8"
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
              >
                <Paperclip className="h-4 w-4" />
              </Button>
            </div>

            {isLoading ? (
              <Button variant="destructive" onClick={cancelRequest}>
                取消
              </Button>
            ) : (
              <Button
                onClick={sendMessage}
                disabled={(!inputMessage.trim() && !processedFile) || isLoading || (processedFile?.processing)}
              >
                <Send className="h-4 w-4" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 