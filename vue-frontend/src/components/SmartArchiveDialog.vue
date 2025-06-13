<template>
  <Dialog :open="isOpen" @update:open="value => emit('update:isOpen', value)">
    <DialogContent class="sm:max-w-2xl">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2">
          <Sparkles class="h-5 w-5 text-blue-500" />
          智能文档归档
        </DialogTitle>
        <DialogDescription>
          上传文档并使用AI智能分析，自动归档到合适的知识库中
        </DialogDescription>
      </DialogHeader>

      <div class="space-y-6 py-4">
        <!-- 文件上传区域 -->
        <div class="space-y-4">
          <Label class="text-sm font-medium">选择文档</Label>
          
          <!-- 文件拖拽上传区域 -->
          <div
            @drop="handleDrop"
            @dragover.prevent
            @dragenter.prevent
            :class="[
              'border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer',
              isDragOver 
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/20' 
                : 'border-slate-300 dark:border-slate-600 hover:border-blue-400'
            ]"
            @click="triggerFileSelect"
            @dragenter="isDragOver = true"
            @dragleave="isDragOver = false"
          >
            <input
              ref="fileInputRef"
              type="file"
              multiple
              accept=".pdf,.png,.jpg,.jpeg,.txt,.doc,.docx"
              class="hidden"
              @change="handleFileSelect"
            />
            
            <div v-if="selectedFiles.length === 0" class="space-y-2">
              <Upload class="h-12 w-12 mx-auto text-slate-400" />
              <div>
                <p class="text-sm font-medium text-slate-900 dark:text-slate-100">
                  点击或拖拽文件到此处
                </p>
                <p class="text-xs text-slate-500 dark:text-slate-400">
                  支持 PDF、图片、Word、文本文件
                </p>
              </div>
            </div>

            <!-- 已选择的文件列表 -->
            <div v-else class="space-y-2">
              <div
                v-for="(file, index) in selectedFiles"
                :key="index"
                class="flex items-center justify-between p-2 bg-slate-50 dark:bg-slate-800 rounded border"
              >
                <div class="flex items-center gap-2 min-w-0">
                  <FileText class="h-4 w-4 text-blue-500 flex-shrink-0" />
                  <span class="text-sm truncate">{{ file.name }}</span>
                  <Badge variant="outline" class="text-xs">
                    {{ formatFileSize(file.size) }}
                  </Badge>
                </div>
                <Button
                  @click.stop="removeFile(index)"
                  variant="ghost"
                  size="sm"
                  class="h-6 w-6 p-0 hover:bg-red-100 hover:text-red-600"
                >
                  <X class="h-3 w-3" />
                </Button>
              </div>
              
              <Button
                @click="triggerFileSelect"
                variant="outline"
                size="sm"
                class="mt-2"
              >
                <Plus class="h-3 w-3 mr-1" />
                继续添加
              </Button>
            </div>
          </div>
        </div>

        <!-- 智能归档配置 -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <Label class="text-sm font-medium">智能归档配置</Label>
            <div class="flex items-center gap-2">
              <Switch
                v-model="enableSmartArchive"
                id="smart-archive"
              />
              <Label for="smart-archive" class="text-xs text-slate-600 dark:text-slate-400">
                启用智能分析
              </Label>
            </div>
          </div>

          <!-- 预设提示词选择 -->
          <div v-if="enableSmartArchive" class="space-y-3">
            <div class="space-y-2">
              <Label class="text-sm">选择文档类型（可选）</Label>
              <Select v-model:model-value="selectedPreset" @update:model-value="(value) => applyPreset(value as string)">
                <SelectTrigger>
                  <SelectValue placeholder="选择预设的文档类型..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem
                    v-for="preset in presetPrompts"
                    :key="preset.id"
                    :value="preset.id"
                  >
                    <div class="flex items-center gap-2">
                      <component :is="preset.icon" class="h-4 w-4" />
                      <span>{{ preset.name }}</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- 自定义提示词 -->
            <div class="space-y-2">
              <Label class="text-sm">分析提示词</Label>
              <Textarea
                v-model="customPrompt"
                placeholder="描述文档的类型、用途或希望的分类方式..."
                rows="3"
                class="resize-none"
              />
              <p class="text-xs text-slate-500 dark:text-slate-400">
                💡 AI将根据此提示词分析文档内容，并匹配到合适的知识库
              </p>
            </div>
          </div>
        </div>

        <!-- 上传进度 -->
        <div v-if="isUploading" class="space-y-3">
          <div class="flex items-center justify-between">
            <Label class="text-sm font-medium">上传进度</Label>
            <Badge variant="secondary">
              {{ completedUploads }}/{{ totalUploads }}
            </Badge>
          </div>
          
          <div class="space-y-2">
            <div
              v-for="(progress, index) in uploadProgress"
              :key="index"
              class="flex items-center gap-3 p-2 border border-slate-200 dark:border-slate-700 rounded"
            >
              <div class="flex-shrink-0">
                <Check v-if="progress.completed && !progress.error" class="h-4 w-4 text-green-600" />
                <AlertTriangle v-else-if="progress.error" class="h-4 w-4 text-red-600" />
                <Loader2 v-else class="h-4 w-4 animate-spin text-blue-600" />
              </div>
              
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium truncate">{{ progress.fileName }}</p>
                <div class="text-xs text-slate-500">
                  <span v-if="progress.completed && !progress.error" class="text-green-600">
                    ✅ {{ progress.smartArchived ? '智能归档完成' : '上传完成' }}
                  </span>
                  <span v-else-if="progress.error" class="text-red-600">
                    ❌ {{ progress.error }}
                  </span>
                  <span v-else-if="progress.analyzing" class="text-purple-600">
                    🧠 AI分析中...
                  </span>
                  <span v-else class="text-blue-600">
                    📤 上传中...
                  </span>
                </div>
                
                <!-- 智能归档结果 -->
                <div v-if="progress.archiveResult" class="mt-1 text-xs">
                  <span class="text-green-600">
                    📂 已归档到：{{ progress.archiveResult.knowledgeBaseName }}
                    <span v-if="progress.archiveResult.isNewKnowledgeBase" class="text-purple-600">(新建)</span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 整体进度条 -->
          <div class="space-y-1">
            <div class="flex justify-between text-xs text-slate-500">
              <span>整体进度</span>
              <span>{{ Math.round(overallProgress) }}%</span>
            </div>
            <div class="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
              <div 
                class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                :style="{ width: `${overallProgress}%` }"
              ></div>
            </div>
          </div>
        </div>

        <!-- 智能分析结果预览 -->
        <div v-if="showAnalysisResults && analysisResults.length > 0" class="space-y-3">
          <Label class="text-sm font-medium text-blue-600">🧠 AI分析结果 - 请确认归档建议</Label>
          <div class="space-y-2">
            <div
              v-for="result in analysisResults"
              :key="result.fileName"
              class="p-3 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg"
            >
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium text-blue-900 dark:text-blue-100">
                  📄 {{ result.fileName }}
                </span>
                <div class="flex items-center gap-2">
                  <Badge variant="outline" class="text-xs">
                    {{ result.documentType }}
                  </Badge>
                  <Badge 
                    :variant="result.isNewKnowledgeBase ? 'default' : 'secondary'"
                    class="text-xs"
                  >
                    {{ result.isNewKnowledgeBase ? '新建' : '已有' }}
                  </Badge>
                </div>
              </div>
              <p class="text-xs text-blue-700 dark:text-blue-300 mt-1">
                📂 建议归档至：{{ result.knowledgeBaseName }}
              </p>
              <p v-if="result.reason" class="text-xs text-blue-600 dark:text-blue-400 mt-1">
                💡 {{ result.reason }}
              </p>
              <div v-if="result.textContent" class="mt-2 p-2 bg-slate-100 dark:bg-slate-800 rounded text-xs">
                <p class="text-slate-600 dark:text-slate-400 font-medium mb-1">文档预览：</p>
                <p class="text-slate-700 dark:text-slate-300 line-clamp-3">{{ result.textContent }}</p>
              </div>
            </div>
          </div>
          
          <div class="flex justify-end gap-2 pt-2 border-t border-blue-200 dark:border-blue-800">
            <Button variant="outline" @click="showAnalysisResults = false" size="sm">
              重新分析
            </Button>
            <Button 
              @click="handleConfirmArchive" 
              class="bg-blue-600 hover:bg-blue-700 text-white"
              size="sm"
            >
              <Check class="h-4 w-4 mr-1" />
              确认归档
            </Button>
          </div>
        </div>

        <!-- 智能归档结果摘要 -->
        <div v-if="showResults && archiveResults.length > 0" class="space-y-3">
          <Label class="text-sm font-medium text-green-600">🎉 智能归档完成</Label>
          <div class="space-y-2">
            <div
              v-for="result in archiveResults"
              :key="result.fileName"
              class="p-3 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg"
            >
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium text-green-900 dark:text-green-100">
                  📄 {{ result.fileName }}
                </span>
                <Badge 
                  :variant="result.isNewKnowledgeBase ? 'default' : 'secondary'"
                  class="text-xs"
                >
                  {{ result.isNewKnowledgeBase ? '新建' : '已有' }}
                </Badge>
              </div>
              <p class="text-xs text-green-700 dark:text-green-300 mt-1">
                📂 归档至：{{ result.knowledgeBaseName }}
              </p>
              <p v-if="result.reason" class="text-xs text-green-600 dark:text-green-400 mt-1">
                💡 {{ result.reason }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!showAnalysisResults" class="flex justify-end gap-2">
        <Button variant="outline" @click="handleCancel" :disabled="isUploading">
          {{ isUploading ? '处理中...' : '取消' }}
        </Button>
        <Button 
          @click="handleConfirm" 
          :disabled="selectedFiles.length === 0 || isUploading"
          class="bg-blue-600 hover:bg-blue-700"
        >
          <template v-if="isUploading">
            <Loader2 class="h-4 w-4 animate-spin mr-2" />
            {{ enableSmartArchive && customPrompt.trim() ? 'AI分析中...' : '处理中...' }}
          </template>
          <template v-else>
            <Sparkles class="h-4 w-4 mr-2" />
            {{ enableSmartArchive && customPrompt.trim() ? '智能分析' : '直接上传' }}
          </template>
        </Button>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Upload,
  FileText,
  X,
  Plus,
  Sparkles,
  Check,
  AlertTriangle,
  Loader2,
  FileIcon,
  GraduationCap,
  Briefcase,
  Settings,
  BookOpen,
  Heart,
  Shield,
  Zap
} from 'lucide-vue-next'

