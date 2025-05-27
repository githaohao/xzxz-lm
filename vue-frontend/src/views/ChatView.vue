<template>
  <div class="flex h-full bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
    <!-- RAG文档管理面板 -->
    <div 
      :class="[
        'transition-all duration-300 ease-in-out flex-shrink-0',
        showDocumentPanel ? 'w-80' : 'w-0'
      ]"
    >
      <RAGDocumentPanel v-show="showDocumentPanel" />
    </div>

    <!-- 主要内容区域 -->
    <div class="flex-1 flex flex-col">
      <!-- 顶部工具栏 -->
      <div class="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
        <div class="flex items-center gap-3">
          <button
            @click="toggleDocumentPanel"
            class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            :title="showDocumentPanel ? '隐藏文档面板' : '显示文档面板'"
          >
            <PanelLeftOpen v-if="!showDocumentPanel" class="h-5 w-5 text-slate-600 dark:text-slate-400" />
            <PanelLeftClose v-else class="h-5 w-5 text-slate-600 dark:text-slate-400" />
          </button>
          <h1 class="text-lg font-semibold text-slate-900 dark:text-slate-100">智能对话</h1>
        </div>
        
        <div class="flex items-center gap-2">
          <Badge v-if="selectedDocumentCount > 0" variant="outline" class="text-purple-600 border-purple-300">
            📚 已选 {{ selectedDocumentCount }} 个文档
          </Badge>
        </div>
      </div>

      <div class="flex-1 container mx-auto px-4 py-4 max-w-7xl flex flex-col min-h-0">
        <!-- 文件处理状态 -->
        <div v-if="processedFile" class="flex-shrink-0 mb-4">
          <div class="relative max-w-7xl mx-auto px-2">
            <div class="
              flex items-center gap-4 p-3
              bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/50 dark:to-indigo-950/50
              border border-blue-200/50 dark:border-blue-800/50
              rounded-xl shadow-lg backdrop-blur-sm
              transition-all duration-300
            ">
              <!-- 文件图标 -->
              <div class="flex-shrink-0">
                <div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center shadow-sm">
                  <Paperclip class="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
              
              <!-- 文件信息 -->
              <div class="flex-1 min-w-0">
                <p class="font-semibold text-sm text-slate-900 dark:text-slate-100 truncate">{{ processedFile.name }}</p>
                <p class="text-xs text-slate-600 dark:text-slate-400">{{ formatFileSize(processedFile.size) }}</p>
                <div class="flex items-center gap-2 mt-1">
                  <div v-if="processedFile.processing" class="w-1.5 h-1.5 rounded-full bg-yellow-500 animate-pulse"></div>
                  <div v-else class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
                  <span v-if="processedFile.processing" class="text-xs text-yellow-600 dark:text-yellow-400 font-medium">处理中...</span>
                  <span v-else class="text-xs text-green-600 dark:text-green-400 font-medium">已准备就绪</span>
                </div>
                
                <!-- RAG状态显示 -->
                <div v-if="processedFile.rag_enabled" class="flex items-center gap-2 mt-1">
                  <div class="w-1.5 h-1.5 rounded-full bg-purple-500"></div>
                  <span class="text-xs text-purple-600 dark:text-purple-400 font-medium">
                    🧠 智能检索已启用
                  </span>
                  <Badge variant="secondary" class="text-xs px-1.5 py-0.5">
                    RAG
                  </Badge>
                </div>
                <div v-else-if="processedFile.ocrCompleted && processedFile.content" class="flex items-center gap-2 mt-1">
                  <div class="w-1.5 h-1.5 rounded-full bg-gray-400"></div>
                  <span class="text-xs text-gray-500 dark:text-gray-400 font-medium">
                    📄 常规文本模式
                  </span>
                </div>
              </div>
              
              <!-- 移除按钮 -->
              <button
                @click="setProcessedFile(null)"
                class="
                  flex-shrink-0 p-1.5 rounded-lg
                  hover:bg-red-50 dark:hover:bg-red-900/20
                  text-slate-500 hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400
                  transition-all duration-200
                  focus:outline-none focus:ring-2 focus:ring-red-500/20
                "
              >
                <X class="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <ScrollArea 
          ref="scrollAreaRef"
          class="flex-1 min-h-0 pr-2" 
          style="height: calc(100vh - 280px);"
        >
          <div class="space-y-4 pb-4">
            <!-- 历史消息 -->
            <div
              v-for="message in messages"
              :key="message.id"
              :class="[
                'flex gap-3 max-w-full',
                message.isUser ? 'flex-row-reverse' : ''
              ]"
            >
              <!-- 头像 -->
              <Avatar class="w-8 h-8 flex-shrink-0 mt-1">
                <AvatarFallback 
                  :class="[
                    'text-white font-medium text-sm',
                    message.isUser 
                      ? 'bg-gradient-to-br from-green-500 to-emerald-600' 
                      : 'bg-gradient-to-br from-blue-500 to-purple-600'
                  ]"
                >
                  <User v-if="message.isUser" class="h-4 w-4" />
                  <Bot v-else class="h-4 w-4" />
                </AvatarFallback>
              </Avatar>

              <div :class="['flex flex-col gap-2 max-w-[80%]', message.isUser ? 'items-end' : 'items-start']">
                <!-- 文件信息 -->
                <Card v-if="message.fileInfo" class="border-slate-200 dark:border-slate-700">
                  <CardContent class="p-2">
                    <div class="flex items-center gap-2 text-xs">
                      <Paperclip class="h-3 w-3 text-slate-500" />
                      <span class="text-slate-700 dark:text-slate-300 truncate max-w-40">{{ message.fileInfo.name }}</span>
                      <Badge variant="secondary" class="text-xs px-1 py-0">
                        {{ formatFileSize(message.fileInfo.size) }}
                      </Badge>
                      <!-- RAG指示器 -->
                      <Badge v-if="message.fileInfo.rag_enabled" variant="outline" class="text-xs text-purple-600 border-purple-300 px-1 py-0">
                        🧠 RAG
                      </Badge>
                    </div>
                  </CardContent>
                </Card>

                <!-- 消息内容 -->
                <Card 
                  :class="[
                    'shadow-sm transition-all duration-200 hover:shadow-md max-w-full',
                    message.isUser 
                      ? 'bg-gradient-to-br from-green-500 to-emerald-600 text-white border-green-200' 
                      : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700'
                  ]"
                >
                  <CardContent class="p-3">
                    <div v-if="!message.isUser && hasThinkTags(message.content)" class="space-y-2">
                      <!-- 思考内容（可折叠） -->
                      <details class="group">
                        <summary class="cursor-pointer text-xs text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 flex items-center gap-1">
                          <span class="text-sm">🤔</span>
                          <span>思考过程</span>
                          <span class="text-xs opacity-60 group-open:hidden">(展开)</span>
                        </summary>
                        <div class="mt-2 p-2 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
                          <div class="text-xs text-slate-600 dark:text-slate-300 whitespace-pre-wrap leading-relaxed max-h-32 overflow-y-auto">
                            {{ extractThinkContent(message.content).think }}
                          </div>
                        </div>
                      </details>
                      
                      <Separator class="my-2" />
                      
                      <!-- 实际回复内容 -->
                      <div class="text-sm text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed">
                        {{ extractThinkContent(message.content).content }}
                      </div>
                    </div>
                    <div v-else class="text-sm whitespace-pre-wrap leading-relaxed break-words">
                      {{ message.content }}
                    </div>
                  </CardContent>
                </Card>

                <!-- 时间戳 -->
                <div class="text-xs text-slate-400 dark:text-slate-500 px-1">
                  {{ formatTime(message.timestamp) }}
                </div>
              </div>
            </div>

          <!-- 当前流式消息 -->
          <div
            v-if="currentStreamingMessage"
            class="flex gap-3 max-w-full"
          >
            <Avatar class="w-8 h-8 flex-shrink-0 mt-1">
              <AvatarFallback class="bg-gradient-to-br from-blue-500 to-purple-600 text-white text-sm">
                <Bot class="h-4 w-4" />
              </AvatarFallback>
            </Avatar>

            <div class="flex flex-col gap-2 max-w-[80%] items-start">
              <Card class="bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 shadow-sm max-w-full">
                <CardContent class="p-3">
                  <div v-if="hasThinkTags(currentStreamingMessage.content)" class="space-y-2">
                    <!-- 思考内容（可折叠） -->
                    <details class="group" :open="currentStreamingMessage.isStreaming && !extractThinkContent(currentStreamingMessage.content).content">
                      <summary class="cursor-pointer text-xs text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 flex items-center gap-1">
                        <span class="text-sm">🤔</span>
                        <span>查看思考过程</span>
                        <span class="text-xs opacity-60 group-open:hidden">(展开)</span>
                      </summary>
                      <div class="mt-2 p-2 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
                        <div class="text-xs text-slate-600 dark:text-slate-300 whitespace-pre-wrap leading-relaxed max-h-32 overflow-y-auto">
                          {{ extractThinkContent(currentStreamingMessage.content).think }}
                          <span v-if="currentStreamingMessage.isStreaming && !extractThinkContent(currentStreamingMessage.content).content" class="inline-block w-1.5 h-4 bg-blue-500 animate-pulse ml-1">▋</span>
                        </div>
                      </div>
                    </details>
                    
                    <Separator v-if="extractThinkContent(currentStreamingMessage.content).content" class="my-2" />
                    
                    <!-- 实际回复内容 -->
                    <div v-if="extractThinkContent(currentStreamingMessage.content).content" class="text-sm text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed">
                      {{ extractThinkContent(currentStreamingMessage.content).content }}
                      <span v-if="currentStreamingMessage.isStreaming" class="inline-block w-1.5 h-4 bg-blue-500 animate-pulse ml-1">▋</span>
                    </div>
                  </div>
                  <div v-else class="text-sm text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed break-words">
                    {{ currentStreamingMessage.content }}
                    <span v-if="currentStreamingMessage.isStreaming" class="inline-block w-1.5 h-4 bg-blue-500 animate-pulse ml-1">▋</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
          
          <!-- 滚动状态指示器 -->
          <div 
            v-if="!isAtBottom && messages.length > 0"
            class="flex justify-center py-2"
          >
            <button
              @click="scrollToBottom"
              class="
                flex items-center gap-2 px-3 py-1.5 
                bg-blue-500/90 hover:bg-blue-600/90 
                text-white text-xs rounded-full 
                shadow-lg backdrop-blur-sm
                transition-all duration-200 hover:scale-105
                animate-pulse
              "
            >
              <span>↓</span>
              <span>滚动到底部</span>
            </button>
          </div>
        </div>
      </ScrollArea>

      <!-- 输入区域 -->
      <div class="flex-shrink-0 mt-4 px-2">
        <!-- RAG智能建议 -->
        <div v-if="ragSuggestion" class="max-w-7xl mx-auto mb-2">
          <div class="flex items-center gap-2 p-2 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/30 dark:to-blue-950/30 border border-purple-200 dark:border-purple-800 rounded-lg">
            <div class="text-purple-600 dark:text-purple-400">💡</div>
            <span class="text-xs text-purple-700 dark:text-purple-300">{{ ragSuggestion }}</span>
            <button 
              v-if="!ragEnabled"
              @click="ragEnabled = true"
              class="ml-auto text-xs bg-purple-100 hover:bg-purple-200 dark:bg-purple-900 dark:hover:bg-purple-800 text-purple-700 dark:text-purple-300 px-2 py-1 rounded-md transition-colors"
            >
              启用RAG
            </button>
          </div>
        </div>
        
        <!-- Grok风格的现代化输入框 -->
        <div class="relative max-w-7xl mx-auto">
          <!-- 主输入容器 -->
          <div 
            :class="[
              'relative flex items-end gap-3 p-4 transition-all duration-300 ease-out',
              'bg-white/90 dark:bg-slate-800/90 backdrop-blur-xl',
              'border rounded-3xl shadow-2xl shadow-black/5 dark:shadow-black/20',
              'hover:shadow-2xl hover:shadow-black/10 dark:hover:shadow-black/30',
              'focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500/30',
              isDragging 
                ? 'border-blue-500 bg-blue-50/80 dark:bg-blue-950/80 scale-[1.02] shadow-2xl shadow-blue-500/20' 
                : 'border-slate-200/50 dark:border-slate-700/50'
            ]"
            @drop.prevent="handleFileDrop"
            @dragover.prevent="handleDragOver"
            @dragenter.prevent="handleDragEnter"
            @dragleave.prevent="handleDragLeave"
          >
            <!-- 文件附件图标 -->
            <div class="flex-shrink-0 pb-1">
              <button
                @click="fileInput?.click()"
                :disabled="isLoading"
                class="
                  group relative p-2 rounded-lg
                  bg-slate-50 dark:bg-slate-700/50
                  hover:bg-slate-100 dark:hover:bg-slate-600/50
                  border border-slate-200 dark:border-slate-600
                  transition-all duration-200 ease-out
                  hover:scale-105 hover:shadow-lg
                  disabled:opacity-50 disabled:cursor-not-allowed
                  focus:outline-none focus:ring-2 focus:ring-blue-500/20
                "
              >
                <Paperclip class="h-4 w-4 text-slate-600 dark:text-slate-300 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors" />
                
                <!-- 悬浮提示 -->
                <div class="
                  absolute -top-8 left-1/2 transform -translate-x-1/2
                  px-2 py-1 text-xs text-white bg-slate-900 rounded-md
                  opacity-0 group-hover:opacity-100 transition-opacity duration-200
                  pointer-events-none whitespace-nowrap
                ">
                  添加文件
                </div>
              </button>
              
              <input
                ref="fileInput"
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.wav,.mp3"
                @change="handleFileSelect"
                class="hidden"
              />
            </div>

            <!-- 输入框区域 -->
            <div class="flex-1 relative">
              <Textarea
                v-model="inputMessage"
                placeholder="输入你的消息..."
                class="
                  w-full min-h-[44px] max-h-32 py-3 px-4
                  bg-transparent border-0 resize-none
                  text-slate-900 dark:text-slate-100
                  placeholder:text-slate-500 dark:placeholder:text-slate-400
                  focus:outline-none focus:ring-0
                  text-sm leading-relaxed
                  scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-600
                "
                :disabled="isLoading"
                @keydown.enter.exact.prevent="handleSend"
                @keydown.enter.shift.exact.prevent="inputMessage += '\n'"
              />
              
              <!-- 字符计数（可选） -->
              <div 
                v-if="inputMessage.length > 800"
                class="absolute bottom-1 right-2 text-xs text-slate-400 dark:text-slate-500"
              >
                {{ inputMessage.length }}/2000
              </div>
            </div>

            <!-- 发送按钮区域 -->
            <div class="flex-shrink-0 pb-1">
              <Button
                v-if="isLoading"
                @click="cancelRequest"
                size="lg"
                class="
                  h-9 w-9 p-0 rounded-lg
                  bg-red-500 hover:bg-red-600
                  border-0 shadow-lg hover:shadow-xl
                  transition-all duration-200 ease-out
                  hover:scale-105
                "
              >
                <X class="h-4 w-4 text-white" />
              </Button>
              
              <Button
                v-else
                @click="handleSend"
                :disabled="(!inputMessage.trim() && !processedFile) || isLoading"
                size="lg"
                class="
                  h-9 w-9 p-0 rounded-lg
                  bg-gradient-to-r from-blue-600 to-purple-600 
                  hover:from-blue-700 hover:to-purple-700
                  disabled:from-slate-300 disabled:to-slate-400
                  border-0 shadow-lg hover:shadow-xl
                  transition-all duration-200 ease-out
                  hover:scale-105 disabled:hover:scale-100
                  focus:outline-none focus:ring-2 focus:ring-blue-500/20
                "
              >
                <Send class="h-4 w-4 text-white ml-0.5" />
              </Button>
            </div>
          </div>

          <!-- 输入提示 -->
          <div class="flex items-center justify-between mt-2 px-4 text-xs text-slate-500 dark:text-slate-400">
            <div class="flex items-center gap-3">
              <span class="flex items-center gap-1">
                <kbd class="px-1 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-[10px] font-mono">⏎</kbd>
                发送
              </span>
              <span class="flex items-center gap-1">
                <kbd class="px-1 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-[10px] font-mono">⇧</kbd>
                <kbd class="px-1 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-[10px] font-mono">⏎</kbd>
                换行
              </span>
              
              <!-- RAG模式切换 -->
              <div v-if="processedFile?.rag_enabled" class="flex items-center gap-1 ml-2">
                <input 
                  id="rag-toggle"
                  v-model="ragEnabled"
                  type="checkbox" 
                  class="w-3 h-3 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500 dark:focus:ring-purple-600 dark:ring-offset-gray-800 focus:ring-1 dark:bg-gray-700 dark:border-gray-600"
                />
                <label for="rag-toggle" class="text-xs text-purple-600 dark:text-purple-400 font-medium cursor-pointer">
                  🧠 智能检索
                </label>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span>支持 PDF、图片拖拽上传</span>
            </div>
          </div>

          <!-- 加载状态指示器 -->
          <div 
            v-if="isLoading"
            class="absolute -top-1 left-1/2 transform -translate-x-1/2"
          >
            <div class="flex items-center gap-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-full text-sm shadow-lg">
              <div class="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <span>{{ processingStatus || 'AI正在思考...' }}</span>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { 
  Send, 
  Paperclip, 
  Bot, 
  User, 
  Loader2,
  X,
  PanelLeftOpen,
  PanelLeftClose
} from 'lucide-vue-next'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { useChatStore } from '@/stores/chat'
import { useRAGStore } from '@/stores/rag'
import { formatTime, formatFileSize, hasThinkTags, extractThinkContent } from '@/utils'
import { uploadFile } from '@/utils/api'
import { getRagSuggestion, isFileRagSuitable } from '@/utils/rag-utils'
import RAGDocumentPanel from '@/components/RAGDocumentPanel.vue'

