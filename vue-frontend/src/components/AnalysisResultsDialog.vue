<template>
  <Dialog :open="isOpen" @update:open="value => emit('update:isOpen', value)">
    <DialogContent class="sm:max-w-4xl h-[80vh] p-0">
      <div class="flex flex-col h-full">
        <!-- 头部 -->
        <DialogHeader class="p-6 pb-4 max-h-[90vh] border-b border-slate-200 dark:border-slate-700">
          <DialogTitle class="flex items-center gap-3">
            <div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-full">
              <Brain class="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h2 class="text-xl font-semibold">AI 智能分析结果</h2>
              <p class="text-sm text-slate-600 dark:text-slate-400 mt-1">
                已分析 {{ analysisResults.length }} 个文档，请确认归档建议
              </p>
            </div>
          </DialogTitle>
        </DialogHeader>

        <!-- 统计信息 -->
        <div class="px-6 py-4 bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
          <div class="flex items-center gap-6 text-sm">
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 bg-green-500 rounded-full"></div>
              <span class="text-slate-600 dark:text-slate-400">
                成功分析: <span class="font-medium text-green-600">{{ successCount }}</span>
              </span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 bg-purple-500 rounded-full"></div>
              <span class="text-slate-600 dark:text-slate-400">
                新建知识库: <span class="font-medium text-purple-600">{{ newKnowledgeBasesCount }}</span>
              </span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span class="text-slate-600 dark:text-slate-400">
                已有知识库: <span class="font-medium text-blue-600">{{ existingKnowledgeBasesCount }}</span>
              </span>
            </div>
            <div v-if="errorCount > 0" class="flex items-center gap-2">
              <div class="w-3 h-3 bg-red-500 rounded-full"></div>
              <span class="text-slate-600 dark:text-slate-400">
                分析失败: <span class="font-medium text-red-600">{{ errorCount }}</span>
              </span>
            </div>
          </div>
        </div>

        <!-- 分析结果列表 -->
        <ScrollArea class="flex-1 px-6">
          <div class="py-4 space-y-4">
            <div
              v-for="(result, index) in analysisResults"
              :key="index"
              class="group relative"
            >
              <!-- 成功分析的结果 -->
              <div
                v-if="result.success"
                class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm hover:shadow-md transition-all duration-200"
              >
                <!-- 文档头部信息 -->
                <div class="flex items-start justify-between mb-4">
                  <div class="flex items-start gap-3 min-w-0 flex-1">
                    <div class="p-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg flex-shrink-0">
                      <FileText class="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div class="min-w-0 flex-1">
                      <h3 class="font-medium text-slate-900 dark:text-slate-100 truncate">
                        {{ result.fileName }}
                      </h3>
                      <div class="flex items-center gap-2 mt-1">
                        <Badge variant="outline" class="text-xs">
                          {{ result.documentType }}
                        </Badge>
                        <Badge 
                          :variant="result.isNewKnowledgeBase ? 'default' : 'secondary'"
                          class="text-xs"
                        >
                          {{ result.isNewKnowledgeBase ? '新建知识库' : '已有知识库' }}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 状态图标 -->
                  <div class="flex-shrink-0">
                    <div class="p-1 bg-green-100 dark:bg-green-900/30 rounded-full">
                      <Check class="h-4 w-4 text-green-600 dark:text-green-400" />
                    </div>
                  </div>
                </div>

                <!-- 归档信息 -->
                <div class="bg-slate-50 dark:bg-slate-900/50 rounded-lg p-4 mb-4">
                  <div class="flex items-center gap-2 mb-2">
                    <Folder class="h-4 w-4 text-slate-600 dark:text-slate-400" />
                    <span class="text-sm font-medium text-slate-700 dark:text-slate-300">
                      推荐归档至
                    </span>
                  </div>
                  <p class="text-base font-medium text-blue-600 dark:text-blue-400 mb-2">
                    📂 {{ result.knowledgeBaseName }}
                  </p>
                  <p v-if="result.reason" class="text-sm text-slate-600 dark:text-slate-400">
                    💡 {{ result.reason }}
                  </p>
                </div>

                <!-- 文档内容预览 -->
                <div v-if="result.textContent" class="border-t border-slate-200 dark:border-slate-700 pt-4">
                  <div class="flex items-center justify-between mb-3">
                    <span class="text-sm font-medium text-slate-700 dark:text-slate-300">
                      文档内容预览
                    </span>
                    <Button
                      @click="toggleContentExpanded(index)"
                      variant="ghost"
                      size="sm"
                      class="h-6 text-xs"
                    >
                      <ChevronDown 
                        :class="[
                          'h-3 w-3 transition-transform duration-200',
                          expandedContents.has(index) ? 'rotate-180' : ''
                        ]" 
                      />
                      {{ expandedContents.has(index) ? '收起' : '展开' }}
                    </Button>
                  </div>
                  <div 
                    :class="[
                      'bg-slate-100 dark:bg-slate-800 rounded-lg p-3 text-sm text-slate-700 dark:text-slate-300 transition-all duration-200',
                      expandedContents.has(index) ? '' : 'line-clamp-3'
                    ]"
                  >
                    {{ result.textContent }}
                  </div>
                </div>
              </div>

              <!-- 分析失败的结果 -->
              <div
                v-else
                class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-5"
              >
                <div class="flex items-start gap-3">
                  <div class="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg flex-shrink-0">
                    <AlertTriangle class="h-5 w-5 text-red-600 dark:text-red-400" />
                  </div>
                  <div class="flex-1">
                    <h3 class="font-medium text-red-900 dark:text-red-100 mb-1">
                      {{ result.fileName }}
                    </h3>
                    <p class="text-sm text-red-600 dark:text-red-400">
                      ❌ {{ result.error || '分析失败，请稍后重试' }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </ScrollArea>

        <!-- 底部操作栏 -->
        <div class="p-6 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
          <div class="flex justify-between items-center">
            <div class="text-sm text-slate-600 dark:text-slate-400">
              {{ successCount > 0 ? `${successCount} 个文档分析成功，准备归档` : '没有成功分析的文档' }}
            </div>
            
            <div class="flex gap-3">
              <Button 
                variant="outline" 
                @click="emit('reanalyze')"
                class="flex items-center gap-2"
              >
                <RotateCcw class="h-4 w-4" />
                重新分析
              </Button>
            </div>
          </div>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Brain,
  FileText,
  Check,
  AlertTriangle,
  Folder,
  ChevronDown,
  RotateCcw
} from 'lucide-vue-next'

// 类型定义
interface AnalysisResult {
  fileName: string
  knowledgeBaseName: string
  isNewKnowledgeBase: boolean
  reason?: string
  knowledgeBaseId?: string
  documentType: string
  textContent: string
  success: boolean
  error?: string
}

// Props
interface Props {
  isOpen: boolean
  analysisResults: AnalysisResult[]
}

// Emits
interface Emits {
  (e: 'update:isOpen', value: boolean): void
  (e: 'confirm-archive'): void
  (e: 'reanalyze'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式状态
const expandedContents = ref<Set<number>>(new Set())

// 计算属性
const successCount = computed(() => 
  props.analysisResults.filter(result => result.success).length
)

const errorCount = computed(() => 
  props.analysisResults.filter(result => !result.success).length
)

const newKnowledgeBasesCount = computed(() => 
  props.analysisResults.filter(result => result.success && result.isNewKnowledgeBase).length
)

const existingKnowledgeBasesCount = computed(() => 
  props.analysisResults.filter(result => result.success && !result.isNewKnowledgeBase).length
)

// 方法
function toggleContentExpanded(index: number) {
  if (expandedContents.value.has(index)) {
    expandedContents.value.delete(index)
  } else {
    expandedContents.value.add(index)
  }
}
</script>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style> 