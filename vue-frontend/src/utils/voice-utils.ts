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
  
  // 移除思考标签
  let cleaned = text.replace(/<think>[\s\S]*?<\/think>/g, '')
  
  // 移除Markdown格式
  cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, '$1') // 粗体
  cleaned = cleaned.replace(/\*(.*?)\*/g, '$1') // 斜体
  cleaned = cleaned.replace(/`(.*?)`/g, '$1') // 代码
  cleaned = cleaned.replace(/#{1,6}\s*(.*)/g, '$1') // 标题
  cleaned = cleaned.replace(/\[(.*?)\]\(.*?\)/g, '$1') // 链接
  
  // 移除表情符号 (简单的范围)
  cleaned = cleaned.replace(/[\\uD800-\\uDBFF][\\uDC00-\\uDFFF]|[\\u2600-\\u26FF]|[\\u2700-\\u27BF]|[\\uFE00-\\uFE0F]/g, '')
  
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