const chatStore = useChatStore()
const {
  messages,
  isLoading,
  processingStatus,
  currentStreamingMessage,
  processedFile
} = storeToRefs(chatStore)

const { sendMessage, cancelRequest, setProcessedFile } = chatStore

const inputMessage = ref('')
const fileInput = ref<HTMLInputElement>()
const isDragging = ref(false)
const ragEnabled = ref(true) // 默认启用RAG
const showDocumentPanel = ref(true) // 显示文档面板

// RAG Store
const ragStore = useRAGStore()
const { selectedCount: selectedDocumentCount } = storeToRefs(ragStore)

// 新增：滚动区域引用
const scrollAreaRef = ref<InstanceType<typeof ScrollArea>>()

// 新增：智能滚动控制
const isUserScrolling = ref(false)
const scrollTimeout = ref<number | null>(null)
const isAtBottom = ref(true)

// 切换文档面板显示
function toggleDocumentPanel() {
  showDocumentPanel.value = !showDocumentPanel.value
}

// 计算智能建议
const ragSuggestion = computed(() => {
  if (!processedFile.value?.content || !inputMessage.value) return null
  return getRagSuggestion(inputMessage.value, processedFile.value.content)
})

// 新增：检测是否在底部的函数
function checkIfAtBottom(viewport: Element) {
  const threshold = 50 // 允许50px的误差
  const isBottom = viewport.scrollTop + viewport.clientHeight >= viewport.scrollHeight - threshold
  isAtBottom.value = isBottom
  return isBottom
}

