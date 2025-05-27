/**
 * RAG功能相关工具函数
 */

import type { ProcessedFile } from '@/types'

/**
 * 检查文件是否适合使用RAG
 */
export function isFileRagSuitable(file: ProcessedFile): boolean {
  // 需要有OCR内容且内容长度足够
  if (!file.content || file.content.trim().length < 50) {
    return false
  }
  
  // 支持的文件类型
  const supportedTypes = ['pdf', 'png', 'jpg', 'jpeg']
  const fileExt = file.name.toLowerCase().split('.').pop()
  
  return supportedTypes.includes(fileExt || '')
}

/**
 * 获取RAG模式的显示文本
 */
export function getRagModeText(ragEnabled: boolean, fileHasRag: boolean): string {
  if (!fileHasRag) {
    return '📄 常规文本模式'
  }
  
  return ragEnabled ? '🧠 智能检索模式' : '📄 完整文档模式'
}

/**
 * 获取RAG状态的颜色类
 */
export function getRagStatusColor(ragEnabled: boolean, fileHasRag: boolean): string {
  if (!fileHasRag) {
    return 'text-gray-500 dark:text-gray-400'
  }
  
  return ragEnabled ? 'text-purple-600 dark:text-purple-400' : 'text-blue-600 dark:text-blue-400'
}

/**
 * 获取RAG智能建议
 */
export function getRagSuggestion(query: string, fileContent?: string): string | null {
  if (!fileContent || !query) return null
  
  const queryLength = query.length
  const contentLength = fileContent.length
  
  // 如果查询很短但文档很长，建议使用RAG
  if (queryLength < 50 && contentLength > 2000) {
    return '💡 建议启用智能检索，更快找到相关内容'
  }
  
  // 如果查询很具体（包含关键词），建议使用RAG
  const specificKeywords = ['什么', '如何', '为什么', '在哪里', '什么时候', '谁']
  const hasSpecificQuery = specificKeywords.some(keyword => query.includes(keyword))
  
  if (hasSpecificQuery && contentLength > 1000) {
    return '💡 检测到具体问题，智能检索可能效果更好'
  }
  
  return null
}

/**
 * 格式化RAG检索结果摘要
 */
export function formatRagResultSummary(chunkCount: number, totalContent: number): string {
  if (chunkCount === 0) {
    return '未找到相关内容，使用完整文档'
  }
  
  const percentage = Math.round((chunkCount * 1000 / totalContent) * 100)
  return `检索到 ${chunkCount} 个相关片段 (~${percentage}% 内容)`
} 