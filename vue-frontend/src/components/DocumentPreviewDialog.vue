<template>
  <Dialog v-model:open="isOpen">
    <DialogContent class="max-w-6xl max-h-[90vh] w-[90vw] flex flex-col overflow-hidden">
      <DialogHeader class="flex-shrink-0">
        <DialogTitle class="text-xl font-semibold flex items-center gap-2">
          <FileText class="h-6 w-6 text-blue-500" />
          文档预览
        </DialogTitle>
        <DialogDescription>
          查看文档详细信息和内容分块
        </DialogDescription>
      </DialogHeader>

      <!-- 加载状态 -->
      <div v-if="isLoading" class="flex-1 flex flex-col items-center justify-center">
        <Loader2 class="h-12 w-12 animate-spin text-slate-400 mb-4" />
        <p class="text-slate-500">正在加载文档内容...</p>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="flex-1 flex flex-col items-center justify-center">
        <AlertTriangle class="h-12 w-12 text-red-400 mb-4" />
        <p class="text-red-600 mb-4">{{ error }}</p>
        <Button @click="loadDocument" variant="outline">
          <RefreshCw class="h-4 w-4 mr-2" />
          重试
        </Button>
      </div>

      <!-- 主内容区域 -->
      <div v-else-if="documentInfo && chunks" class="flex-1 flex min-h-0 gap-6 overflow-hidden">
        <!-- 左侧文档信息面板 -->
        <div class="w-80 flex-shrink-0 space-y-6 overflow-y-auto pr-2">
          <!-- 基本信息 -->
          <Card>
            <CardHeader>
              <CardTitle class="text-lg flex items-center gap-2">
                <Info class="h-5 w-5" />
                基本信息
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div>
                <label class="text-sm font-medium text-slate-600 dark:text-slate-400">文件名</label>
                <p class="text-sm text-slate-900 dark:text-slate-100 break-all">{{ documentInfo.filename }}</p>
              </div>
              <div>
                <label class="text-sm font-medium text-slate-600 dark:text-slate-400">文件类型</label>
                <Badge variant="outline" class="mt-1">
                  {{ getFileTypeDisplay(documentInfo.file_type) }}
                </Badge>
              </div>
              <div>
                <label class="text-sm font-medium text-slate-600 dark:text-slate-400">文件大小</label>
                <p class="text-sm text-slate-900 dark:text-slate-100">{{ formatFileSize(documentInfo.total_length) }}</p>
              </div>
              <div>
                <label class="text-sm font-medium text-slate-600 dark:text-slate-400">分块数量</label>
                <p class="text-sm text-slate-900 dark:text-slate-100 flex items-center gap-1">
                  <Hash class="h-4 w-4" />
                  {{ documentInfo.chunk_count }} 个片段
                </p>
              </div>
              <div>
                <label class="text-sm font-medium text-slate-600 dark:text-slate-400">创建时间</label>
                <p class="text-sm text-slate-900 dark:text-slate-100 flex items-center gap-1">
                  <Clock class="h-4 w-4" />
                  {{ formatDate(documentInfo.created_at) }}
                </p>
              </div>
              <div>
                <label class="text-sm font-medium text-slate-600 dark:text-slate-400">文档ID</label>
                <p class="text-xs font-mono text-slate-500 dark:text-slate-400 break-all">{{ documentInfo.doc_id }}</p>
              </div>
            </CardContent>
          </Card>

          <!-- 所属知识库 -->
          <Card v-if="knowledgeBases.length > 0">
            <CardHeader>
              <CardTitle class="text-lg flex items-center gap-2">
                <Database class="h-5 w-5" />
                所属知识库
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div class="space-y-2">
                <Badge
                  v-for="kb in knowledgeBases"
                  :key="kb.id"
                  variant="secondary"
                  class="flex items-center gap-2 justify-start w-full p-2 h-auto"
                  :style="{ backgroundColor: `${kb.color}20`, borderColor: kb.color }"
                >
                  <div
                    class="w-3 h-3 rounded-full"
                    :style="{ backgroundColor: kb.color }"
                  ></div>
                  <span class="text-sm">{{ kb.name }}</span>
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- 右侧内容分块面板 -->
        <div class="flex-1 flex flex-col min-w-0 min-h-0">
          <Card class="flex-1 flex flex-col min-h-0">
            <CardHeader class="flex-shrink-0 border-b border-slate-200 dark:border-slate-700">
              <div class="flex items-center justify-between">
                <CardTitle class="text-lg flex items-center gap-2">
                  <FileText class="h-5 w-5" />
                  内容分块 ({{ chunks.length }})
                </CardTitle>
                <div class="flex items-center gap-2">
                  <Button
                    @click="toggleMetadata"
                    variant="outline"
                    size="sm"
                  >
                    <Eye class="h-4 w-4 mr-1" />
                    {{ showMetadata ? '隐藏' : '显示' }}元数据
                  </Button>
                  <Button
                    @click="scrollToTop"
                    variant="outline"
                    size="sm"
                  >
                    <ArrowUp class="h-4 w-4 mr-1" />
                    回到顶部
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent class="flex-1 min-h-0 p-0">
              <ScrollArea class="h-full w-full">
                <div class="p-6">
                  <div class="space-y-4">
                    <Collapsible
                      v-for="(chunk, index) in chunks"
                      :key="chunk.chunk_id"
                      class="border border-slate-200 dark:border-slate-700 rounded-lg p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                      :open="expandedChunks.has(chunk.chunk_id)"
                      @update:open="(isOpen) => toggleChunkCollapse(chunk.chunk_id, isOpen)"
                    >
                      <!-- 分块头部 -->
                      <CollapsibleTrigger class="flex items-center justify-between w-full mb-3 cursor-pointer">
                        <div class="flex items-center gap-2">
                          <Badge variant="outline" class="text-xs">
                            片段 {{ index + 1 }}
                          </Badge>
                          <span class="text-xs text-slate-500">
                            {{ chunk.content.length }} 字符
                          </span>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          class="text-xs"
                        >
                          <template v-if="expandedChunks.has(chunk.chunk_id)">
                            <ChevronUp class="h-3 w-3 mr-1" />
                            折叠
                          </template>
                          <template v-else>
                            <ChevronDown class="h-3 w-3 mr-1" />
                            展开
                          </template>
                        </Button>
                      </CollapsibleTrigger>

                      <CollapsibleContent>
                        <!-- 分块内容 -->
                        <div class="mb-3">
                          <pre class="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">{{ chunk.content }}</pre>
                        </div>

                        <!-- 元数据（可选显示） -->
                        <div v-if="showMetadata && chunk.metadata" class="border-t border-slate-200 dark:border-slate-700 pt-3">
                          <div class="text-xs font-medium text-slate-600 dark:text-slate-400 mb-2">元数据:</div>
                          <pre class="text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 p-2 rounded overflow-x-auto">{{ JSON.stringify(chunk.metadata, null, 2) }}</pre>
                        </div>

                        <Button
                          @click="copyChunkContent(chunk.content)"
                          variant="ghost"
                          size="sm"
                          class="text-xs mt-2"
                        >
                          <Copy class="h-3 w-3 mr-1" />
                          复制
                        </Button>
                      </CollapsibleContent>
                    </Collapsible>
                  </div>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  FileText,
  Info,
  Database,
  Settings,
  Folder,
  Trash2,
  Eye,
  ArrowUp,
  Copy,
  Hash,
  Clock,
  Loader2,
  AlertTriangle,
  RefreshCw,
  ChevronDown,
  ChevronUp
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger
} from '@/components/ui/collapsible'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { getDocumentInfo, getDocumentChunks } from '@/utils/api'
import type { RAGDocument, KnowledgeBase } from '@/types'

