import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 格式化时间 - 支持Date对象或字符串格式
export function formatTime(date: Date | string): string {
  try {
    // 如果传入的是字符串，先转换为Date对象
    const dateObj = typeof date === 'string' ? new Date(date.replace(' ', 'T')) : date
    
    // 检查是否为有效日期
    if (isNaN(dateObj.getTime())) {
      console.warn('Invalid date provided to formatTime:', date)
      return '无效时间'
    }
    
    return dateObj.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    console.error('Error formatting time:', error)
    return '时间解析错误'
  }
}

// 格式化文件大小
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 清理文本用于语音合成
export function cleanTextForSpeech(text: string): string {
  if (!text) return ''
  
  // 移除思考标签及其内容（包括不完整的标签）
  let cleaned = text.replace(/<think>[\s\S]*?<\/think>/g, '')
  // 移除不完整的思考标签（只有开始标签的情况）
  cleaned = cleaned.replace(/<think>.*$/g, '')
  
  // 移除Markdown格式
  cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, '$1') // 粗体
  cleaned = cleaned.replace(/\*(.*?)\*/g, '$1') // 斜体
  cleaned = cleaned.replace(/`(.*?)`/g, '$1') // 代码
  cleaned = cleaned.replace(/#{1,6}\s*(.*)/g, '$1') // 标题
  cleaned = cleaned.replace(/\[(.*?)\]\(.*?\)/g, '$1') // 链接
  
  // 移除表情符号（更全面的Unicode范围，与后端保持一致）
  cleaned = cleaned.replace(/[\u{1F600}-\u{1F64F}]/gu, '') // 表情符号
  cleaned = cleaned.replace(/[\u{1F300}-\u{1F5FF}]/gu, '') // 符号和图标
  cleaned = cleaned.replace(/[\u{1F680}-\u{1F6FF}]/gu, '') // 交通和地图符号
  cleaned = cleaned.replace(/[\u{1F700}-\u{1F77F}]/gu, '') // 炼金术符号
  cleaned = cleaned.replace(/[\u{1F780}-\u{1F7FF}]/gu, '') // 几何图形扩展
  cleaned = cleaned.replace(/[\u{1F800}-\u{1F8FF}]/gu, '') // 补充箭头-C
  cleaned = cleaned.replace(/[\u{1F900}-\u{1F9FF}]/gu, '') // 补充符号和图标
  cleaned = cleaned.replace(/[\u{1FA00}-\u{1FA6F}]/gu, '') // 扩展-A
  cleaned = cleaned.replace(/[\u{1FA70}-\u{1FAFF}]/gu, '') // 符号和图标扩展-A
  cleaned = cleaned.replace(/[\u{2600}-\u{26FF}]/gu, '') // 杂项符号
  cleaned = cleaned.replace(/[\u{2700}-\u{27BF}]/gu, '') // 装饰符号
  cleaned = cleaned.replace(/[\u{FE00}-\u{FE0F}]/gu, '') // 变体选择器
  
  // 移除多余的空白字符
  cleaned = cleaned.replace(/\s+/g, ' ').trim()
  
  return cleaned
}

// 检查文本是否包含思考标签（包括不完整的标签）
export function hasThinkTags(text: string): boolean {
  // 检查是否包含完整的think标签对，或者只有开始标签
  return /<think>[\s\S]*?<\/think>/.test(text) || /<think>/.test(text)
}

// 提取思考内容
export function extractThinkContent(text: string): { think: string; content: string } {
  // 首先尝试匹配完整的think标签对
  const completeThinkMatch = text.match(/<think>([\s\S]*?)<\/think>/)
  
  if (completeThinkMatch) {
    // 如果有完整的标签对，正常处理
    const think = completeThinkMatch[1].trim()
    const content = text.replace(/<think>[\s\S]*?<\/think>/g, '').trim()
    return { think, content }
  } else {
    // 如果只有开始标签，提取从<think>到文本结尾的内容作为思考内容
    const incompleteThinkMatch = text.match(/<think>([\s\S]*)/)
    if (incompleteThinkMatch) {
      const think = incompleteThinkMatch[1].trim()
      const content = '' // 还没有实际回复内容
      return { think, content }
    }
  }
  
  // 如果没有think标签，返回空的思考内容和原文本
  return { think: '', content: text.trim() }
}

