import { ref, computed, onUnmounted, readonly } from 'vue'
import type { VoiceMessage, CallState } from '@/types'
import { generateId } from '@/utils/voice-utils'

export interface WebSocketVoiceConfig {
  url: string
  sessionId?: string
  language?: string
  onMessage?: (message: VoiceMessage) => void
  onStatusChange?: (status: CallState) => void
  onError?: (error: Error) => void
}

export interface StreamAudioChunk {
  text: string
  chunkId: number
  audioSize: number
  isFinal?: boolean
  timestamp: number
}

export function useWebSocketVoice(config: WebSocketVoiceConfig) {
  // 状态管理
  const websocket = ref<WebSocket | null>(null)
  const connectionState = ref<CallState>('idle')
  const isConnected = ref(false)
  const isRecording = ref(false)
  const isAIPlaying = ref(false)
  const currentPlayingText = ref('')
  const recognizedText = ref('')
  const aiResponse = ref('')
  
  // 音频相关
  const mediaRecorder = ref<MediaRecorder | null>(null)
  const audioStream = ref<MediaStream | null>(null)
  const audioChunks = ref<Blob[]>([])
  const audioQueue = ref<HTMLAudioElement[]>([])
  const currentAudio = ref<HTMLAudioElement | null>(null)
  
  // 计算属性
  const canRecord = computed(() => isConnected.value && !isRecording.value && !isAIPlaying.value)
  const canConnect = computed(() => !isConnected.value)

  // 连接WebSocket
  async function connect(): Promise<void> {
    try {
      if (websocket.value?.readyState === WebSocket.OPEN) {
        console.log('WebSocket已连接')
        return
      }

      connectionState.value = 'connecting'
      
      websocket.value = new WebSocket(config.url)
      
      websocket.value.onopen = () => {
        console.log('🔌 WebSocket语音连接已建立')
        isConnected.value = true
        connectionState.value = 'connected'
        config.onStatusChange?.('connected')
        
        // 发送配置
        sendConfig()
      }
      
      websocket.value.onmessage = async (event) => {
        try {
          // 处理JSON消息
          if (typeof event.data === 'string') {
            const message = JSON.parse(event.data)
            await handleWebSocketMessage(message)
          }
          // 处理二进制音频数据
          else if (event.data instanceof Blob) {
            await handleAudioData(event.data)
          }
          // 处理ArrayBuffer音频数据
          else if (event.data instanceof ArrayBuffer) {
            const audioBlob = new Blob([event.data], { type: 'audio/mpeg' })
            await handleAudioData(audioBlob)
          }
        } catch (error) {
          console.error('处理WebSocket消息失败:', error)
          config.onError?.(new Error(`消息处理失败: ${error}`))
        }
      }
      
      websocket.value.onerror = (error) => {
        console.error('❌ WebSocket连接错误:', error)
        config.onError?.(new Error('WebSocket连接错误'))
      }
      
      websocket.value.onclose = () => {
        console.log('🔌 WebSocket连接已关闭')
        isConnected.value = false
        connectionState.value = 'idle'
        config.onStatusChange?.('idle')
        cleanup()
      }
      
    } catch (error) {
      console.error('WebSocket连接失败:', error)
      connectionState.value = 'idle'
      config.onError?.(new Error(`连接失败: ${error}`))
      throw error
    }
  }

  // 断开连接
  function disconnect(): void {
    if (websocket.value) {
      websocket.value.close()
      websocket.value = null
    }
    cleanup()
  }

  // 发送配置
  function sendConfig(): void {
    if (!websocket.value || websocket.value.readyState !== WebSocket.OPEN) return
    
    const configMessage = {
      type: 'config',
      session_id: config.sessionId || `ws-voice-${Date.now()}`,
      language: config.language || 'auto'
    }
    
    websocket.value.send(JSON.stringify(configMessage))
    console.log('📤 发送WebSocket配置:', configMessage)
  }

  // 开始录音
  async function startRecording(): Promise<void> {
    try {
      if (isRecording.value) return
      
      console.log('🎤 开始录音...')
      
      // 获取麦克风权限
      audioStream.value = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      })
      
      // 创建MediaRecorder
      const options = {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 16000
      }
      
      mediaRecorder.value = new MediaRecorder(audioStream.value, options)
      audioChunks.value = []
      
      mediaRecorder.value.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.value.push(event.data)
        }
      }
      
      mediaRecorder.value.onstop = async () => {
        console.log('🎤 录音结束，处理音频数据...')
        await processRecordedAudio()
      }
      
      mediaRecorder.value.start(1000) // 每秒收集一次数据
      isRecording.value = true
      connectionState.value = 'listening'
      config.onStatusChange?.('listening')
      
    } catch (error) {
      console.error('开始录音失败:', error)
      config.onError?.(new Error(`录音失败: ${error}`))
    }
  }

  // 停止录音
  function stopRecording(): void {
    if (mediaRecorder.value && isRecording.value) {
      mediaRecorder.value.stop()
      isRecording.value = false
      
      // 停止音频流
      if (audioStream.value) {
        audioStream.value.getTracks().forEach(track => track.stop())
        audioStream.value = null
      }
    }
  }

  // 处理录音数据
  async function processRecordedAudio(): Promise<void> {
    try {
      if (audioChunks.value.length === 0) {
        console.warn('没有录音数据')
        return
      }
      
      // 合并音频数据
      const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })
      console.log(`🎵 录音数据大小: ${audioBlob.size} 字节`)
      
      // 转换为ArrayBuffer并直接发送二进制数据
      const arrayBuffer = await audioBlob.arrayBuffer()
      
      if (websocket.value?.readyState === WebSocket.OPEN) {
        connectionState.value = 'processing'
        config.onStatusChange?.('processing')
        
        // 直接发送二进制音频数据，无需base64编码
        websocket.value.send(arrayBuffer)
        console.log('📤 发送流式音频数据:', arrayBuffer.byteLength, '字节')
      } else {
        throw new Error('WebSocket连接不可用')
      }
      
    } catch (error) {
      console.error('处理录音数据失败:', error)
      config.onError?.(new Error(`音频处理失败: ${error}`))
      connectionState.value = 'connected'
      config.onStatusChange?.('connected')
    }
  }

  // 处理WebSocket消息
  async function handleWebSocketMessage(message: any): Promise<void> {
    console.log('📥 收到WebSocket消息:', message.type, message)
    
    switch (message.type) {
      case 'status':
        if (message.status === 'listening') {
          connectionState.value = 'connected'
          config.onStatusChange?.('connected')
        }
        break
        
      case 'recognition_result':
        if (message.success && message.recognized_text) {
          recognizedText.value = message.recognized_text
          
          // 添加用户消息
          const userMessage: VoiceMessage = {
            id: generateId(),
            content: message.recognized_text,
            isUser: true,
            timestamp: new Date(),
            recognizedText: message.recognized_text
          }
          config.onMessage?.(userMessage)
        }
        break
        
      case 'ai_thinking':
        connectionState.value = 'processing'
        config.onStatusChange?.('processing')
        aiResponse.value = ''
        break
        
      case 'ai_text_chunk':
        aiResponse.value += message.content
        break
        
      case 'audio_chunk_info':
        // 音频块信息，准备接收二进制数据
        currentPlayingText.value = message.text
        console.log(`🎵 准备播放音频块 ${message.chunk_id}: ${message.text.substring(0, 30)}...`)
        break
        
      case 'stream_complete':
        // 流式处理完成
        if (aiResponse.value.trim()) {
          const aiMessage: VoiceMessage = {
            id: generateId(),
            content: aiResponse.value.trim(),
            isUser: false,
            timestamp: new Date()
          }
          config.onMessage?.(aiMessage)
        }
        
        connectionState.value = 'connected'
        config.onStatusChange?.('connected')
        currentPlayingText.value = ''
        break
        
      case 'error':
        console.error('WebSocket错误:', message.error)
        config.onError?.(new Error(message.error))
        connectionState.value = 'connected'
        config.onStatusChange?.('connected')
        break
        
      case 'tts_error':
        console.error('TTS错误:', message.message)
        break
        
      default:
        console.log('未处理的消息类型:', message.type)
    }
  }

  // 处理音频数据
  async function handleAudioData(audioBlob: Blob): Promise<void> {
    try {
      console.log(`🔊 收到音频数据: ${audioBlob.size} 字节`)
      
      // 创建音频URL
      const audioUrl = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioUrl)
      audio.volume = 0.8
      audio.preload = 'auto'
      
      // 添加到播放队列
      audioQueue.value.push(audio)
      
      // 如果当前没有播放，开始播放
      if (!isAIPlaying.value) {
        await playNextAudio()
      }
      
    } catch (error) {
      console.error('处理音频数据失败:', error)
      config.onError?.(new Error(`音频播放失败: ${error}`))
    }
  }

  // 播放下一个音频
  async function playNextAudio(): Promise<void> {
    if (audioQueue.value.length === 0) {
      isAIPlaying.value = false
      currentPlayingText.value = ''
      connectionState.value = 'connected'
      config.onStatusChange?.('connected')
      return
    }
    
    const audio = audioQueue.value.shift()!
    currentAudio.value = audio
    isAIPlaying.value = true
    connectionState.value = 'speaking'
    config.onStatusChange?.('speaking')
    
    return new Promise((resolve) => {
      audio.onended = async () => {
        // 清理音频URL
        URL.revokeObjectURL(audio.src)
        
        // 播放下一个音频
        await playNextAudio()
        resolve()
      }
      
      audio.onerror = (error) => {
        console.error('音频播放错误:', error)
        URL.revokeObjectURL(audio.src)
        playNextAudio()
        resolve()
      }
      
      audio.play().catch(error => {
        console.error('音频播放失败:', error)
        URL.revokeObjectURL(audio.src)
        playNextAudio()
        resolve()
      })
    })
  }

  // 停止音频播放
  function stopAudio(): void {
    if (currentAudio.value) {
      currentAudio.value.pause()
      currentAudio.value = null
    }
    
    // 清理播放队列
    audioQueue.value.forEach(audio => {
      URL.revokeObjectURL(audio.src)
    })
    audioQueue.value = []
    
    isAIPlaying.value = false
    currentPlayingText.value = ''
  }

  // 发送心跳
  function sendHeartbeat(): void {
    if (websocket.value?.readyState === WebSocket.OPEN) {
      websocket.value.send(JSON.stringify({ type: 'ping' }))
    }
  }

  // 清理资源
  function cleanup(): void {
    stopRecording()
    stopAudio()
    
    if (mediaRecorder.value) {
      mediaRecorder.value = null
    }
    
    if (audioStream.value) {
      audioStream.value.getTracks().forEach(track => track.stop())
      audioStream.value = null
    }
    
    audioChunks.value = []
    recognizedText.value = ''
    aiResponse.value = ''
    currentPlayingText.value = ''
  }

  // 组件卸载时清理
  onUnmounted(() => {
    disconnect()
  })

  return {
    // 状态
    connectionState: readonly(connectionState),
    isConnected: readonly(isConnected),
    isRecording: readonly(isRecording),
    isAIPlaying: readonly(isAIPlaying),
    currentPlayingText: readonly(currentPlayingText),
    recognizedText: readonly(recognizedText),
    aiResponse: readonly(aiResponse),
    
    // 计算属性
    canRecord,
    canConnect,
    
    // 方法
    connect,
    disconnect,
    startRecording,
    stopRecording,
    stopAudio,
    sendHeartbeat,
    cleanup
  }
} 