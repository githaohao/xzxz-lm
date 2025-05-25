'use client'

import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'

interface StreamEvent {
  type: 'content' | 'complete' | 'error' | 'thinking'
  content?: string
  message?: string
}

export default function StreamingDebug() {
  const [message, setMessage] = useState('请简单介绍一下你自己')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamedContent, setStreamedContent] = useState('')
  const [logs, setLogs] = useState<string[]>([])
  const abortControllerRef = useRef<AbortController | null>(null)

  const addLog = (log: string) => {
    const timestamp = new Date().toLocaleTimeString()
    setLogs(prev => [...prev, `[${timestamp}] ${log}`])
    console.log(log)
  }

  const testStreaming = async () => {
    if (!message.trim()) return

    setIsStreaming(true)
    setStreamedContent('')
    setLogs([])
    
    abortControllerRef.current = new AbortController()
    
    addLog('🚀 开始测试流式连接...')

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: message,
          temperature: 0.7,
          max_tokens: 500
        }),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      addLog('✅ 连接成功，Content-Type: ' + response.headers.get('content-type'))
      
      const reader = response.body?.getReader()
      if (!reader) throw new Error('无法获取响应流')

      const decoder = new TextDecoder()
      let buffer = ''
      let contentLength = 0

      addLog('📡 开始读取流式数据...')

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          addLog('🎉 流式读取完成')
          break
        }

        const chunk = decoder.decode(value, { stream: true })
        addLog(`📦 收到chunk: ${chunk.length} 字节`)
        
        buffer += chunk
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.trim() === '') continue
          
          addLog(`📝 处理行: ${line.slice(0, 100)}${line.length > 100 ? '...' : ''}`)
          
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            
            if (data === '[DONE]') {
              addLog('✅ 接收到完成信号')
              setIsStreaming(false)
              return
            }

            try {
              const event: StreamEvent = JSON.parse(data)
              addLog(`📨 解析事件: ${event.type}`)
              
              if (event.type === 'content' && event.content) {
                contentLength += event.content.length
                addLog(`💬 内容片段: "${event.content}" (累计${contentLength}字符)`)
                setStreamedContent(prev => prev + event.content)
              } else if (event.type === 'complete') {
                addLog('✅ 对话完成')
                setIsStreaming(false)
                return
              } else if (event.type === 'error') {
                addLog(`❌ 服务器错误: ${event.message}`)
                setIsStreaming(false)
                return
              }
            } catch (e) {
              addLog(`⚠️ JSON解析失败: ${data}`)
            }
          }
        }
      }

    } catch (error) {
      addLog(`❌ 请求失败: ${error}`)
      setIsStreaming(false)
    }
  }

  const stopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      addLog('🛑 用户取消请求')
    }
    setIsStreaming(false)
  }

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>流式输出调试工具</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="输入测试消息..."
            className="min-h-[100px]"
            disabled={isStreaming}
          />
          
          <div className="flex gap-2">
            {!isStreaming ? (
              <Button onClick={testStreaming} disabled={!message.trim()}>
                开始流式测试
              </Button>
            ) : (
              <Button variant="destructive" onClick={stopStreaming}>
                停止测试
              </Button>
            )}
            <Button variant="outline" onClick={() => {
              setLogs([])
              setStreamedContent('')
            }}>
              清除日志
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-4">
        {/* 流式内容显示 */}
        <Card>
          <CardHeader>
            <CardTitle>流式内容</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-muted p-4 rounded min-h-[200px] whitespace-pre-wrap font-mono text-sm">
              {streamedContent || '等待流式内容...'}
              {isStreaming && (
                <span className="inline-block w-2 h-4 bg-primary ml-1 animate-pulse" />
              )}
            </div>
          </CardContent>
        </Card>

        {/* 调试日志 */}
        <Card>
          <CardHeader>
            <CardTitle>调试日志</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-black text-green-400 p-4 rounded min-h-[200px] font-mono text-xs overflow-y-auto max-h-[400px]">
              {logs.length === 0 ? (
                <div className="text-gray-500">等待调试日志...</div>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className="mb-1">
                    {log}
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
