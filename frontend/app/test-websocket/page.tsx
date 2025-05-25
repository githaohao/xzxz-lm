'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export default function TestWebSocketPage() {
  const [connectionState, setConnectionState] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const [messages, setMessages] = useState<any[]>([])
  const [isRecording, setIsRecording] = useState(false)
  
  const wsRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioStreamRef = useRef<MediaStream | null>(null)

  const connectWebSocket = () => {
    setConnectionState('connecting')
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const backendHost = process.env.NEXT_PUBLIC_BACKEND_HOST || 'localhost:8000'
    const wsUrl = `${protocol}//${backendHost}/api/voice/ws/voice`
    
    console.log('连接到统一语音端点:', wsUrl)
    
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws
    
    ws.onopen = () => {
      console.log('WebSocket连接已建立')
      setConnectionState('connected')
      
      // 发送配置
      ws.send(JSON.stringify({
        type: 'config',
        wake_words: ['小智小智', '小智', '智能助手'],
        confidence_threshold: 0.6,
        language: 'zh'
      }))
    }
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      console.log('收到消息:', message)
      setMessages(prev => [...prev, { ...message, timestamp: new Date() }])
    }
    
    ws.onclose = () => {
      console.log('WebSocket连接关闭')
      setConnectionState('disconnected')
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
      setConnectionState('error')
    }
  }

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close()
    }
    stopRecording()
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      audioStreamRef.current = stream
      
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          const reader = new FileReader()
          reader.onload = () => {
            const base64Data = (reader.result as string).split(',')[1]
            wsRef.current!.send(JSON.stringify({
              type: 'audio',
              data: base64Data,
              timestamp: Date.now()
            }))
          }
          reader.readAsDataURL(event.data)
        }
      }
      
      mediaRecorder.start()
      setIsRecording(true)
      
      // 每2秒停止并重新开始录制
      const interval = setInterval(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop()
          setTimeout(() => {
            if (mediaRecorder.state === 'inactive' && isRecording) {
              mediaRecorder.start()
            }
          }, 100)
        }
      }, 2000)
      
      // 清理函数
      return () => {
        clearInterval(interval)
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop()
        }
        stream.getTracks().forEach(track => track.stop())
      }
      
    } catch (error) {
      console.error('录音失败:', error)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => track.stop())
    }
    setIsRecording(false)
  }

  const clearMessages = () => {
    setMessages([])
  }

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>WebSocket 统一语音测试</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            
            {/* 连接状态 */}
            <div className="flex items-center gap-4">
              <Badge variant={connectionState === 'connected' ? 'default' : 'secondary'}>
                {connectionState}
              </Badge>
              
              {connectionState === 'disconnected' ? (
                <Button onClick={connectWebSocket}>连接 WebSocket</Button>
              ) : (
                <Button onClick={disconnectWebSocket} variant="destructive">断开连接</Button>
              )}
              
              {connectionState === 'connected' && (
                <>
                  {!isRecording ? (
                    <Button onClick={startRecording}>开始录音</Button>
                  ) : (
                    <Button onClick={stopRecording} variant="destructive">停止录音</Button>
                  )}
                </>
              )}
              
              <Button onClick={clearMessages} variant="outline">清除消息</Button>
            </div>

            {/* 消息列表 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">消息记录 ({messages.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {messages.length === 0 ? (
                    <div className="text-center text-muted-foreground py-4">
                      暂无消息
                    </div>
                  ) : (
                    messages.map((msg, index) => (
                      <div key={index} className="p-3 bg-muted rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline" className="text-xs">
                            {msg.type}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {msg.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                        <pre className="text-sm whitespace-pre-wrap">
                          {JSON.stringify(msg, null, 2)}
                        </pre>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* 使用说明 */}
            <Card className="bg-blue-50 dark:bg-blue-950/20">
              <CardContent className="p-4">
                <h4 className="font-semibold mb-2">测试说明：</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>点击"连接 WebSocket"建立统一语音连接</li>
                  <li>连接成功后点击"开始录音"</li>
                  <li>说出"小智小智"测试唤醒词检测</li>
                  <li>说出其他内容测试语音对话</li>
                  <li>观察消息记录中的检测和对话结果</li>
                  <li>检查是否收到 detection 或 voice_chat_response 类型的消息</li>
                </ul>
              </CardContent>
            </Card>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 