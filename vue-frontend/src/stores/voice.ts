import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { VoiceMessage, CallState } from '@/types'
import { generateId, cleanTextForSpeech } from '@/utils'
import { 
  sendVoiceMessage, 
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

  // 音频相关引用
  const audioStream = ref<MediaStream | null>(null)
  const audioContext = ref<AudioContext | null>(null)
  const currentAudio = ref<HTMLAudioElement | null>(null)

  // 计算属性
  const hasMessages = computed(() => messages.value.length > 0)
  const isConnected = computed(() => callState.value !== 'idle')
  const canStartCall = computed(() => funAudioAvailable.value && callState.value === 'idle')

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
      
      console.log('✅ 录音初始化成功')
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
      const mediaRecorder = new MediaRecorder(audioStream.value, {
        mimeType: 'audio/webm;codecs=opus'
      })

      const audioChunks: Blob[] = []
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
        await handleUserSpeech('', audioBlob)
      }

      mediaRecorder.start()
      isRecording.value = true
      callState.value = 'listening'
      
      // 10秒后自动停止录音
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop()
          isRecording.value = false
        }
      }, 10000)

      console.log('🎤 开始录音')
    } catch (error) {
      console.error('❌ 开始录音失败:', error)
      throw error
    }
  }

  // 处理用户语音
  async function handleUserSpeech(transcript: string, audioBlob?: Blob): Promise<void> {
    if (!transcript.trim() && !audioBlob) return

    callState.value = 'processing'
    let userMessage: VoiceMessage | null = null
    let aiResponse = ''

    try {
      if (funAudioAvailable.value && audioBlob) {
        console.log('🎯 使用FunAudioLLM流程')

        const result = await sendVoiceMessage(audioBlob, sessionId.value, 'auto')

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
      console.error('❌ 处理语音失败:', error)

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

  // 结束通话
  function endCall(): void {
    callState.value = 'idle'
    isRecording.value = false
    isAIPlaying.value = false
    currentTranscript.value = ''

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

    // 停止当前播放的音频
    if (currentAudio.value) {
      currentAudio.value.pause()
      currentAudio.value = null
    }
  }

  // 切换静音
  function toggleMute(): void {
    isMuted.value = !isMuted.value
    if (currentAudio.value) {
      currentAudio.value.pause()
      isAIPlaying.value = false
    }
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
    toggleMute,
    interruptAI,
    clearHistory,
    restartSession,
    getStatusText
  }
}) 