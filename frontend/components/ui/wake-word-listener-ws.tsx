'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  Loader2,
  Zap,
  Settings,
  Play,
  Pause,
  Wifi,
  WifiOff
} from 'lucide-react'

interface VoiceConfig {
  wake_words: string[]
  confidence_threshold: number
  audio_chunk_duration: number
  silence_timeout: number
  wake_up_message: string
  session_id?: string
}

interface VoiceListenerWSProps {
  onWakeWordDetected: (detectedWord: string, confidence: number) => void
  onError: (error: string) => void
  config?: Partial<VoiceConfig>
  enabled?: boolean
}

type ListeningState = 'idle' | 'connecting' | 'connected' | 'listening' | 'detected' | 'error'
type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error'

export default function VoiceListenerWS({
  onWakeWordDetected,
  onError,
  config = {},
  enabled = true
}: VoiceListenerWSProps) {
  const [listeningState, setListeningState] = useState<ListeningState>('idle')
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [audioLevel, setAudioLevel] = useState(0)
  const [detectedWords, setDetectedWords] = useState<string[]>([])
  const [isEnabled, setIsEnabled] = useState(enabled)
  const [lastDetectionTime, setLastDetectionTime] = useState<Date | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const [latency, setLatency] = useState<number>(0)
  
  const wsRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioStreamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const recordingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const lastPingTimeRef = useRef<number>(0)
  
  // 默认配置
  const defaultConfig: VoiceConfig = {
    wake_words: ["小智小智", "小智", "智能助手"],
    confidence_threshold: 0.6,
    audio_chunk_duration: 1500, // WebSocket模式下可以更短
    silence_timeout: 3000,
    wake_up_message: "我在，请说话"
  }
  
  const finalConfig = { ...defaultConfig, ...config }

  // 建立WebSocket连接
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    setConnectionState('connecting')
    console.log('🔌 建立唤醒词WebSocket连接...')
    
    try {
      // 构建WebSocket URL - 使用唤醒词检测端点
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const backendHost = process.env.NEXT_PUBLIC_BACKEND_HOST || 'localhost:8000'
      const wsUrl = `${protocol}//${backendHost}/api/voice/ws/voice`
      
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws
      
      ws.onopen = () => {
        console.log('✅ 唤醒词WebSocket连接已建立')
        setConnectionState('connected')
        setReconnectAttempts(0)
        
        // 发送配置
        sendConfig()
        
        // 开始心跳
        startHeartbeat()
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          handleWebSocketMessage(message)
        } catch (error) {
          console.error('❌ 解析WebSocket消息失败:', error)
        }
      }
      
      ws.onclose = (event) => {
        console.log('🔌 唤醒词WebSocket连接关闭:', event.code, event.reason)
        setConnectionState('disconnected')
        setListeningState('idle')
        
        // 清理心跳
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current)
          pingIntervalRef.current = null
        }
        
        // 自动重连
        if (isEnabled && reconnectAttempts < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000)
          console.log(`🔄 ${delay}ms后尝试重连 (第${reconnectAttempts + 1}次)`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1)
            connectWebSocket()
          }, delay)
        }
      }
      
      ws.onerror = (error) => {
        console.error('❌ 唤醒词WebSocket连接错误:', error)
        setConnectionState('error')
        onError('WebSocket连接失败')
      }
      
    } catch (error) {
      console.error('❌ 创建WebSocket连接失败:', error)
      setConnectionState('error')
      onError('无法创建WebSocket连接')
    }
  }, [isEnabled, reconnectAttempts, onError])

  // 断开WebSocket连接
  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
    
    setConnectionState('disconnected')
    setReconnectAttempts(0)
  }, [])

  // 发送配置信息
  const sendConfig = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const configMessage = {
        type: 'config',
        wake_words: finalConfig.wake_words,
        confidence_threshold: finalConfig.confidence_threshold,
        language: 'zh',
        session_id: finalConfig.session_id
      }
      
      wsRef.current.send(JSON.stringify(configMessage))
      console.log('📤 发送唤醒词配置信息:', configMessage)
    }
  }, [finalConfig])

  // 开始心跳
  const startHeartbeat = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
    }
    
    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        lastPingTimeRef.current = Date.now()
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000) // 30秒心跳
  }, [])

  // 处理WebSocket消息
  const handleWebSocketMessage = useCallback((message: any) => {
    const { type } = message
    
    switch (type) {
      case 'status':
        if (message.status === 'connected') {
          console.log('✅ 唤醒词WebSocket服务器确认连接')
        } else if (message.status === 'listening') {
          setListeningState('listening')
        }
        break
        
      case 'config_ack':
        console.log('✅ 唤醒词配置已确认:', message.config)
        break
        
      case 'detection':
        if (message.wake_word_detected) {
          console.log('✅ WebSocket检测到唤醒词:', message.detected_word)
          setListeningState('detected')
          setDetectedWords(prev => [...prev, message.detected_word])
          setLastDetectionTime(new Date())
          
          // 播放唤醒音效
          playWakeUpSound()
          
          // 通知父组件
          onWakeWordDetected(message.detected_word, message.confidence)
          
          // 短暂延迟后恢复监听
          setTimeout(() => {
            if (isEnabled) {
              setListeningState('listening')
            }
          }, 1000)
        }
        break
        
      case 'pong':
        // 计算延迟
        const currentTime = Date.now()
        const pingTime = lastPingTimeRef.current
        if (pingTime > 0) {
          setLatency(currentTime - pingTime)
        }
        break
        
      case 'error':
        console.error('❌ 唤醒词WebSocket服务器错误:', message.error)
        setListeningState('error')
        onError(message.error)
        break
        
      default:
        console.warn('⚠️ 未知消息类型:', type)
    }
  }, [isEnabled, onWakeWordDetected, onError])

  // 发送音频数据
  const sendAudioData = useCallback((audioData: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const audioMessage = {
        type: 'audio',
        data: audioData,
        mode: 'wake_word',
        timestamp: Date.now(),
        session_id: finalConfig.session_id
      }
      wsRef.current.send(JSON.stringify(audioMessage))
    }
  }, [finalConfig.session_id])

  // 初始化音频监听
  const initializeAudioListening = useCallback(async () => {
    try {
      console.log('🎤 初始化唤醒词WebSocket音频监听...')
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        } 
      })
      
      audioStreamRef.current = stream
      
      // 设置音频分析器
      const audioContext = new AudioContext()
      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      
      analyser.fftSize = 256
      source.connect(analyser)
      
      audioContextRef.current = audioContext
      analyserRef.current = analyser
      
      // 设置媒体录制器
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorderRef.current = mediaRecorder
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          // 将音频数据转换为base64并发送
          const reader = new FileReader()
          reader.onload = () => {
            const base64Data = (reader.result as string).split(',')[1]
            sendAudioData(base64Data)
          }
          reader.readAsDataURL(event.data)
        }
      }
      
      console.log('✅ 唤醒词WebSocket音频监听初始化成功')
      return true
      
    } catch (error) {
      console.error('❌ 初始化音频监听失败:', error)
      onError('无法访问麦克风，请检查权限设置')
      return false
    }
  }, [onError, sendAudioData])

  // 开始录音
  const startRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'inactive') {
      mediaRecorderRef.current.start()
      
      // 定时停止并重新开始录制
      recordingIntervalRef.current = setInterval(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.stop()
          
          // 短暂延迟后重新开始
          setTimeout(() => {
            if (mediaRecorderRef.current && 
                mediaRecorderRef.current.state === 'inactive' && 
                isEnabled && 
                connectionState === 'connected') {
              mediaRecorderRef.current.start()
            }
          }, 100)
        }
      }, finalConfig.audio_chunk_duration)
    }
  }, [isEnabled, connectionState, finalConfig.audio_chunk_duration])

  // 停止录音
  const stopRecording = useCallback(() => {
    if (recordingIntervalRef.current) {
      clearInterval(recordingIntervalRef.current)
      recordingIntervalRef.current = null
    }
    
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
  }, [])

  // 播放唤醒音效
  const playWakeUpSound = useCallback(() => {
    try {
      if (audioContextRef.current) {
        const oscillator = audioContextRef.current.createOscillator()
        const gainNode = audioContextRef.current.createGain()
        
        oscillator.connect(gainNode)
        gainNode.connect(audioContextRef.current.destination)
        
        oscillator.frequency.setValueAtTime(800, audioContextRef.current.currentTime)
        oscillator.frequency.setValueAtTime(1000, audioContextRef.current.currentTime + 0.1)
        
        gainNode.gain.setValueAtTime(0.3, audioContextRef.current.currentTime)
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContextRef.current.currentTime + 0.3)
        
        oscillator.start(audioContextRef.current.currentTime)
        oscillator.stop(audioContextRef.current.currentTime + 0.3)
      }
    } catch (error) {
      console.warn('播放唤醒音效失败:', error)
    }
  }, [])

  // 开始监听
  const startListening = useCallback(async () => {
    if (!isEnabled) return
    
    // 建立WebSocket连接
    if (connectionState !== 'connected') {
      connectWebSocket()
      return
    }
    
    const success = await initializeAudioListening()
    if (!success) return
    
    setListeningState('listening')
    startRecording()
    
  }, [isEnabled, connectionState, connectWebSocket, initializeAudioListening, startRecording])

  // 停止监听
  const stopListening = useCallback(() => {
    setListeningState('idle')
    stopRecording()
    
    // 关闭音频流
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => track.stop())
      audioStreamRef.current = null
    }
    
    // 关闭音频上下文
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
    
    // 断开WebSocket连接
    disconnectWebSocket()
    
    console.log('🔇 唤醒词WebSocket监听已停止')
  }, [stopRecording, disconnectWebSocket])

  // 切换监听状态
  const toggleListening = useCallback(() => {
    if (listeningState === 'idle') {
      startListening()
    } else {
      stopListening()
    }
  }, [listeningState, startListening, stopListening])

  // 音频级别监控
  useEffect(() => {
    if (listeningState === 'listening' && analyserRef.current) {
      const updateAudioLevel = () => {
        const dataArray = new Uint8Array(analyserRef.current!.frequencyBinCount)
        analyserRef.current!.getByteFrequencyData(dataArray)
        
        const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length
        setAudioLevel(average / 255)
        
        if (listeningState === 'listening') {
          requestAnimationFrame(updateAudioLevel)
        }
      }
      updateAudioLevel()
    }
  }, [listeningState])

  // 自动启动监听 - 当启用状态和连接状态都准备好时
  useEffect(() => {
    if (isEnabled && connectionState === 'connected' && listeningState === 'idle') {
      console.log('🚀 自动开始唤醒词监听...')
      startListening()
    }
  }, [isEnabled, connectionState, listeningState, startListening])

  // 组件挂载时自动建立连接
  useEffect(() => {
    if (isEnabled) {
      console.log('🔌 组件挂载，自动建立WebSocket连接...')
      connectWebSocket()
    }
  }, [isEnabled, connectWebSocket])

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      stopListening()
    }
  }, [stopListening])

  // 启用状态变化时的处理
  useEffect(() => {
    if (!isEnabled && listeningState !== 'idle') {
      stopListening()
    }
  }, [isEnabled, listeningState, stopListening])

  const getStatusColor = () => {
    switch (listeningState) {
      case 'listening': return 'bg-green-500'
      case 'detected': return 'bg-yellow-500'
      case 'connecting': return 'bg-orange-500'
      case 'error': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusText = () => {
    switch (listeningState) {
      case 'connecting': return '正在连接...'
      case 'listening': return '正在监听唤醒词...'
      case 'detected': return '检测到唤醒词！'
      case 'error': return '检测异常'
      default: return '待机中'
    }
  }

  const getConnectionIcon = () => {
    switch (connectionState) {
      case 'connected': return <Wifi className="h-4 w-4 text-green-500" />
      case 'connecting': return <Loader2 className="h-4 w-4 text-orange-500 animate-spin" />
      case 'error': return <WifiOff className="h-4 w-4 text-red-500" />
      default: return <WifiOff className="h-4 w-4 text-gray-500" />
    }
  }

  const getModeIcon = () => {
    return <Zap className="h-4 w-4" />
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          {getModeIcon()}
          唤醒词监听 (WebSocket)
          {getConnectionIcon()}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 连接状态 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getStatusColor()}`} />
            <span className="text-sm font-medium">{getStatusText()}</span>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={connectionState === 'connected' ? 'default' : 'secondary'}>
              {connectionState === 'connected' ? '已连接' : '未连接'}
            </Badge>
            {latency > 0 && (
              <Badge variant="outline" className="text-xs">
                {latency}ms
              </Badge>
            )}
          </div>
        </div>

        {/* 重连信息 */}
        {reconnectAttempts > 0 && connectionState !== 'connected' && (
          <div className="text-xs text-orange-600 bg-orange-50 p-2 rounded">
            重连尝试: {reconnectAttempts}/5
          </div>
        )}

        {/* 音频级别指示器 */}
        {listeningState === 'listening' && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Volume2 className="h-4 w-4" />
              <span className="text-sm">音频级别</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-100"
                style={{ width: `${audioLevel * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* 控制按钮 */}
        <div className="flex gap-2">
          <Button
            onClick={toggleListening}
            variant={listeningState === 'listening' ? 'destructive' : 'default'}
            className="flex-1"
            disabled={!isEnabled}
          >
            {listeningState === 'listening' ? (
              <>
                <MicOff className="h-4 w-4 mr-2" />
                停止监听
              </>
            ) : (
              <>
                <Mic className="h-4 w-4 mr-2" />
                开始监听
              </>
            )}
          </Button>
          
          <Button
            onClick={() => setIsEnabled(!isEnabled)}
            variant="outline"
            size="icon"
          >
            {isEnabled ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
          </Button>
        </div>

        {/* 唤醒词列表 */}
        <div className="space-y-2">
          <span className="text-sm font-medium">支持的唤醒词：</span>
          <div className="flex flex-wrap gap-1">
            {finalConfig.wake_words.map((word, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                {word}
              </Badge>
            ))}
          </div>
        </div>

        {/* 最近检测记录 */}
        {detectedWords.length > 0 && (
          <div className="space-y-2">
            <span className="text-sm font-medium">最近检测：</span>
            <div className="flex flex-wrap gap-1">
              {detectedWords.slice(-3).map((word, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {word}
                </Badge>
              ))}
            </div>
            {lastDetectionTime && (
              <span className="text-xs text-gray-500">
                最后检测时间: {lastDetectionTime.toLocaleTimeString()}
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
} 