// Props
interface Props {
  isOpen: boolean
}

// Emits
interface Emits {
  (e: 'update:isOpen', value: boolean): void
  (e: 'success', results: ArchiveResult[]): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 归档结果类型
interface ArchiveResult {
  fileName: string
  knowledgeBaseName: string
  isNewKnowledgeBase: boolean
  reason?: string
}

// 分析结果类型
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

// 上传进度类型
interface UploadProgress {
  fileName: string
  completed: boolean
  error?: string
  analyzing?: boolean
  smartArchived?: boolean
  archiveResult?: ArchiveResult
}

// 预设提示词类型
interface PresetPrompt {
  id: string
  name: string
  icon: any
  prompt: string
}

// 响应式状态
const selectedFiles = ref<File[]>([])
const isDragOver = ref(false)
const enableSmartArchive = ref(true)
const selectedPreset = ref<string>('')
const customPrompt = ref('')
const isUploading = ref(false)
const uploadProgress = ref<UploadProgress[]>([])
const showResults = ref(false)
const showAnalysisResults = ref(false)
const archiveResults = ref<ArchiveResult[]>([])
const analysisResults = ref<AnalysisResult[]>([])
const filesForArchive = ref<{fileName: string, content: string, fileType: string}[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)

// 预设提示词配置
const presetPrompts: PresetPrompt[] = [
  {
    id: 'contract',
    name: '合同文档',
    icon: FileIcon,
    prompt: '这是合同相关的法律文档，包含合同条款、协议书、法律文件等。请分析文档内容，判断是否属于合同类文档，如果是则归档到"合同文档"知识库。'
  },
  {
    id: 'education',
    name: '教育培训',
    icon: GraduationCap,
    prompt: '这是教育培训相关的文档，包含课程资料、培训手册、学习指南、教学大纲等。请分析文档内容，判断是否属于教育培训材料，如果是则归档到"教育培训"知识库。'
  },
  {
    id: 'business',
    name: '商务文档',
    icon: Briefcase,
    prompt: '这是商务相关的文档，包含商业计划书、市场分析、财务报告、商务提案等。请分析文档内容，判断是否属于商务文档，如果是则归档到"商务文档"知识库。'
  },
  {
    id: 'technical',
    name: '技术文档',
    icon: Settings,
    prompt: '这是技术相关的文档，包含技术规范、API文档、系统设计、开发指南等。请分析文档内容，判断是否属于技术文档，如果是则归档到"技术文档"知识库。'
  },
  {
    id: 'manual',
    name: '操作手册',
    icon: BookOpen,
    prompt: '这是操作手册类文档，包含用户手册、操作指南、使用说明书、流程文档等。请分析文档内容，判断是否属于操作手册，如果是则归档到"操作手册"知识库。'
  },
  {
    id: 'medical',
    name: '医疗健康',
    icon: Heart,
    prompt: '这是医疗健康相关的文档，包含医学资料、健康指南、医疗报告、药品说明等。请分析文档内容，判断是否属于医疗健康文档，如果是则归档到"医疗健康"知识库。'
  },
  {
    id: 'policy',
    name: '政策法规',
    icon: Shield,
    prompt: '这是政策法规相关的文档，包含政府政策、法律法规、规章制度、政策解读等。请分析文档内容，判断是否属于政策法规文档，如果是则归档到"政策法规"知识库。'
  },
  {
    id: 'other',
    name: '自定义分析',
    icon: Zap,
    prompt: '请根据文档内容自动判断文档类型和主题，选择最合适的知识库进行归档，如果没有匹配的知识库请创建新的知识库。'
  }
]

// 计算属性
const totalUploads = computed(() => uploadProgress.value.length)
const completedUploads = computed(() => uploadProgress.value.filter(p => p.completed).length)
const overallProgress = computed(() => {
  if (totalUploads.value === 0) return 0
  return (completedUploads.value / totalUploads.value) * 100
})

// 监听对话框打开状态
watch(() => props.isOpen, (isOpen) => {
  if (!isOpen) {
    resetDialog()
  }
})

// 方法
function triggerFileSelect() {
  if (fileInputRef.value) {
    fileInputRef.value.click()
  }
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target?.files) {
    const newFiles = Array.from(target.files)
    selectedFiles.value.push(...newFiles)
    target.value = '' // 清空input，允许重复选择同一文件
  }
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  isDragOver.value = false
  
