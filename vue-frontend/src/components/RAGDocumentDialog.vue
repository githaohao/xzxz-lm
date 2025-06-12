<template>
  <Dialog v-model:open="isOpen">
    <DialogContent class="max-w-4xl h-[650px] flex flex-col p-4 gap-3">
      <DialogHeader class="pb-3">
        <DialogTitle class="flex items-center gap-2 text-lg">
          <FileText class="h-5 w-5 text-blue-500" />
          📚 当前对话文档管理
        </DialogTitle>
        <DialogDescription class="text-sm mt-1">
          管理当前对话的RAG文档，支持搜索、选择和删除操作
        </DialogDescription>
      </DialogHeader>

      <!-- 工具栏 -->
      <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 pb-3 mb-3">
        <!-- 美化的搜索框 -->
        <div class="flex-1 max-w-md">
          <div class="relative group">
            <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
            <Input
              v-model="searchQuery"
              placeholder="搜索文档..."
              class="pl-10 pr-10 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 shadow-sm transition-all duration-200 hover:shadow-md focus:shadow-lg"
            />
            <!-- 清除搜索按钮 -->
            <Button
              v-if="searchQuery"
              @click="searchQuery = ''"
              variant="ghost"
              size="sm"
              class="absolute right-1 top-1/2 transform -translate-y-1/2 h-7 w-7 p-0 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-full"
            >
              <X class="h-3 w-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300" />
            </Button>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="flex items-center gap-2">
          <Button
            @click="refreshDocuments"
            :disabled="isLoading"
            variant="outline"
            size="sm"
          >
            <RefreshCw :class="['h-4 w-4', isLoading ? 'animate-spin' : '']" />
            刷新
          </Button>
          <Button
            v-if="selectedCount > 0"
            @click="handleBatchRemove"
            variant="destructive"
            size="sm"
          >
            <Trash2 class="h-4 w-4 mr-1" />
            删除 ({{ selectedCount }})
          </Button>
        </div>
      </div>

      <!-- 统计信息 -->
      <div class="flex items-center justify-between text-sm text-slate-500 dark:text-slate-400 py-1 mb-2">
        <div>
          {{ filteredDocuments.length }} / {{ documentStats.totalDocuments }} 个文档
          <span v-if="selectedCount > 0" class="text-purple-600 dark:text-purple-400">
            (已选 {{ selectedCount }})
          </span>
          <span v-if="conversationStore.currentConversation" class="ml-2 text-blue-600 dark:text-blue-400">
            • {{ conversationStore.currentConversation.title }}
          </span>
        </div>
        
        <div v-if="searchQuery" class="text-xs bg-yellow-100 dark:bg-yellow-900/30 px-2 py-1 rounded-full">
          搜索: "{{ searchQuery }}"
        </div>
      </div>

      <!-- 修复的文档列表滚动区域 -->
      <div class="h-[400px] overflow-hidden">
        <ScrollArea class="h-full w-full">
          <div class="space-y-3 pr-2 pb-2">
            <!-- 加载状态 -->
            <div v-if="isLoading && !hasDocuments" class="flex flex-col items-center justify-center py-12">
              <Loader2 class="h-8 w-8 animate-spin mx-auto text-slate-400 mb-3" />
              <p class="text-sm text-slate-500">加载文档中...</p>
            </div>

            <!-- 空状态 -->
            <div v-else-if="!hasDocuments" class="flex flex-col items-center justify-center py-12">
              <FileText class="h-16 w-16 mx-auto text-slate-300 dark:text-slate-600 mb-4" />
              <p class="text-sm text-slate-500 dark:text-slate-400 mb-2">
                当前对话还没有文档
              </p>
              <p class="text-xs text-slate-400 dark:text-slate-500">
                在聊天界面上传文件即可添加文档
              </p>
            </div>

            <!-- 搜索无结果 -->
            <div v-else-if="searchQuery && filteredDocuments.length === 0" class="flex flex-col items-center justify-center py-12">
              <Search class="h-16 w-16 mx-auto text-slate-300 dark:text-slate-600 mb-4" />
              <p class="text-sm text-slate-500 dark:text-slate-400 mb-2">
                未找到匹配的文档
              </p>
              <p class="text-xs text-slate-400 dark:text-slate-500">
                尝试修改搜索关键词
              </p>
            </div>
            <!-- 文档项 -->
            <div
              v-for="document in filteredDocuments"
              :key="document.doc_id"
              :class="[
                'group p-4 rounded-lg border cursor-pointer transition-all duration-200',
                selectedDocuments.has(document.doc_id)
                  ? 'border-purple-300 bg-purple-50 dark:border-purple-700 dark:bg-purple-950/30 shadow-md'
                  : 'border-slate-200 hover:border-slate-300 dark:border-slate-700 dark:hover:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800/50 hover:shadow-sm'
              ]"
              @click="toggleDocument(document.doc_id)"
            >
              <div class="flex items-start gap-4">
                <!-- 选择框 -->
                <div class="flex-shrink-0 mt-1">
                  <div
                    :class="[
                      'w-5 h-5 rounded border-2 flex items-center justify-center transition-all duration-200',
                      selectedDocuments.has(document.doc_id)
                        ? 'border-purple-500 bg-purple-500 scale-110'
                        : 'border-slate-300 dark:border-slate-600 hover:border-purple-400'
                    ]"
                  >
                    <Check v-if="selectedDocuments.has(document.doc_id)" class="h-3 w-3 text-white" />
                  </div>
                </div>

                <!-- 文档信息 -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-3 mb-2">
                    <FileText class="h-5 w-5 text-slate-500 dark:text-slate-400 flex-shrink-0" />
                    <h3 class="font-medium text-slate-900 dark:text-slate-100 truncate">
                      {{ highlightSearchTerm(document.filename, searchQuery) }}
                    </h3>
                  </div>
                  
                  <div class="space-y-2">
                    <div class="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
                      <Badge variant="secondary" class="text-xs px-2 py-1">
                        {{ getFileTypeDisplay(document.file_type) }}
                      </Badge>
                      <span class="flex items-center gap-1">
                        <Hash class="h-3 w-3" />
                        {{ document.chunk_count }} 个片段
                      </span>
                      <span class="flex items-center gap-1">
                        <Clock class="h-3 w-3" />
                        {{ formatCreateTime(document.created_at) }}
                      </span>
                    </div>
                    
                    <div class="text-sm text-slate-600 dark:text-slate-300">
                      文档大小: {{ formatDocumentSize(document.total_length) }}
                    </div>
                  </div>
                </div>

                <!-- 操作按钮 -->
                <div class="flex-shrink-0 flex items-center gap-1">
                  <Button
                    @click.stop="handlePreviewDocument(document)"
                    variant="ghost"
                    size="sm"
                    class="opacity-0 group-hover:opacity-100 transition-opacity"
                    title="预览文档"
                  >
                    <Eye class="h-4 w-4" />
                  </Button>
                  <Button
                    @click.stop="handleRemoveFromConversation(document.doc_id)"
                    variant="ghost"
                    size="sm"
                    class="opacity-0 group-hover:opacity-100 transition-opacity text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                    title="删除文档"
                  >
                    <X class="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </ScrollArea>
      </div>

      <!-- 底部操作栏 -->
      <div v-if="hasDocuments" class="flex items-center justify-between border-t border-slate-200 dark:border-slate-700 pt-4">
        <div class="flex items-center gap-4 text-sm">
          <Button
            @click="clearSelection"
            :disabled="selectedCount === 0"
            variant="ghost"
            size="sm"
          >
            清除选择
          </Button>
          <Button
            @click="selectAll"
            :disabled="selectedCount === filteredDocuments.length"
            variant="ghost"
            size="sm"
          >
            全选
          </Button>
          <Button
            @click="selectFiltered"
            :disabled="filteredDocuments.length === 0 || selectedCount === filteredDocuments.length"
            variant="ghost"
            size="sm"
          >
            选择搜索结果
          </Button>
        </div>
        
        <div class="text-sm text-slate-500 dark:text-slate-400">
          <span v-if="selectedCount > 0" class="text-purple-600 dark:text-purple-400 font-medium">
            已选择 {{ selectedCount }} 个文档
          </span>
          <span v-else>
            点击文档可选择，支持批量操作
          </span>
        </div>
        <!-- 确认按钮 -->
        <Button
          @click="isOpen = false"
          variant="default"
          size="sm"
        >
          确认
        </Button>
      </div>
    </DialogContent>
  </Dialog>

  <!-- 删除单个文档确认对话框 -->
  <ConfirmDialog
    v-model:open="showDeleteDocDialog"
    type="danger"
    title="移除文档"
    description="确定要从当前对话中移除这个文档吗？"
    warning-text="此操作会将文档从对话的知识库中移除，但不会删除原始文档"
    confirm-text="确认移除"
    :confirm-icon="Trash2"
    :loading="isDeleting"
    @confirm="confirmDeleteDocument"
  />

  <!-- 批量删除文档确认对话框 -->
  <ConfirmDialog
    v-model:open="showBatchDeleteDialog"
    type="danger"
    title="批量移除文档"
    description="确定要从当前对话中移除选中的文档吗？"
    :details="`已选择 ${selectedCount} 个文档`"
    warning-text="此操作会将这些文档从对话的知识库中移除，但不会删除原始文档"
    confirm-text="确认移除"
    :confirm-icon="Trash2"
    :loading="isDeleting"
    @confirm="confirmBatchDelete"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import {
  RefreshCw,
  Trash2,
  FileText,
  Loader2,
  Check,
  X,
  Search,
  Eye,
  Hash,
  Clock
} from 'lucide-vue-next'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useRAGStore } from '@/stores/rag'
import { useConversationStore } from '@/stores/conversation'
import type { RAGDocument } from '@/types'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'

