'use client'

import React, { useState } from 'react'
import { ChevronDown, ChevronRight, Brain, Loader2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface CollapsibleThinkProps {
  content: string
  className?: string
  isStreaming?: boolean
}

export function CollapsibleThink({ content, className, isStreaming = false }: CollapsibleThinkProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  // 解析think标签内容（支持不完整的标签）
  const parseThinkContent = (text: string) => {
    // 检测完整的think标签
    const completeThinkRegex = /<think>([\s\S]*?)<\/think>/
    const completeMatch = text.match(completeThinkRegex)
    
    if (completeMatch) {
      const thinkContent = completeMatch[1].trim()
      const mainContent = text.replace(completeThinkRegex, '').trim()
      return { thinkContent, mainContent, isComplete: true }
    }
    
    // 检测不完整的think标签（只有开始标签）
    const partialThinkRegex = /<think>([\s\S]*?)$/
    const partialMatch = text.match(partialThinkRegex)
    
    if (partialMatch) {
      const thinkContent = partialMatch[1].trim()
      const mainContent = text.replace(partialThinkRegex, '').trim()
      return { thinkContent, mainContent, isComplete: false }
    }
    
    return { thinkContent: '', mainContent: text, isComplete: true }
  }

  const { thinkContent, mainContent, isComplete } = parseThinkContent(content)

  // 如果没有think内容，直接返回原内容
  if (!thinkContent && !content.includes('<think>')) {
    return <div className="whitespace-pre-wrap break-words">{content}</div>
  }

  return (
    <div className={cn("space-y-3", className)}>
      {/* 思考过程折叠区域 */}
      <Card className="think-container bg-blue-50/50 border-blue-200 dark:bg-blue-950/20 dark:border-blue-800">
        <CardContent className="p-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="think-toggle-button w-full justify-start gap-2 h-auto p-2 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/30"
          >
            <Brain className="h-4 w-4 flex-shrink-0" />
            <span className="text-sm font-medium">
              {!isComplete && isStreaming ? 'AI正在思考中...' : 'AI思考过程'}
            </span>
            {!isComplete && isStreaming ? (
              <Loader2 className="h-4 w-4 ml-auto animate-spin" />
            ) : isExpanded ? (
              <ChevronDown className="h-4 w-4 ml-auto transition-transform duration-200" />
            ) : (
              <ChevronRight className="h-4 w-4 ml-auto transition-transform duration-200" />
            )}
          </Button>
          
          {(isExpanded || (!isComplete && isStreaming)) && (
            <div className="think-expanded mt-3 pt-3 border-t border-blue-200 dark:border-blue-800">
              <div className="think-content text-sm text-blue-800 dark:text-blue-200 whitespace-pre-wrap leading-relaxed">
                {thinkContent || '思考中...'}
                {!isComplete && isStreaming && (
                  <span className="inline-block w-2 h-4 bg-blue-600 ml-1 animate-pulse" />
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 主要回复内容 */}
      {mainContent && (
        <div className="whitespace-pre-wrap break-words">
          {mainContent}
        </div>
      )}
    </div>
  )
}

// 工具函数：检查文本是否包含think标签（包括不完整的）
export function hasThinkTag(text: string): boolean {
  return /<think>[\s\S]*?<\/think>/.test(text) || /<think>[\s\S]*$/.test(text)
}

// 工具函数：检查是否有完整的think标签
export function hasCompleteThinkTag(text: string): boolean {
  return /<think>[\s\S]*?<\/think>/.test(text)
}

// 工具函数：检查是否有不完整的think标签
export function hasPartialThinkTag(text: string): boolean {
  return /<think>[\s\S]*$/.test(text) && !/<think>[\s\S]*?<\/think>/.test(text)
}

// 工具函数：提取think标签内容
export function extractThinkContent(text: string): { thinkContent: string; mainContent: string } {
  const thinkRegex = /<think>([\s\S]*?)<\/think>/
  const match = text.match(thinkRegex)
  
  if (!match) {
    return { thinkContent: '', mainContent: text }
  }

  const thinkContent = match[1].trim()
  const mainContent = text.replace(thinkRegex, '').trim()
  
  return { thinkContent, mainContent }
} 