  if (event.dataTransfer?.files) {
    const newFiles = Array.from(event.dataTransfer.files)
    selectedFiles.value.push(...newFiles)
  }
}

function removeFile(index: number) {
  selectedFiles.value.splice(index, 1)
}

function applyPreset(presetId: string | null) {
  if (!presetId) return
  const preset = presetPrompts.find(p => p.id === presetId)
  if (preset) {
    customPrompt.value = preset.prompt
  }
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

async function handleConfirm() {
  if (selectedFiles.value.length === 0) return

  if (enableSmartArchive.value && customPrompt.value.trim()) {
    // 智能归档：先分析
    await handleAnalyzeDocuments()
  } else {
    // 普通上传：直接上传
    await handleRegularUpload()
  }
}

async function handleAnalyzeDocuments() {
  isUploading.value = true
  showResults.value = false
  showAnalysisResults.value = false
  archiveResults.value = []
  analysisResults.value = []
  
  // 初始化上传进度
  uploadProgress.value = selectedFiles.value.map(file => ({
    fileName: file.name,
    completed: false,
    analyzing: true
  }))

  try {
    // 导入API函数
    const { analyzeDocumentsForArchive } = await import('@/utils/api/file')
    
    // 先将文件转换为Base64格式保存
    filesForArchive.value = await Promise.all(
      selectedFiles.value.map(async (file) => ({
        fileName: file.name,
        fileType: file.type,
        content: await fileToBase64(file)
      }))
    )
    
    // 调用分析API
    const response = await analyzeDocumentsForArchive({
      files: selectedFiles.value,
      prompt: customPrompt.value,
      customAnalysis: true
    })
    
    // 处理分析结果
    if (response.data && response.data.results) {
      analysisResults.value = response.data.results
      
      // 更新进度状态
      response.data.results.forEach((result, index) => {
        const progress = uploadProgress.value[index]
        if (progress) {
          progress.analyzing = false
          progress.completed = true
          if (!result.success) {
            progress.error = result.error || '分析失败'
          }
        }
      })
      
      showAnalysisResults.value = true
    } else {
      throw new Error('分析API调用失败')
    }
    
  } catch (error) {
    console.error('文档分析失败:', error)
    
    // 处理错误
    uploadProgress.value.forEach((progress) => {
      progress.analyzing = false
      progress.error = '分析失败，请稍后重试'
      progress.completed = true
    })
  } finally {
    isUploading.value = false
  }
}

async function handleConfirmArchive() {
  isUploading.value = true
  showAnalysisResults.value = false
  showResults.value = false
  archiveResults.value = []
  
  // 重置进度状态
  uploadProgress.value = selectedFiles.value.map(file => ({
    fileName: file.name,
    completed: false,
    smartArchived: false
  }))

  try {
    // 导入API函数
    const { confirmSmartArchive } = await import('@/utils/api/file')
    
    // 调用确认归档API
    const response = await confirmSmartArchive({
      files: filesForArchive.value,
      analysisResults: analysisResults.value
    })
    
    // 处理归档结果
    if (response.data && response.data.results) {
      const results = response.data.results
      
      results.forEach((result: any, index: number) => {
        const progress = uploadProgress.value[index]
        
        if (result.success) {
          const archiveResult: ArchiveResult = {
            fileName: result.fileName,
            knowledgeBaseName: result.knowledgeBaseName,
            isNewKnowledgeBase: result.isNewKnowledgeBase,
            reason: result.reason
          }
          
          progress.archiveResult = archiveResult
          progress.smartArchived = true
          progress.completed = true
          
          archiveResults.value.push(archiveResult)
        } else {
          progress.error = result.error || '归档失败'
          progress.completed = true
        }
      })
      
      showResults.value = true
      
      // 3秒后自动关闭对话框
      setTimeout(() => {
        emit('success', archiveResults.value)
        emit('update:isOpen', false)
      }, 3000)
    } else {
      throw new Error('归档API调用失败')
    }
    
  } catch (error) {
    console.error('确认归档失败:', error)
    
    uploadProgress.value.forEach((progress) => {
      progress.error = '归档失败，请稍后重试'
      progress.completed = true
    })
  } finally {
    isUploading.value = false
  }
}

async function handleRegularUpload() {
  isUploading.value = true
  showResults.value = false
  archiveResults.value = []
  
  // 初始化上传进度
  uploadProgress.value = selectedFiles.value.map(file => ({
    fileName: file.name,
    completed: false
  }))

  try {
    // 普通上传逻辑（不使用智能归档）
    for (let i = 0; i < selectedFiles.value.length; i++) {
      const file = selectedFiles.value[i]
      const progress = uploadProgress.value[i]
      
      try {
        // 这里可以调用普通的文件上传API
        await new Promise(resolve => setTimeout(resolve, 1000)) // 模拟上传延迟
        
        progress.completed = true
        
      } catch (error) {
        progress.error = error instanceof Error ? error.message : '上传失败'
        progress.completed = true
      }
    }
    
    showResults.value = true
    
    // 3秒后自动关闭对话框
    setTimeout(() => {
      emit('success', archiveResults.value)
      emit('update:isOpen', false)
    }, 3000)
    
  } catch (error) {
    console.error('文档上传失败:', error)
  } finally {
    isUploading.value = false
  }
}

// 将文件转换为Base64格式
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        // 移除data:开头部分，只保留Base64编码
        const base64 = reader.result.split(',')[1]
        resolve(base64)
      } else {
        reject(new Error('文件读取失败'))
      }
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

