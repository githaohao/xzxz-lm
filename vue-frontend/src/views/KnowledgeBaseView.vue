<template>
  <div class="flex h-full bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
    <!-- 知识库列表侧边栏 -->
    <div class="w-80 border-r border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm flex flex-col">
      <!-- 头部 -->
      <div class="p-6 border-b border-slate-200 dark:border-slate-700">
        <div class="flex items-center justify-between mb-4">
          <h1 class="text-xl font-semibold text-slate-900 dark:text-slate-100">
            📚 知识库管理
          </h1>
          <Button
            @click="showCreateDialog = true"
            size="sm"
            class="bg-blue-600 hover:bg-blue-700"
          >
            <Plus class="h-4 w-4 mr-1" />
            新建
          </Button>
        </div>
        
        <!-- 搜索框 -->
        <div class="relative">
          <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            v-model="knowledgeBaseSearch"
            placeholder="搜索知识库..."
            class="pl-10"
          />
        </div>
      </div>

      <!-- 知识库列表 -->
      <ScrollArea class="flex-1 p-4">
        <div class="space-y-2">
          <!-- 全部文档选项 -->
          <div
            :class="[
              'p-4 rounded-lg cursor-pointer transition-all duration-200 group',
              !selectedKnowledgeBase
                ? 'bg-blue-50 dark:bg-blue-950/30 border-2 border-blue-200 dark:border-blue-800'
                : 'hover:bg-slate-50 dark:hover:bg-slate-800/50 border border-slate-200 dark:border-slate-700'
            ]"
            @click="setSelectedKnowledgeBase(null)"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-slate-500 to-slate-600 flex items-center justify-center shadow-sm">
                <FileText class="h-5 w-5 text-white" />
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-slate-900 dark:text-slate-100 truncate">
                  全部文档
                </h3>
                <p class="text-sm text-slate-500 dark:text-slate-400">
                  {{ allDocuments.length }} 个文档
                </p>
              </div>
            </div>
          </div>

          <!-- 未分类文档 -->
          <div
            v-if="uncategorizedDocuments.length > 0"
            :class="[
              'p-4 rounded-lg cursor-pointer transition-all duration-200 group',
              'hover:bg-orange-50 dark:hover:bg-orange-950/30 border border-orange-200 dark:border-orange-700'
            ]"
            @click="showUncategorized = true"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center shadow-sm">
                <AlertTriangle class="h-5 w-5 text-white" />
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-slate-900 dark:text-slate-100 truncate">
                  未分类文档
                </h3>
                <p class="text-sm text-orange-600 dark:text-orange-400">
                  {{ uncategorizedDocuments.length }} 个文档需要分类
                </p>
              </div>
            </div>
          </div>

          <!-- 知识库列表 -->
          <div
            v-for="kb in filteredKnowledgeBases"
            :key="kb.id"
            :class="[
              'p-4 rounded-lg cursor-pointer transition-all duration-200 group',
              selectedKnowledgeBase?.id === kb.id
                ? 'bg-blue-50 dark:bg-blue-950/30 border-2 border-blue-200 dark:border-blue-800'
                : 'hover:bg-slate-50 dark:hover:bg-slate-800/50 border border-slate-200 dark:border-slate-700'
            ]"
            @click="setSelectedKnowledgeBase(kb)"
          >
            <div class="flex items-center gap-3">
              <!-- 知识库图标 -->
              <div 
                :style="{ backgroundColor: kb.color }"
                class="w-10 h-10 rounded-lg flex items-center justify-center shadow-sm"
              >
                <Database class="h-5 w-5 text-white" />
              </div>
              
              <!-- 知识库信息 -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <h3 class="font-medium text-slate-900 dark:text-slate-100 truncate">
                    {{ kb.name }}
                  </h3>
                  <Badge v-if="kb.isDefault" variant="secondary" class="text-xs">
                    默认
                  </Badge>
                </div>
                <p class="text-sm text-slate-500 dark:text-slate-400">
                  {{ knowledgeBaseStats[kb.id]?.totalDocuments || 0 }} 个文档
                  <span v-if="knowledgeBaseStats[kb.id]?.recentlyAdded" class="text-green-600 dark:text-green-400">
                    · {{ knowledgeBaseStats[kb.id].recentlyAdded }} 个新增
                  </span>
                </p>
                <p v-if="kb.description" class="text-xs text-slate-400 dark:text-slate-500 mt-1 truncate">
                  {{ kb.description }}
                </p>
              </div>

              <!-- 操作按钮 -->
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    class="opacity-0 group-hover:opacity-100 transition-opacity"
                    @click.stop
                  >
                    <MoreVertical class="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem @click="editKnowledgeBase(kb)">
                    <Edit2 class="h-4 w-4 mr-2" />
                    编辑
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    v-if="!kb.isDefault"
                    @click="confirmDeleteKnowledgeBase(kb)"
                    class="text-red-600 focus:text-red-600"
                  >
                    <Trash2 class="h-4 w-4 mr-2" />
                    删除
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>

    <!-- 主内容区域 -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- 工具栏 -->
      <div class="p-6 border-b border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div>
              <h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
                {{ selectedKnowledgeBase ? selectedKnowledgeBase.name : '全部文档' }}
              </h2>
              <p class="text-sm text-slate-500 dark:text-slate-400">
                {{ filteredDocuments.length }} 个文档
                <span v-if="selectedDocuments.size > 0" class="text-purple-600 dark:text-purple-400">
                  · 已选择 {{ selectedDocuments.size }} 个
                </span>
              </p>
            </div>
            
            <!-- 快速统计 -->
            <div v-if="selectedKnowledgeBase && knowledgeBaseStats[selectedKnowledgeBase.id]" class="flex items-center gap-4 text-sm text-slate-500">
              <span class="flex items-center gap-1">
                <Hash class="h-4 w-4" />
                {{ knowledgeBaseStats[selectedKnowledgeBase.id].totalChunks }} 个片段
              </span>
              <span class="flex items-center gap-1">
                <HardDrive class="h-4 w-4" />
                {{ formatFileSize(knowledgeBaseStats[selectedKnowledgeBase.id].totalSize) }}
              </span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex items-center gap-2">
            <!-- 搜索和过滤 -->
            <div class="flex items-center gap-2">
              <div class="relative">
                <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  v-model="documentSearch"
                  placeholder="搜索文档..."
                  class="pl-10 w-64"
                />
              </div>
              
              <Button
                @click="showFilterDialog = true"
                variant="outline"
                size="sm"
              >
                <Filter class="h-4 w-4 mr-1" />
                筛选
              </Button>
            </div>

            <!-- 批量操作 -->
            <div v-if="selectedDocuments.size > 0" class="flex items-center gap-2">
              <Select v-model="batchMoveTarget" @update:model-value="(value: any) => value && typeof value === 'string' && handleBatchMove(value)">
                <SelectTrigger class="w-48">
                  <SelectValue placeholder="移动到知识库..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem
                    v-for="kb in knowledgeBases"
                    :key="kb.id"
                    :value="kb.id"
                  >
                    {{ kb.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
              
              <Button
                @click="handleBatchDelete"
                variant="destructive"
                size="sm"
              >
                <Trash2 class="h-4 w-4 mr-1" />
                删除
              </Button>
            </div>

            <Button
              @click="refreshDocuments"
              :disabled="isLoading"
              variant="outline"
              size="sm"
            >
              <RefreshCw :class="['h-4 w-4', isLoading ? 'animate-spin' : '']" />
            </Button>
          </div>
        </div>
      </div>

      <!-- 文档列表 -->
      <ScrollArea class="flex-1 p-6">
        <div v-if="isLoading && !hasDocuments" class="flex flex-col items-center justify-center py-20">
          <Loader2 class="h-12 w-12 animate-spin text-slate-400 mb-4" />
          <p class="text-slate-500">正在加载文档...</p>
        </div>

        <div v-else-if="!hasDocuments" class="flex flex-col items-center justify-center py-20">
          <FileText class="h-20 w-20 text-slate-300 dark:text-slate-600 mb-6" />
          <h3 class="text-lg font-medium text-slate-700 dark:text-slate-300 mb-2">
            {{ selectedKnowledgeBase ? '该知识库还没有文档' : '还没有任何文档' }}
          </h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mb-6">
            在聊天界面上传文件即可自动添加到知识库
          </p>
        </div>

        <div v-else-if="filteredDocuments.length === 0" class="flex flex-col items-center justify-center py-20">
          <Search class="h-20 w-20 text-slate-300 dark:text-slate-600 mb-6" />
          <h3 class="text-lg font-medium text-slate-700 dark:text-slate-300 mb-2">
            未找到匹配的文档
          </h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">
            尝试修改搜索条件或清除筛选
          </p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <div
            v-for="document in filteredDocuments"
            :key="document.doc_id"
            :class="[
              'group p-4 rounded-lg border cursor-pointer transition-all duration-200',
              selectedDocuments.has(document.doc_id)
                ? 'border-purple-300 bg-purple-50 dark:border-purple-700 dark:bg-purple-950/30 shadow-md transform scale-105'
                : 'border-slate-200 hover:border-slate-300 dark:border-slate-700 dark:hover:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800/50 hover:shadow-lg'
            ]"
            @click="toggleDocument(document.doc_id)"
          >
            <!-- 选择指示器 -->
            <div class="flex items-start justify-between mb-3">
              <div
                :class="[
                  'w-5 h-5 rounded border-2 flex items-center justify-center transition-all duration-200',
                  selectedDocuments.has(document.doc_id)
                    ? 'border-purple-500 bg-purple-500 scale-110'
                    : 'border-slate-300 dark:border-slate-600 group-hover:border-purple-400'
                ]"
              >
                <Check v-if="selectedDocuments.has(document.doc_id)" class="h-3 w-3 text-white" />
              </div>
              
              <!-- 文档操作 -->
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    class="opacity-0 group-hover:opacity-100 transition-opacity p-1 h-7 w-7"
                    @click.stop
                  >
                    <MoreVertical class="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem @click="previewDocument(document)">
                    <Eye class="h-4 w-4 mr-2" />
                    预览
                  </DropdownMenuItem>
                  <DropdownMenuItem @click="showMoveDialog(document)">
                    <Folder class="h-4 w-4 mr-2" />
                    移动
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    @click="deleteDocument(document.doc_id)"
                    class="text-red-600 focus:text-red-600"
                  >
                    <Trash2 class="h-4 w-4 mr-2" />
                    删除
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            <!-- 文档信息 -->
            <div class="space-y-3">
              <!-- 文件图标和类型 -->
              <div class="flex items-center gap-2">
                <FileText class="h-8 w-8 text-blue-500" />
                <Badge variant="outline" class="text-xs">
                  {{ getFileTypeDisplay(document.file_type) }}
                </Badge>
              </div>

              <!-- 文件名 -->
              <h3 class="font-medium text-slate-900 dark:text-slate-100 truncate" :title="document.filename">
                {{ document.filename }}
              </h3>

              <!-- 统计信息 -->
              <div class="space-y-1 text-xs text-slate-500 dark:text-slate-400">
                <div class="flex items-center justify-between">
                  <span class="flex items-center gap-1">
                    <Hash class="h-3 w-3" />
                    {{ document.chunk_count }} 片段
                  </span>
                  <span>{{ formatFileSize(document.total_length) }}</span>
                </div>
                <div class="flex items-center gap-1">
                  <Clock class="h-3 w-3" />
                  {{ formatDate(document.created_at) }}
                </div>
              </div>

              <!-- 所属知识库 -->
              <div class="flex flex-wrap gap-1">
                <Badge
                  v-for="kb in getDocumentKnowledgeBases(document.doc_id)"
                  :key="kb.id"
                  variant="secondary"
                  class="text-xs px-1.5 py-0.5"
                  :style="{ backgroundColor: `${kb.color}20`, borderColor: kb.color }"
                >
                  {{ kb.name }}
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  </div>

  <!-- 创建知识库对话框 -->
  <Dialog v-model:open="showCreateDialog">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>{{ editingKnowledgeBase ? '编辑知识库' : '创建新知识库' }}</DialogTitle>
        <DialogDescription>
          {{ editingKnowledgeBase ? '修改知识库信息' : '创建一个新的知识库来组织你的文档' }}
        </DialogDescription>
      </DialogHeader>
      
      <div class="space-y-4">
        <div>
          <Label for="kb-name">知识库名称</Label>
          <Input
            id="kb-name"
            v-model="newKnowledgeBase.name"
            placeholder="输入知识库名称"
            class="mt-1"
          />
        </div>
        
        <div>
          <Label for="kb-description">描述（可选）</Label>
          <Textarea
            id="kb-description"
            v-model="newKnowledgeBase.description"
            placeholder="简单描述这个知识库的用途"
            class="mt-1"
            rows="3"
          />
        </div>
        
        <div>
          <Label>颜色</Label>
          <div class="flex gap-2 mt-2">
            <button
              v-for="color in availableColors"
              :key="color"
              :style="{ backgroundColor: color }"
              :class="[
                'w-8 h-8 rounded-lg border-2 transition-all duration-200',
                newKnowledgeBase.color === color
                  ? 'border-slate-900 dark:border-white scale-110'
                  : 'border-slate-300 dark:border-slate-600 hover:scale-105'
              ]"
              @click="newKnowledgeBase.color = color"
            />
          </div>
        </div>
      </div>

      <div class="flex justify-end gap-2 mt-6">
        <Button variant="outline" @click="showCreateDialog = false">
          取消
        </Button>
        <Button @click="handleCreateKnowledgeBase">
          {{ editingKnowledgeBase ? '保存' : '创建' }}
        </Button>
      </div>
    </DialogContent>
  </Dialog>

  <!-- 未分类文档对话框 -->
  <Dialog v-model:open="showUncategorized">
    <DialogContent class="max-w-4xl max-h-[80vh] flex flex-col">
      <DialogHeader>
        <DialogTitle>未分类文档</DialogTitle>
        <DialogDescription>
          以下文档还未添加到任何知识库，建议将它们分类整理
        </DialogDescription>
      </DialogHeader>
      
      <ScrollArea class="flex-1 mt-4">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="document in uncategorizedDocuments"
            :key="document.doc_id"
            class="p-3 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
          >
            <div class="flex items-center gap-2 mb-2">
              <FileText class="h-5 w-5 text-blue-500" />
              <span class="text-sm font-medium truncate">{{ document.filename }}</span>
            </div>
            <div class="text-xs text-slate-500 mb-3">
              {{ document.chunk_count }} 片段 · {{ formatFileSize(document.total_length) }}
            </div>
            <Select @update:model-value="(value: any) => value && typeof value === 'string' && addToKnowledgeBase(document.doc_id, value)">
              <SelectTrigger class="h-8 text-xs">
                <SelectValue placeholder="选择知识库..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="kb in knowledgeBases"
                  :key="kb.id"
                  :value="kb.id"
                >
                  {{ kb.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </ScrollArea>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import {
  Plus,
  Search,
  Database,
  FileText,
  MoreVertical,
  Edit2,
  Trash2,
  Hash,
  Clock,
  Check,
  Eye,
  Folder,
  Filter,
  RefreshCw,
  Loader2,
  AlertTriangle,
  HardDrive
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import { deleteDocument as apiDeleteDocument } from '@/utils/api'
import type { KnowledgeBase, RAGDocument } from '@/types'

// Store
const knowledgeBaseStore = useKnowledgeBaseStore()
const {
  knowledgeBases,
  allDocuments,
  selectedKnowledgeBase,
  selectedDocuments,
  isLoading,
  uncategorizedDocuments,
  knowledgeBaseStats,
  filteredDocuments
} = storeToRefs(knowledgeBaseStore)

const {
  initialize,
  fetchAllDocuments,
  setSelectedKnowledgeBase,
  createKnowledgeBase,
  updateKnowledgeBase,
  deleteKnowledgeBase,
  toggleDocument,
  clearSelection,
  updateSearchOptions,
  addDocumentsToKnowledgeBase,
  moveDocuments,
  getDocumentKnowledgeBases,
  formatFileSize,
  formatDate,
  availableColors
} = knowledgeBaseStore

// 本地状态
const knowledgeBaseSearch = ref('')
const documentSearch = ref('')
const showCreateDialog = ref(false)
const showUncategorized = ref(false)
const showFilterDialog = ref(false)
const editingKnowledgeBase = ref<KnowledgeBase | null>(null)
const batchMoveTarget = ref('')

// 新建/编辑知识库表单
const newKnowledgeBase = ref({
  name: '',
  description: '',
  color: availableColors[0]
})

// 计算属性
const hasDocuments = computed(() => allDocuments.value.length > 0)

const filteredKnowledgeBases = computed(() => {
  if (!knowledgeBaseSearch.value) return knowledgeBases.value
  
  const query = knowledgeBaseSearch.value.toLowerCase()
  return knowledgeBases.value.filter(kb =>
    kb.name.toLowerCase().includes(query) ||
    (kb.description && kb.description.toLowerCase().includes(query))
  )
})

// 监听文档搜索
watch(documentSearch, (value) => {
  updateSearchOptions({ query: value })
})

// 生命周期
onMounted(async () => {
  await initialize()
})

// 文件类型显示
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

// 刷新文档
async function refreshDocuments() {
  await fetchAllDocuments()
}

// 创建/编辑知识库
function editKnowledgeBase(kb: KnowledgeBase) {
  editingKnowledgeBase.value = kb
  newKnowledgeBase.value = {
    name: kb.name,
    description: kb.description || '',
    color: kb.color || availableColors[0]
  }
  showCreateDialog.value = true
}

async function handleCreateKnowledgeBase() {
  try {
    if (editingKnowledgeBase.value) {
      // 编辑现有知识库
      await updateKnowledgeBase(editingKnowledgeBase.value.id, newKnowledgeBase.value)
    } else {
      // 创建新知识库
      const kb = await createKnowledgeBase(newKnowledgeBase.value)
      setSelectedKnowledgeBase(kb)
    }
    
    // 重置表单
    newKnowledgeBase.value = {
      name: '',
      description: '',
      color: availableColors[0]
    }
    editingKnowledgeBase.value = null
    showCreateDialog.value = false
  } catch (error) {
    console.error('操作失败:', error)
    alert('操作失败，请重试')
  }
}

// 删除知识库
async function confirmDeleteKnowledgeBase(kb: KnowledgeBase) {
  if (confirm(`确定要删除知识库"${kb.name}"吗？删除后无法恢复。`)) {
    await deleteKnowledgeBase(kb.id)
  }
}

// 批量操作
async function handleBatchMove(targetKbId: string) {
  if (!targetKbId || selectedDocuments.value.size === 0) return
  
  try {
    const docIds = Array.from(selectedDocuments.value)
    await moveDocuments(docIds, targetKbId, selectedKnowledgeBase.value?.id)
    clearSelection()
    batchMoveTarget.value = ''
  } catch (error) {
    console.error('移动文档失败:', error)
    alert('移动文档失败，请重试')
  }
}

async function handleBatchDelete() {
  if (selectedDocuments.value.size === 0) return
  
  const count = selectedDocuments.value.size
  if (confirm(`确定要删除选中的 ${count} 个文档吗？删除后无法恢复。`)) {
    try {
      const docIds = Array.from(selectedDocuments.value)
      await Promise.all(docIds.map(docId => apiDeleteDocument(docId)))
      
      // 重新获取文档列表
      await fetchAllDocuments()
      clearSelection()
    } catch (error) {
      console.error('删除文档失败:', error)
      alert('删除文档失败，请重试')
    }
  }
}

// 文档操作
function previewDocument(document: RAGDocument) {
  // TODO: 实现文档预览功能
  console.log('预览文档:', document.filename)
}

function showMoveDialog(document: RAGDocument) {
  // TODO: 实现文档移动对话框
  console.log('移动文档:', document.filename)
}

async function deleteDocument(docId: string) {
  if (confirm('确定要删除这个文档吗？删除后无法恢复。')) {
    try {
      await apiDeleteDocument(docId)
      await fetchAllDocuments()
    } catch (error) {
      console.error('删除文档失败:', error)
      alert('删除文档失败，请重试')
    }
  }
}

// 将未分类文档添加到知识库
async function addToKnowledgeBase(docId: string, kbId: string) {
  try {
    await addDocumentsToKnowledgeBase(kbId, [docId])
    // 刷新未分类列表
    await fetchAllDocuments()
  } catch (error) {
    console.error('添加文档到知识库失败:', error)
    alert('添加失败，请重试')
  }
}
</script> 