// 生成唯一ID
export function generateId(): string {
  return Date.now().toString() + Math.random().toString(36).substr(2, 9)
}

// 防抖函数
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: number | null = null
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

// 节流函数
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

/**
 * 音频播放队列管理类
 * 用于管理流式TTS音频片段的顺序播放
 */
export class AudioPlayQueue {
  private queue: Array<{
    audio: HTMLAudioElement
    text: string
    chunkId: number
  }> = []
  private isPlaying = false
  private currentAudio: HTMLAudioElement | null = null
  private onPlayStart?: (text: string, chunkId: number) => void
  private onPlayEnd?: (text: string, chunkId: number) => void
  private onQueueEmpty?: () => void
  private onError?: (error: Error) => void

  constructor(callbacks?: {
    onPlayStart?: (text: string, chunkId: number) => void
    onPlayEnd?: (text: string, chunkId: number) => void
    onQueueEmpty?: () => void
    onError?: (error: Error) => void
  }) {
    this.onPlayStart = callbacks?.onPlayStart
    this.onPlayEnd = callbacks?.onPlayEnd  
    this.onQueueEmpty = callbacks?.onQueueEmpty
    this.onError = callbacks?.onError
  }

  /**
   * 添加音频到播放队列
   */
  addAudio(audioBase64: string, text: string, chunkId: number): void {
    try {
      // 将base64转换为Blob和URL
      const audioData = atob(audioBase64)
      const audioArray = new Uint8Array(audioData.length)
      for (let i = 0; i < audioData.length; i++) {
        audioArray[i] = audioData.charCodeAt(i)
      }
      const audioBlob = new Blob([audioArray], { type: 'audio/mpeg' })
      const audioUrl = URL.createObjectURL(audioBlob)

      // 创建音频元素
      const audio = new Audio(audioUrl)
      audio.volume = 0.8

      // 添加到队列
      this.queue.push({ audio, text, chunkId })

      // 如果当前没有播放，开始播放
      if (!this.isPlaying) {
        this.playNext()
      }
    } catch (error) {
      console.error('添加音频到队列失败:', error)
      this.onError?.(new Error(`添加音频失败: ${error}`))
    }
  }

  /**
   * 播放下一个音频
   */
  private async playNext(): Promise<void> {
    if (this.queue.length === 0) {
      this.isPlaying = false
      this.currentAudio = null
      this.onQueueEmpty?.()
      return
    }

    this.isPlaying = true
    const { audio, text, chunkId } = this.queue.shift()!
    this.currentAudio = audio

    try {
      // 播放开始回调
      this.onPlayStart?.(text, chunkId)

      // 设置播放结束事件
      audio.onended = () => {
        this.onPlayEnd?.(text, chunkId)
        // 清理资源
        URL.revokeObjectURL(audio.src)
        // 播放下一个
        this.playNext()
      }

      audio.onerror = (event) => {
        console.error('音频播放错误:', event)
        this.onError?.(new Error('音频播放失败'))
        URL.revokeObjectURL(audio.src)
        // 继续播放下一个
        this.playNext()
      }

      // 开始播放
      await audio.play()
    } catch (error) {
      console.error('播放音频失败:', error)
      this.onError?.(new Error(`播放失败: ${error}`))
      URL.revokeObjectURL(audio.src)
      // 继续播放下一个
      this.playNext()
    }
  }

  /**
   * 停止播放并清空队列
   */
  stop(): void {
    // 停止当前播放
    if (this.currentAudio) {
      this.currentAudio.pause()
      URL.revokeObjectURL(this.currentAudio.src)
      this.currentAudio = null
    }

    // 清空队列并释放资源
    this.queue.forEach(({ audio }) => {
      URL.revokeObjectURL(audio.src)
    })
    this.queue = []
    this.isPlaying = false
  }

  /**
   * 设置音量
   */
  setVolume(volume: number): void {
    if (this.currentAudio) {
      this.currentAudio.volume = Math.max(0, Math.min(1, volume))
    }
  }

  /**
   * 获取队列状态
   */
  getStatus(): {
    isPlaying: boolean
    queueLength: number
  } {
    return {
      isPlaying: this.isPlaying,
      queueLength: this.queue.length
    }
  }
} 