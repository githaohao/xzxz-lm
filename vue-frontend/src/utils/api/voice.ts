import type { VoiceRecognitionResponse, TTSRequest } from '@/types'
import { API_CONFIG } from '../api-config'
import { api } from './client'

/**
 * 语音聊天API
 */
export async function sendVoiceMessage(
  audioBlob: Blob,
  sessionId: string,
  language: string = 'auto'
): Promise<VoiceRecognitionResponse> {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'voice.wav')
  formData.append('session_id', sessionId)
  formData.append('language', language)

  return api.upload<VoiceRecognitionResponse>(
    API_CONFIG.ENDPOINTS.VOICE_CHAT, 
    formData, 
    API_CONFIG.TIMEOUT.VOICE
  )
}

/**
 * TTS语音合成API
 */
export async function synthesizeSpeech(params: TTSRequest): Promise<ArrayBuffer> {
  return api.post<ArrayBuffer>(API_CONFIG.ENDPOINTS.VOICE_TTS, params, {
    headers: API_CONFIG.HEADERS.BINARY
  })
}

/**
 * 检查FunAudioLLM服务状态
 */
export async function checkFunAudioStatus(): Promise<boolean> {
  try {
    const response = await api.get<any>(API_CONFIG.ENDPOINTS.VOICE_ENGINE)
    // 处理后端返回的嵌套数据结构
    if (response.success && response.engine && response.engine.status) {
      return response.engine.status.available || false
    }
    // 兼容旧的数据结构
    return response.available || false
  } catch (error) {
    console.error('检查FunAudioLLM状态失败:', error)
    return false
  }
}

/**
 * 清除对话历史
 */
export async function clearConversationHistory(sessionId: string): Promise<boolean> {
  try {
    await api.delete(`${API_CONFIG.ENDPOINTS.VOICE_CONVERSATION}/${sessionId}`)
    return true
  } catch (error) {
    console.error('清除对话历史失败:', error)
    return false
  }
} 