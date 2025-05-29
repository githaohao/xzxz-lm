<template>
  <div class="h-full flex flex-col bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700">
    <!-- 标题栏 -->
    <div class="p-4 border-b border-slate-200 dark:border-slate-700">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
          📚 当前对话文档
        </h2>
        <div class="flex items-center gap-2">
          <button
            @click="refreshDocuments"
            :disabled="isLoading"
            class="p-1.5 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <RefreshCw :class="['h-4 w-4', isLoading ? 'animate-spin' : '']" />
          </button>
          <button
            v-if="selectedCount > 0"
            @click="handleBatchRemove"
            class="p-1.5 rounded-md hover:bg-red-100 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 transition-colors"
          >
            <Trash2 class="h-4 w-4" />
          </button>
        </div>
      </div>
      
      <!-- 统计信息 -->
      <div class="mt-2 text-sm text-slate-500 dark:text-slate-400">
        {{ documentStats.totalDocuments }} 个文档
        <span v-if="selectedCount > 0" class="text-purple-600 dark:text-purple-400">
          (已选 {{ selectedCount }})
        </span>
        <span v-if="conversationStore.currentConversation" class="ml-2 text-blue-600 dark:text-blue-400">
          • {{ conversationStore.currentConversation.title }}
        </span>
      </div>
    </div>

    <!-- 文档列表 -->
    <ScrollArea class="flex-1">
      <div class="p-2 space-y-2">
        <!-- 加载状态 -->
        <div v-if="isLoading && !hasDocuments" class="p-4 text-center">
          <Loader2 class="h-6 w-6 animate-spin mx-auto text-slate-400" />
          <p class="text-sm text-slate-500 mt-2">加载文档中...</p>
        </div>

        <!-- 空状态 -->
        <div v-else-if="!hasDocuments" class="p-4 text-center">
          <FileText class="h-12 w-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
          <p class="text-sm text-slate-500 dark:text-slate-400 mb-3">
            当前对话还没有文档
          </p>
          <p class="text-xs text-slate-400 dark:text-slate-500">
            在聊天界面上传文件即可添加文档
          </p>
        </div>

        <!-- 文档项 -->
        <div
          v-for="document in documents"
          :key="document.doc_id"
          :class="[
            'p-3 rounded-lg border cursor-pointer transition-all duration-200',
            selectedDocuments.has(document.doc_id)
              ? 'border-purple-300 bg-purple-50 dark:border-purple-700 dark:bg-purple-950/30'
              : 'border-slate-200 hover:border-slate-300 dark:border-slate-700 dark:hover:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800/50'
          ]"
          @click="toggleDocument(document.doc_id)"
        >
          <div class="flex items-start gap-3">
            <!-- 选择框 -->
            <div class="flex-shrink-0 mt-0.5">
              <div
                :class="[
                  'w-4 h-4 rounded border-2 flex items-center justify-center transition-colors',
                  selectedDocuments.has(document.doc_id)
                    ? 'border-purple-500 bg-purple-500'
                    : 'border-slate-300 dark:border-slate-600'
                ]"
              >
                <Check v-if="selectedDocuments.has(document.doc_id)" class="h-3 w-3 text-white" />
              </div>
            </div>

            <!-- 文档信息 -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <FileText class="h-4 w-4 text-slate-500 dark:text-slate-400 flex-shrink-0" />
                <p class="font-medium text-slate-900 dark:text-slate-100 truncate text-sm">
                  {{ document.filename }}
                </p>
              </div>
              
              <div class="space-y-1">
                <div class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <Badge variant="secondary" class="text-xs px-1.5 py-0.5">
                    {{ getFileTypeDisplay(document.file_type) }}
                  </Badge>
                  <span>{{ document.chunk_count }} 个片段</span>
                </div>
                
                <div class="text-xs text-slate-500 dark:text-slate-400">
                  {{ formatDocumentSize(document.total_length) }} • {{ formatCreateTime(document.created_at) }}
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="flex-shrink-0">
              <button
                @click.stop="handleRemoveFromConversation(document.doc_id)"
                class="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/20 text-red-500 dark:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                title="从对话中删除"
              >
                <X class="h-3 w-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </ScrollArea>

    <!-- 底部操作栏 -->
    <div v-if="hasDocuments" class="p-3 border-t border-slate-200 dark:border-slate-700">
      <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
        <div class="flex items-center gap-3">
          <button
            @click="clearSelection"
            :disabled="selectedCount === 0"
            class="hover:text-slate-700 dark:hover:text-slate-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            清除选择
          </button>
          <button
            @click="selectAll"
            :disabled="selectedCount === documents.length"
            class="hover:text-slate-700 dark:hover:text-slate-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            全选
          </button>
        </div>
        
        <div v-if="selectedCount > 0" class="text-purple-600 dark:text-purple-400">
          已选 {{ selectedCount }} 个
        </div>
      </div>
    </div>
  </div>
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
  X
} from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useRAGStore } from '@/stores/rag'
import { useConversationStore } from '@/stores/conversation'

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

// 监听当前对话的文档变化
watch(currentConversationRagDocs, (newDocs) => {
  setCurrentConversationDocuments(newDocs)
}, { immediate: true })

// 监听对话切换
watch(() => conversationStore.currentConversation, () => {
  // 对话切换时重新设置文档
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
  if (conversationStore.currentConversation && confirm('确定要删除这个文档吗？删除后无法恢复。')) {
    conversationStore.removeRagDocumentFromConversation(conversationStore.currentConversation.id, docId)
  }
}

// 批量删除文档
function handleBatchRemove() {
  if (conversationStore.currentConversation && confirm(`确定要删除选中的 ${selectedCount.value} 个文档吗？删除后无法恢复。`)) {
    const docIds = Array.from(selectedDocuments.value)
    docIds.forEach(docId => {
      conversationStore.removeRagDocumentFromConversation(conversationStore.currentConversation!.id, docId)
    })
  }
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

// 组件挂载时获取文档列表
onMounted(() => {
  fetchDocuments()
})
</script>

<style scoped>
.group:hover .group-hover\:opacity-100 {
  opacity: 1;
}
</style>