import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { VoiceMessage, CallState, KnowledgeBase } from '@/types'
import { generateId, cleanTextForSpeech, AudioPlayQueue } from '@/utils/voice-utils'
import { 
  sendVoiceMessage, 
  sendVoiceMessageStream,
  synthesizeSpeech, 
  checkFunAudioStatus, 
  clearConversationHistory 
} from '@/utils/api'

export const useVoiceStore = defineStore('voice', () => {
  // 状态
  const messages = ref<VoiceMessage[]>([])
  const callState = ref<CallState>('idle')
  const isRecording = ref(false)
  const isAIPlaying = ref(false)
  const isMuted = ref(false)
  const sessionId = ref(`voice-chat-${Date.now()}`)
  const conversationRounds = ref(0)
  const currentTranscript = ref('')
  const funAudioAvailable = ref(false)
  const speechRecognitionAvailable = ref(false)
  
  // 流式处理相关状态
  const isStreamMode = ref(true) // 默认启用流式模式
  const currentAIResponse = ref('')
  const currentPlayingText = ref('')
  const audioQueue = ref<AudioPlayQueue | null>(null)
  
  // 知识库相关状态
  const selectedKnowledgeBase = ref<KnowledgeBase | null>(null)

  // 音频相关引用
  const audioStream = ref<MediaStream | null>(null)
  const audioContext = ref<AudioContext | null>(null)
  const currentAudio = ref<HTMLAudioElement | null>(null)
  const analyserNode = ref<AnalyserNode | null>(null)
  const mediaRecorder = ref<MediaRecorder | null>(null)
  
  // 智能静音检测配置
  const silenceThreshold = ref(30) // 静音阈值 (0-255)
  const silenceTimeout = ref(2000) // 静音超时时间 (毫秒)
  const minRecordingTime = ref(1000) // 最小录音时间 (毫秒)
  const maxRecordingTime = ref(30000) // 最大录音时间 (毫秒)
  
  // 静音检测状态
  const lastSoundTime = ref(0)
  const recordingStartTime = ref(0)
  const silenceDetectionActive = ref(false)

  // 计算属性
  const hasMessages = computed(() => messages.value.length > 0)
  const isConnected = computed(() => callState.value !== 'idle')
  const canStartCall = computed(() => funAudioAvailable.value && callState.value === 'idle')

  // 初始化音频播放队列
  function initAudioQueue() {
    audioQueue.value = new AudioPlayQueue({
      onPlayStart: (text, chunkId) => {
        currentPlayingText.value = text
        isAIPlaying.value = true
        console.log(`Starting audio chunk ${chunkId}: ${text.substring(0, 30)}...`)
      },
      onPlayEnd: (text, chunkId) => {
        console.log(`Completed audio chunk ${chunkId}`)
      },
      onQueueEmpty: () => {
        isAIPlaying.value = false
        currentPlayingText.value = ''
        callState.value = 'connected'
        console.log('Audio playback queue empty')
        
        // 播放结束后继续录音
        setTimeout(() => {
          if (funAudioAvailable.value && callState.value === 'connected') {
            startRecording()
          }
        }, 500)
      },
      onError: (error) => {
        console.error('Audio playback error:', error)
        isAIPlaying.value = false
        currentPlayingText.value = ''
      }
    })
  }

  // 添加消息
  function addMessage(message: Omit<VoiceMessage, 'id' | 'timestamp'>) {
    const newMessage: VoiceMessage = {
      ...message,
      id: generateId(),
      timestamp: new Date()
    }
    messages.value.push(newMessage)
    return newMessage
  }

  // 音频监测函数
  function startAudioMonitoring(): void {
    if (!audioContext.value || !analyserNode.value) return

    const bufferLength = analyserNode.value.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)
    
    silenceDetectionActive.value = true
    lastSoundTime.value = Date.now()
    recordingStartTime.value = Date.now()

    function checkAudioLevel(): void {
      if (!silenceDetectionActive.value || !analyserNode.value) return

      analyserNode.value.getByteFrequencyData(dataArray)
      
      // 计算平均音量
      let sum = 0
      for (let i = 0; i < bufferLength; i++) {
        sum += dataArray[i]
      }
      const averageVolume = sum / bufferLength

      const currentTime = Date.now()
      const recordingDuration = currentTime - recordingStartTime.value
      const silenceDuration = currentTime - lastSoundTime.value

      // 如果检测到声音，更新最后声音时间
      if (averageVolume > silenceThreshold.value) {
        lastSoundTime.value = currentTime
      }

      // 检查是否应该停止录音
      const shouldStop = (
        // 静音时间超过阈值且已录音最小时间
        (silenceDuration > silenceTimeout.value && recordingDuration > minRecordingTime.value) ||
        // 录音时间超过最大时间
        recordingDuration > maxRecordingTime.value
      )

      if (shouldStop) {
        console.log(`🔇 智能静音检测: 平均音量=${averageVolume.toFixed(1)}, 静音时长=${silenceDuration}ms, 录音时长=${recordingDuration}ms`)
        stopRecording()
        return
      }

      // 继续监测
      requestAnimationFrame(checkAudioLevel)
    }

    checkAudioLevel()
  }

  // 停止音频监测
  function stopAudioMonitoring(): void {
    silenceDetectionActive.value = false
  }

  // 停止录音
  function stopRecording(): void {
    if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
      mediaRecorder.value.stop()
      isRecording.value = false
      stopAudioMonitoring()
      console.log('🎤 录音已停止')
    }
  }

  // 检查服务状态
  async function checkServiceStatus() {
    try {
      funAudioAvailable.value = await checkFunAudioStatus()
      
      // 检查Web Speech API支持
      speechRecognitionAvailable.value = !!(
        (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
      )
      
      console.log('服务状态检查:', {
        funAudio: funAudioAvailable.value,
        speechRecognition: speechRecognitionAvailable.value
      })
    } catch (error) {
      console.error('检查服务状态失败:', error)
      funAudioAvailable.value = false
    }
  }

  // 初始化录音
  async function initRecording(): Promise<void> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      })
      
      audioStream.value = stream
      audioContext.value = new AudioContext()
      
      // 创建音频分析器用于智能静音检测
      const source = audioContext.value.createMediaStreamSource(stream)
      analyserNode.value = audioContext.value.createAnalyser()
      analyserNode.value.fftSize = 256
      analyserNode.value.smoothingTimeConstant = 0.8
      source.connect(analyserNode.value)
      
      console.log('✅ 录音初始化成功，智能静音检测已启用')
    } catch (error) {
      console.error('❌ 录音初始化失败:', error)
      throw new Error('无法访问麦克风，请检查权限设置')
    }
  }

  // 开始录音
  async function startRecording(): Promise<void> {
    if (!audioStream.value) {
      await initRecording()
    }

    if (!audioStream.value) {
      throw new Error('音频流未初始化')
    }

    try {
      mediaRecorder.value = new MediaRecorder(audioStream.value, {
        mimeType: 'audio/webm;codecs=opus'
      })

      const audioChunks: Blob[] = []
      
      mediaRecorder.value.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data)
        }
      }

      mediaRecorder.value.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
        await handleUserSpeech('', audioBlob)
      }

      mediaRecorder.value.start()
      isRecording.value = true
      callState.value = 'listening'
      
      // 启动智能静音检测
      startAudioMonitoring()

      console.log('🎤 开始录音 (智能静音检测已启用)')
    } catch (error) {
      console.error('❌ 开始录音失败:', error)
      throw error
    }
  }

  // 处理用户语音 - 流式版本
  async function handleUserSpeechStream(transcript: string, audioBlob?: Blob): Promise<void> {
    if (!transcript.trim() && !audioBlob) return

    callState.value = 'processing'
    let userMessage: VoiceMessage | null = null
    currentAIResponse.value = ''

    try {
      if (funAudioAvailable.value && audioBlob) {
        console.log('Using streaming FunAudioLLM workflow')

        // 创建用户消息
        userMessage = addMessage({
          content: transcript || '[语音输入]',
          isUser: true,
          recognizedText: transcript
        })

        // 初始化音频队列
        initAudioQueue()

        // 调用流式语音聊天API
        const response = await sendVoiceMessageStream(
          audioBlob, 
          sessionId.value, 
          'auto',
          selectedKnowledgeBase.value?.id
        )

        if (!response.ok) {
          throw new Error(`HTTP错误 ${response.status}: ${response.statusText}`)
        }

        // 处理流式响应
        await handleStreamingResponse(response)

      } else {
        throw new Error('无有效输入')
      }
    } catch (error: any) {
      console.error('Voice processing failed:', error)

      if (!userMessage) {
        userMessage = addMessage({
          content: transcript || '[语音输入]',
          isUser: true
        })
      }

      addMessage({
        content: '抱歉，处理您的语音时出现了问题。请稍后重试。',
        isUser: false
      })

      callState.value = 'connected'
    }
  }

  // 处理流式响应
  async function handleStreamingResponse(response: Response): Promise<void> {
    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('无法读取响应流')
    }

    const decoder = new TextDecoder()
    let buffer = ''

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
              // 流式处理完成，添加完整的AI消息
              if (currentAIResponse.value.trim()) {
                addMessage({
                  content: currentAIResponse.value.trim(),
                  isUser: false
                })
              }
              return
            }

            try {
              const event = JSON.parse(data)
              await handleStreamEvent(event)
            } catch (e) {
              console.warn('解析流式数据失败:', data, e)
            }
          }
        }
      }
    } catch (error) {
      console.error('处理流式响应时出错:', error)
      throw error
    } finally {
      if (!reader.closed) {
        await reader.cancel()
      }
    }
  }

  // 处理流式事件
  async function handleStreamEvent(event: any): Promise<void> {
    switch (event.type) {
      case 'status':
        console.log('📊 状态:', event.message)
        break
        
      case 'recognition':
        console.log('🎤 语音识别:', event.text)
        break
        
      case 'ai_text':
        // AI生成的文字片段
        currentAIResponse.value += event.content
        console.log('💬 AI文字:', event.content)
        break
        
      case 'audio_chunk':
        // 收到音频片段，加入播放队列
        if (audioQueue.value && event.audio) {
          callState.value = 'speaking'
          audioQueue.value.addAudio(event.audio, event.text, event.chunk_id)
          console.log(`🎵 收到音频块 ${event.chunk_id}: ${event.text.substring(0, 30)}...`)
        }
        break
        
      case 'complete':
        console.log('✅ 流式处理完成')
        break
        
      case 'error':
        console.error('❌ 流式处理错误:', event.message)
        throw new Error(event.message)
        
      case 'tts_error':
        console.error('❌ TTS合成错误:', event.message)
        // TTS错误不中断整个流程
        break
        
      default:
        console.log('🔍 未知事件类型:', event.type, event)
    }
  }

  // 修改原有的handleUserSpeech，支持流式模式切换
  async function handleUserSpeech(transcript: string, audioBlob?: Blob): Promise<void> {
    if (isStreamMode.value) {
      return handleUserSpeechStream(transcript, audioBlob)
    } else {
      return handleUserSpeechOriginal(transcript, audioBlob)
    }
  }

  // 原有的非流式处理方法（重命名）
  async function handleUserSpeechOriginal(transcript: string, audioBlob?: Blob): Promise<void> {
    if (!transcript.trim() && !audioBlob) return

    callState.value = 'processing'
    let userMessage: VoiceMessage | null = null
    let aiResponse = ''

    try {
      if (funAudioAvailable.value && audioBlob) {
        console.log('🎯 使用FunAudioLLM流程')

        const result = await sendVoiceMessage(
          audioBlob, 
          sessionId.value, 
          'auto',
          selectedKnowledgeBase.value?.id
        )

        if (result.success) {
          userMessage = addMessage({
            content: result.recognized_text || '[语音输入]',
            isUser: true,
            recognizedText: result.recognized_text
          })

          aiResponse = result.response
          conversationRounds.value = result.history_length || 0

          console.log('✅ FunAudioLLM语音对话成功')
        } else {
          const errorMsg = result.error || ''
          if (errorMsg.includes('未识别到有效语音内容')) {
            console.log('🔇 未检测到语音内容，自动结束通话')
            endCall()
            return
          } else {
            throw new Error(result.error || 'FunAudioLLM对话失败')
          }
        }
      } else {
        throw new Error('无有效输入')
      }

      if (aiResponse) {
        const aiMessage = addMessage({
          content: aiResponse,
          isUser: false
        })

        await speakText(aiResponse)
      }
    } catch (error: any) {
      console.error('Voice processing failed:', error)

      if (!userMessage) {
        userMessage = addMessage({
          content: transcript || '[语音输入]',
          isUser: true
        })
      }

      addMessage({
        content: '抱歉，处理您的语音时出现了问题。请稍后重试。',
        isUser: false
      })
    }

    callState.value = 'connected'
  }

  // 文本转语音
  async function speakText(text: string): Promise<void> {
    try {
      const cleanedText = cleanTextForSpeech(text)

      console.log('🔊 开始语音合成:', cleanedText.substring(0, 50) + '...')

      if (!cleanedText.trim()) {
        console.warn('⚠️ 清理后的文本为空，跳过语音合成')
        isAIPlaying.value = false
        callState.value = 'connected'
        return
      }

      isAIPlaying.value = true
      callState.value = 'speaking'

      try {
        const audioBuffer = await synthesizeSpeech({
          text: cleanedText,
          voice: 'zh-CN-XiaoxiaoNeural',
          rate: 0.9,
          pitch: 1.1
        })

        const audioBlob = new Blob([audioBuffer], { type: 'audio/wav' })
        const audioUrl = URL.createObjectURL(audioBlob)

        const audio = new Audio(audioUrl)
        audio.volume = isMuted.value ? 0 : 0.8
        currentAudio.value = audio

        audio.onplay = () => {
          console.log('✅ AI语音播放开始')
        }

        audio.onended = () => {
          console.log('✅ AI语音播放结束')
          isAIPlaying.value = false
          callState.value = 'connected'
          URL.revokeObjectURL(audioUrl)

          // 播放结束后继续录音
          setTimeout(() => {
            if (funAudioAvailable.value && callState.value === 'connected') {
              startRecording()
            }
          }, 500)
        }

        audio.onerror = (event) => {
          console.error('❌ 音频播放错误:', event)
          isAIPlaying.value = false
          callState.value = 'connected'
          URL.revokeObjectURL(audioUrl)
        }

        await audio.play()
      } catch (error) {
        console.error('❌ TTS API调用失败:', error)
        isAIPlaying.value = false
        callState.value = 'connected'
      }
    } catch (error) {
      console.error('❌ 语音合成失败:', error)
      isAIPlaying.value = false
      callState.value = 'connected'
    }
  }

  // 开始通话
  async function startCall(): Promise<void> {
    if (!funAudioAvailable.value) {
      console.log('⚠️ 检测到FunAudioLLM服务不可用，尝试重新检查状态...')
      await checkServiceStatus()
      await new Promise(resolve => setTimeout(resolve, 1000))
    }

    try {
      callState.value = 'connecting'
      console.log('🎤 启动FunAudioLLM录音模式')
      await initRecording()
      callState.value = 'connected'

      setTimeout(() => {
        startRecording()
      }, 1000)

      messages.value = []
    } catch (error: any) {
      console.error('❌ 开始通话失败:', error)
      callState.value = 'idle'
      throw new Error('开始通话失败，请检查麦克风权限并重试')
    }
  }

  // 结束通话 - 添加停止音频队列
  function endCall(): void {
    callState.value = 'idle'
    isRecording.value = false
    isAIPlaying.value = false
    currentTranscript.value = ''
    currentAIResponse.value = ''
    currentPlayingText.value = ''

    // 停止音频队列
    if (audioQueue.value) {
      audioQueue.value.stop()
      audioQueue.value = null
    }

    // 停止智能静音检测
    stopAudioMonitoring()

    // 停止录音
    if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
      mediaRecorder.value.stop()
    }
    mediaRecorder.value = null

    // 停止音频流
    if (audioStream.value) {
      audioStream.value.getTracks().forEach(track => track.stop())
      audioStream.value = null
    }

    // 关闭音频上下文
    if (audioContext.value) {
      audioContext.value.close()
      audioContext.value = null
    }
    analyserNode.value = null

    // 停止当前播放的音频
    if (currentAudio.value) {
      currentAudio.value.pause()
      currentAudio.value = null
    }

    console.log('📞 通话已结束，所有资源已清理')
  }

  // 切换静音 - 支持音频队列
  function toggleMute(): void {
    isMuted.value = !isMuted.value
    
    if (isMuted.value) {
      // 静音：停止音频队列
      if (audioQueue.value) {
        audioQueue.value.stop()
      }
      if (currentAudio.value) {
        currentAudio.value.pause()
      }
      isAIPlaying.value = false
    } else {
      // 取消静音：设置音量
      if (audioQueue.value) {
        audioQueue.value.setVolume(0.8)
      }
    }
  }

  // 切换流式模式
  function toggleStreamMode(): void {
    isStreamMode.value = !isStreamMode.value
    console.log(`🔄 流式模式已${isStreamMode.value ? '启用' : '禁用'}`)
  }

  // 中断AI说话
  function interruptAI(): void {
    if (isAIPlaying.value) {
      if (currentAudio.value) {
        currentAudio.value.pause()
      }
      isAIPlaying.value = false
      callState.value = 'connected'

      if (funAudioAvailable.value) {
        setTimeout(() => {
          startRecording()
        }, 500)
      }
    }
  }

  // 清除对话历史
  async function clearHistory(): Promise<void> {
    try {
      const success = await clearConversationHistory(sessionId.value)
      if (success) {
        messages.value = []
        conversationRounds.value = 0
        console.log('✅ 对话历史已清除')
      } else {
        console.error('❌ 清除对话历史失败')
      }
    } catch (error) {
      console.error('❌ 清除对话历史错误:', error)
    }
  }

  // 重新开始会话
  function restartSession(): void {
    sessionId.value = `voice-chat-${Date.now()}`
    messages.value = []
    conversationRounds.value = 0
    console.log('🔄 会话已重新开始')
  }

  // 获取状态显示文本
  function getStatusText(): string {
    switch (callState.value) {
      case 'idle':
        return '未连接'
      case 'connecting':
        return '正在连接...'
      case 'connected':
        return '已连接'
      case 'listening':
        return '正在听您说话...'
      case 'speaking':
        return 'AI正在回复...'
      case 'processing':
        return '正在处理...'
      default:
        return '未知状态'
    }
  }

  // 设置选中的知识库
  function setSelectedKnowledgeBase(knowledgeBase: KnowledgeBase | null): void {
    selectedKnowledgeBase.value = knowledgeBase
    console.log('📚 语音聊天知识库已切换:', knowledgeBase?.name || '无')
  }

  // 配置智能静音检测参数
  function configureSilenceDetection(config: {
    threshold?: number
    timeout?: number
    minRecordingTime?: number
    maxRecordingTime?: number
  }): void {
    if (config.threshold !== undefined) {
      silenceThreshold.value = Math.max(0, Math.min(255, config.threshold))
    }
    if (config.timeout !== undefined) {
      silenceTimeout.value = Math.max(500, config.timeout)
    }
    if (config.minRecordingTime !== undefined) {
      minRecordingTime.value = Math.max(500, config.minRecordingTime)
    }
    if (config.maxRecordingTime !== undefined) {
      maxRecordingTime.value = Math.max(5000, config.maxRecordingTime)
    }
    
    console.log('🔧 智能静音检测配置已更新:', {
      threshold: silenceThreshold.value,
      timeout: silenceTimeout.value,
      minRecordingTime: minRecordingTime.value,
      maxRecordingTime: maxRecordingTime.value
    })
  }

  return {
    // 状态
    messages,
    callState,
    isRecording,
    isAIPlaying,
    isMuted,
    sessionId,
    conversationRounds,
    currentTranscript,
    funAudioAvailable,
    speechRecognitionAvailable,
    silenceDetectionActive,
    
    // 流式处理相关状态
    isStreamMode,
    currentAIResponse,
    currentPlayingText,
    
    // 智能静音检测配置
    silenceThreshold,
    silenceTimeout,
    minRecordingTime,
    maxRecordingTime,
    
    // 知识库相关状态
    selectedKnowledgeBase,
    
    // 计算属性
    hasMessages,
    isConnected,
    canStartCall,
    
    // 方法
    addMessage,
    checkServiceStatus,
    startCall,
    endCall,
    startRecording,
    stopRecording,
    toggleMute,
    interruptAI,
    clearHistory,
    restartSession,
    getStatusText,
    configureSilenceDetection,
    setSelectedKnowledgeBase,
    toggleStreamMode
  }
}) 