// 新增：处理用户滚动事件
function handleUserScroll(event: Event) {
  const viewport = event.target as Element
  
  // 检测是否在底部
  checkIfAtBottom(viewport)
  
  // 标记用户正在滚动
  isUserScrolling.value = true
  
  // 清除之前的超时
  if (scrollTimeout.value) {
    clearTimeout(scrollTimeout.value)
  }
  
  // 1秒后重置用户滚动状态
  scrollTimeout.value = setTimeout(() => {
    isUserScrolling.value = false
    // 如果在底部，重新启用自动滚动
    if (isAtBottom.value) {
      scrollToBottom()
    }
  }, 1000)
}

// 新增：自动滚动到底部函数
function scrollToBottom() {
  // 如果用户正在滚动，不执行自动滚动
  if (isUserScrolling.value) return
  
  nextTick(() => {
    if (scrollAreaRef.value) {
      const viewport = scrollAreaRef.value.$el.querySelector('[data-reka-scroll-area-viewport]')
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight
        isAtBottom.value = true
      }
    }
  })
}

// 新增：初始化滚动监听
function initScrollListener() {
  nextTick(() => {
    if (scrollAreaRef.value) {
      const viewport = scrollAreaRef.value.$el.querySelector('[data-reka-scroll-area-viewport]')
      if (viewport) {
        viewport.addEventListener('scroll', handleUserScroll, { passive: true })
      }
    }
  })
}

