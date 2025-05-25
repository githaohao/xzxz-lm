import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 格式化时间
export function formatTime(date: Date): string {
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
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
  
  // 移除思考标签
  let cleaned = text.replace(/<think>[\s\S]*?<\/think>/g, '')
  
  // 移除Markdown格式
  cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, '$1') // 粗体
  cleaned = cleaned.replace(/\*(.*?)\*/g, '$1') // 斜体
  cleaned = cleaned.replace(/`(.*?)`/g, '$1') // 代码
  cleaned = cleaned.replace(/#{1,6}\s*(.*)/g, '$1') // 标题
  cleaned = cleaned.replace(/\[(.*?)\]\(.*?\)/g, '$1') // 链接
  
  // 移除多余的空白字符
  cleaned = cleaned.replace(/\s+/g, ' ').trim()
  
  return cleaned
}

// 检查文本是否包含思考标签
export function hasThinkTags(text: string): boolean {
  return /<think>[\s\S]*?<\/think>/.test(text)
}

// 提取思考内容
export function extractThinkContent(text: string): { think: string; content: string } {
  const thinkMatch = text.match(/<think>([\s\S]*?)<\/think>/)
  const think = thinkMatch ? thinkMatch[1].trim() : ''
  const content = text.replace(/<think>[\s\S]*?<\/think>/g, '').trim()
  
  return { think, content }
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
  let timeout: NodeJS.Timeout | null = null
  
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