function handleCancel() {
  if (!isUploading.value) {
    emit('update:isOpen', false)
  }
}

function resetDialog() {
  selectedFiles.value = []
  isDragOver.value = false
  enableSmartArchive.value = true
  selectedPreset.value = ''
  customPrompt.value = ''
  isUploading.value = false
  uploadProgress.value = []
  showResults.value = false
  showAnalysisResults.value = false
  archiveResults.value = []
  analysisResults.value = []
  filesForArchive.value = []
}

// 模拟方法（实际使用时需要调用真实API）
function generateMockKnowledgeBaseName(fileName: string): string {
  const lowerName = fileName.toLowerCase()
  
  if (lowerName.includes('合同') || lowerName.includes('contract')) return '合同文档'
  if (lowerName.includes('培训') || lowerName.includes('教育') || lowerName.includes('课程')) return '教育培训'
  if (lowerName.includes('技术') || lowerName.includes('api') || lowerName.includes('开发')) return '技术文档'
  if (lowerName.includes('商务') || lowerName.includes('商业') || lowerName.includes('business')) return '商务文档'
  if (lowerName.includes('手册') || lowerName.includes('指南') || lowerName.includes('manual')) return '操作手册'
  if (lowerName.includes('医疗') || lowerName.includes('健康') || lowerName.includes('medical')) return '医疗健康'
  if (lowerName.includes('政策') || lowerName.includes('法规') || lowerName.includes('policy')) return '政策法规'
  
  // 默认归档到通用知识库
  return '通用文档'
}

function generateMockReason(fileName: string): string {
  const reasons = [
    '文档内容与现有知识库高度匹配',
    '根据文档主题和关键词自动分类',
    'AI分析确定最佳归档位置',
    '文档类型符合知识库定位',
    '基于内容相似度智能匹配'
  ]
  return reasons[Math.floor(Math.random() * reasons.length)]
}
</script>