// Props
interface Props {
  open?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  open: false
})

// Emits
const emit = defineEmits<{
  'update:open': [value: boolean]
  'preview-document': [document: RAGDocument]
}>()

// State
const isOpen = ref(props.open)
const searchQuery = ref('')

// 确认对话框状态
const showDeleteDocDialog = ref(false)
const showBatchDeleteDialog = ref(false)
const deletingDocumentId = ref<string | null>(null)
const isDeleting = ref(false)

// Stores
const ragStore = useRAGStore()
const conversationStore = useConversationStore()

const {
  documents,
  selectedDocuments,
  isLoading,
  hasDocuments,
  selectedCount,
  documentStats
} = storeToRefs(ragStore)

const {
  fetchDocuments,
  setCurrentConversationDocuments,
  toggleDocument,
  clearSelection,
  selectAll,
  formatDocumentSize,
  formatCreateTime
} = ragStore

// 当前对话的RAG文档
const { currentConversationRagDocs } = storeToRefs(conversationStore)

// 监听外部 open 状态变化
watch(() => props.open, (newVal) => {
  isOpen.value = newVal
})

// 监听内部 open 状态变化并向外发射
watch(isOpen, (newVal) => {
  emit('update:open', newVal)
})

// 过滤后的文档列表
const filteredDocuments = computed(() => {
  if (!searchQuery.value) {
    return documents.value
  }
  
  const query = searchQuery.value.toLowerCase()
  return documents.value.filter(doc => 
    doc.filename.toLowerCase().includes(query) ||
    doc.file_type.toLowerCase().includes(query) ||
    getFileTypeDisplay(doc.file_type).toLowerCase().includes(query)
  )
})