// Props
interface Props {
  isOpen: boolean
  document: RAGDocument | null
  knowledgeBases?: KnowledgeBase[]
}

const props = withDefaults(defineProps<Props>(), {
  knowledgeBases: () => []
})

// Emits
const emit = defineEmits<{
  'update:isOpen': [value: boolean]
  'move': [document: RAGDocument]
  'delete': [docId: string]
}>()

// 响应式状态
const isLoading = ref(false)
const error = ref<string | null>(null)
const documentInfo = ref<any>(null)
const chunks = ref<any[]>([])
const showMetadata = ref(false)
const expandedChunks = ref<Set<string>>(new Set()) // Tracks expanded chunks

// 计算属性
const isOpen = computed({
  get: () => props.isOpen,
  set: (value) => emit('update:isOpen', value)
})

// 监听文档变化
watch(() => props.document, (newDocument) => {
  if (newDocument && props.isOpen) {
    loadDocument()
  }
}, { immediate: true })

// 监听对话框打开状态
watch(() => props.isOpen, (isOpen) => {
  if (isOpen && props.document) {
    loadDocument()
  } else if (!isOpen) {
    clearData()
  }
})

// 加载文档数据
async function loadDocument() {
  if (!props.document) return

  isLoading.value = true
  error.value = null

  try {
    // 并行加载文档信息和分块内容
    const [docInfo, chunksData] = await Promise.all([
      getDocumentInfo(props.document.doc_id),
      getDocumentChunks(props.document.doc_id)
    ])

    // 正确提取API响应中的data字段
    documentInfo.value = docInfo.data || docInfo
    chunks.value = chunksData.data?.chunks || chunksData.chunks || []
    expandedChunks.value = new Set() // Collapse all chunks by default

    console.log('✅ 文档预览数据加载完成:', {
      filename: documentInfo.value.filename,
      chunksCount: chunks.value.length,
      docInfoStructure: docInfo,
      chunksDataStructure: chunksData
    })

  } catch (err) {
    console.error('❌ 加载文档预览数据失败:', err)
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    isLoading.value = false
  }
}

// 清理数据
function clearData() {
  documentInfo.value = null
  chunks.value = []
  error.value = null
  showMetadata.value = false
  expandedChunks.value = new Set() // Reset expanded chunks
}

// 关闭对话框
function closeDialog() {
  isOpen.value = false
}

// 切换元数据显示
function toggleMetadata() {
  showMetadata.value = !showMetadata.value
}

// 滚动到顶部
function scrollToTop() {
  const scrollArea = document.querySelector('.scroll-area-viewport')
  if (scrollArea) {
    scrollArea.scrollTop = 0
  }
}

// 复制分块内容
async function copyChunkContent(content: string) {
  try {
    await navigator.clipboard.writeText(content)
    console.log('✅ 内容已复制到剪贴板')
    // 这里可以添加toast提示
  } catch (err) {
    console.error('❌ 复制失败:', err)
    // 降级方案：使用传统方法复制
    const textArea = document.createElement('textarea')
    textArea.value = content
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
  }
}


// 工具函数
function getFileTypeDisplay(type: string): string {
  const typeMap: Record<string, string> = {
    'application/pdf': 'PDF',
    'image/png': 'PNG',
    'image/jpeg': 'JPG',
    'image/jpg': 'JPG',
    'audio/wav': 'WAV',
    'audio/mp3': 'MP3'
  }
  return typeMap[type] || type.split('/').pop()?.toUpperCase() || '未知'
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateString
  }
}

function toggleChunkCollapse(chunkId: string, isOpen: boolean) {
  if (isOpen) {
    expandedChunks.value.add(chunkId)
  } else {
    expandedChunks.value.delete(chunkId)
  }
}
</script> 