// 新增：清理滚动监听
function cleanupScrollListener() {
  if (scrollAreaRef.value) {
    const viewport = scrollAreaRef.value.$el.querySelector('[data-reka-scroll-area-viewport]')
    if (viewport) {
      viewport.removeEventListener('scroll', handleUserScroll)
    }
  }
  if (scrollTimeout.value) {
    clearTimeout(scrollTimeout.value)
  }
}

// 生命周期钩子
onMounted(() => {
  initScrollListener()
})

onUnmounted(() => {
  cleanupScrollListener()
})

// 监听消息变化，智能自动滚动到底部
watch(
  () => messages.value.length,
  () => {
    // 只有在底部或者不是用户滚动时才自动滚动
    if (isAtBottom.value || !isUserScrolling.value) {
      scrollToBottom()
    }
  }
)

// 监听流式消息内容变化，智能自动滚动到底部  
watch(
  () => currentStreamingMessage.value?.content,
  () => {
    if (currentStreamingMessage.value && (isAtBottom.value || !isUserScrolling.value)) {
      scrollToBottom()
    }
  }
)

// 发送消息
async function handleSend() {
  if (!inputMessage.value.trim() && !processedFile.value && selectedDocumentCount.value === 0) return

  // 优先使用选中的文档
  let fileToSend = processedFile.value
  
  // 如果有选中的文档，使用第一个选中的文档（或者可以扩展为多文档支持）
  if (selectedDocumentCount.value > 0) {
    const selectedDocs = ragStore.selectedDocumentsList
    if (selectedDocs.length > 0) {
      const firstDoc = selectedDocs[0]
              fileToSend = {
          name: firstDoc.filename,
          type: firstDoc.file_type,
          size: firstDoc.total_length,
          content: '', // 内容会在后端检索时获取
          doc_id: firstDoc.doc_id,
          ocrCompleted: true,
          rag_enabled: ragEnabled.value
        }
    }
  }
  
  // 如果用户关闭了RAG，创建一个不带RAG功能的文件副本
  if (fileToSend && !ragEnabled.value) {
    fileToSend = {
      ...fileToSend,
      rag_enabled: false,
      doc_id: undefined
    }
  }

  await sendMessage(inputMessage.value, fileToSend || undefined)
  inputMessage.value = ''
}