// 监听当前对话的文档变化
watch(currentConversationRagDocs, (newDocs) => {
  console.log('🔍 RAG文档数据变化:', newDocs)
  setCurrentConversationDocuments(newDocs)
}, { immediate: true })

// 监听对话切换
watch(() => conversationStore.currentConversation, () => {
  if (conversationStore.currentConversation) {
    setCurrentConversationDocuments(currentConversationRagDocs.value)
  }
}, { immediate: true })

// 刷新文档列表
async function refreshDocuments() {
  await fetchDocuments()
}

// 从对话中删除文档
function handleRemoveFromConversation(docId: string) {
  if (!conversationStore.currentConversation) return
  deletingDocumentId.value = docId
  showDeleteDocDialog.value = true
}

async function confirmDeleteDocument() {
  if (!deletingDocumentId.value || !conversationStore.currentConversation) return
  
  isDeleting.value = true
  try {
    conversationStore.removeRagDocumentFromConversation(conversationStore.currentConversation.id, deletingDocumentId.value)
    showDeleteDocDialog.value = false
    deletingDocumentId.value = null
  } catch (error) {
    console.error('删除文档失败:', error)
  } finally {
    isDeleting.value = false
  }
}

// 批量删除文档
function handleBatchRemove() {
  if (!conversationStore.currentConversation || selectedCount.value === 0) return
  showBatchDeleteDialog.value = true
}

async function confirmBatchDelete() {
  if (!conversationStore.currentConversation || selectedCount.value === 0) return
  
  isDeleting.value = true
  try {
    const docIds = Array.from(selectedDocuments.value)
    docIds.forEach(docId => {
      conversationStore.removeRagDocumentFromConversation(conversationStore.currentConversation!.id, docId)
    })
    showBatchDeleteDialog.value = false
  } catch (error) {
    console.error('批量删除文档失败:', error)
  } finally {
    isDeleting.value = false
  }
}

// 预览文档
function handlePreviewDocument(document: RAGDocument) {
  emit('preview-document', document)
}

// 选择搜索结果
function selectFiltered() {
  filteredDocuments.value.forEach(doc => {
    selectedDocuments.value.add(doc.doc_id)
  })
}

// 获取文件类型显示名称
function getFileTypeDisplay(fileType: string): string {
  const typeMap: Record<string, string> = {
    'application/pdf': 'PDF',
    'image/png': 'PNG',
    'image/jpg': 'JPG',
    'image/jpeg': 'JPEG',
  }
  return typeMap[fileType] || 'File'
}

// 高亮搜索词
function highlightSearchTerm(text: string, searchTerm: string): string {
  if (!searchTerm) return text
  
  const regex = new RegExp(`(${searchTerm})`, 'gi')
  return text.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-800">$1</mark>')
}

// 组件挂载时获取文档列表
onMounted(() => {
  fetchDocuments()
})
</script>

<style scoped>
/* 搜索高亮样式 */
:deep(mark) {
  background-color: rgb(254 240 138); /* yellow-200 */
  border-radius: 0.125rem;
  padding: 0 0.125rem;
}

:deep(.dark mark) {
  background-color: rgb(133 77 14); /* yellow-800 */
}

.group:hover .group-hover\:opacity-100 {
  opacity: 1;
}
</style>