// 处理文件选择
async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    await processFile(file)
    target.value = ''
  }
}

// 处理文件拖拽
async function handleFileDrop(event: DragEvent) {
  isDragging.value = false
  const file = event.dataTransfer?.files[0]
  if (file) {
    await processFile(file)
  }
}

// 拖拽事件处理
function handleDragEnter(event: DragEvent) {
  event.preventDefault()
  isDragging.value = true
}

function handleDragLeave(event: DragEvent) {
  event.preventDefault()
  if (!event.relatedTarget || !(event.currentTarget as Element).contains(event.relatedTarget as Node)) {
    isDragging.value = false
  }
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
}

// 处理文件
async function processFile(file: File) {
  try {
    console.log('📎 开始处理文件:', file.name)
    
    // 设置处理中状态
    setProcessedFile({
      name: file.name,
      size: file.size,
      type: file.type,
      processing: true
    })

    // 上传并处理文件
    const result = await uploadFile(file)
    
    // 设置文件状态（uploadFile函数已经处理了ocrCompleted和processing状态）
    setProcessedFile(result)
    
    if (result.ocrCompleted) {
      console.log('✅ OCR处理完成，文件已准备就绪（支持RAG智能检索）:', result)
    } else {
      console.log('⏳ 文件上传成功，OCR处理中:', result)
    }
  } catch (error: any) {
    console.error('❌ 文件处理失败:', error)
    setProcessedFile(null)
    alert(`文件处理失败: ${error.message}`)
  }
}
</script>