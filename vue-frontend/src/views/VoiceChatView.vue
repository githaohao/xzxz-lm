<template>
  <div class="min-h-full overflow-y-auto">
    <div class="container mx-auto p-4 max-w-7xl">
      <div class="space-y-6">
        <!-- 页面标题 -->
        <div class="text-center">
          <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            语音聊天控制台
          </h1>
          <p class="text-gray-600 dark:text-gray-400">
            基于 FunAudioLLM 的高性能语音对话系统
          </p>
        </div>

        <!-- 知识库选择区域 -->
        <Card class="border-0 shadow-lg">
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Database class="h-6 w-6 text-purple-500" />
              知识库设置
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <KnowledgeBaseSelector v-model="localSelectedKnowledgeBase" />
              </div>
              <div class="flex items-center gap-2 ml-4">
                <Badge v-if="localSelectedKnowledgeBase && currentKnowledgeBaseDocumentsCount > 0" variant="outline" class="text-green-600 border-green-300">
                  🗂️ {{ currentKnowledgeBaseDocumentsCount }} 个文档
                </Badge>
                <Badge v-else-if="localSelectedKnowledgeBase" variant="outline" class="text-gray-500 border-gray-300">
                  🗂️ 空知识库
                </Badge>
                <Badge v-else variant="outline" class="text-gray-400 border-gray-300">
                  💬 常规对话
                </Badge>
              </div>
            </div>
            <div v-if="localSelectedKnowledgeBase" class="mt-2 text-sm text-gray-600 dark:text-gray-400">
              💡 已选择知识库"{{ localSelectedKnowledgeBase.name }}"，语音对话将基于知识库内容进行智能问答
            </div>
            <div v-else class="mt-2 text-sm text-gray-500 dark:text-gray-500">
              💬 当前为常规对话模式，选择知识库可开启基于文档的智能问答
            </div>
          </CardContent>
        </Card>

      <!-- 状态显示 -->
      <Card class="border-0 shadow-lg">
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Mic class="h-6 w-6 text-blue-500" />
            系统状态
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg border">
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-blue-500"></div>
                <span class="font-medium">通话状态</span>
              </div>
              <Badge :variant="getStatusColor()" class="font-medium">
                {{ getStatusText() }}
              </Badge>
            </div>
            <div class="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg border">
              <div class="flex items-center gap-2">
                <MessageCircle class="h-4 w-4 text-green-500" />
                <span class="font-medium">对话轮数</span>
              </div>
              <Badge variant="outline" class="font-medium">{{ conversationRounds }}</Badge>
            </div>
            <div class="flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg border">
              <div class="flex items-center gap-2">
                <Cpu class="h-4 w-4 text-purple-500" />
                <span class="font-medium">语音引擎</span>
              </div>
              <Badge :variant="funAudioAvailable ? 'default' : 'destructive'" class="font-medium">
                {{ funAudioAvailable ? 'FunAudioLLM' : '不可用' }}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- 语音引擎状态提示 -->
      <div v-if="!funAudioAvailable" class="flex justify-center">
        <Alert variant="destructive" class="max-w-2xl">
          <AlertTriangle class="h-4 w-4" />
          <AlertDescription class="ml-2">
            <strong>语音引擎不可用</strong> - 请检查后端服务状态，确保 FunAudioLLM 服务正常运行
          </AlertDescription>
        </Alert>
      </div>

      <!-- 通话控制区域 -->
      <Card class="border-0 shadow-lg">
        <CardContent class="p-8">
          <div class="flex justify-center">
            <div class="flex items-center gap-6">
              <div v-if="callState === 'idle'">
                  <div class="relative">
                  <Button
                    @click="handleStartCall"
                    size="lg"
                    class="rounded-full w-20 h-20 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 shadow-xl transition-all duration-300 hover:scale-110 relative z-10"
                    :disabled="!canStartCall"
                  >
                    <Phone class="h-8 w-8" />
                  </Button>
                  <div class="absolute -inset-2 bg-green-400 rounded-full opacity-20 animate-ping pointer-events-none"></div>
                </div>
              </div>
              <div v-else class="flex items-center gap-6">
                <!-- 结束通话 -->
                <Button
                  @click="endCall"
                  size="lg"
                  variant="destructive"
                  class="rounded-full w-16 h-16 shadow-lg transition-all duration-200 hover:scale-105"
                >
                  <Phone class="h-8 w-8 text-white" />
                </Button>

                <!-- 静音控制 -->
                <Button
                  @click="toggleMute"
                  :variant="isMuted ? 'default' : 'outline'"
                  size="lg"
                  class="rounded-full w-14 h-14 shadow-lg transition-all duration-200 hover:scale-105"
                >
                  <Volume2 v-if="!isMuted" class="h-5 w-5" />
                  <VolumeX v-else class="h-5 w-5" />
                </Button>

                <!-- 中断AI -->
                <Button
                  v-if="isAIPlaying"
                  @click="interruptAI"
                  variant="outline"
                  size="lg"
                  class="rounded-full w-14 h-14 shadow-lg transition-all duration-200 hover:scale-105"
                >
                  <Pause class="h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>
          
          <!-- 状态指示器 -->
          <div class="flex justify-center mt-6">
            <div class="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
              <div v-if="callState === 'listening'" class="flex items-center gap-2">
                <div class="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                <span>正在录音</span>
              </div>
              <div v-if="isAIPlaying" class="flex items-center gap-2">
                <div class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <span>AI 正在回复</span>
              </div>
              <div v-if="callState === 'processing'" class="flex items-center gap-2">
                <div class="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                <span>正在处理</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- 会话管理 -->
      <div v-if="callState === 'idle'" class="flex justify-center gap-3">
        <Button
          @click="clearHistory"
          variant="outline"
          size="sm"
          :disabled="!hasMessages"
          class="transition-all duration-200 hover:scale-105"
        >
          <Trash2 class="h-4 w-4 mr-2" />
          清除历史
        </Button>
        <Button
          @click="restartSession"
          variant="outline"
          size="sm"
          class="transition-all duration-200 hover:scale-105"
        >
          <RotateCcw class="h-4 w-4 mr-2" />
          新会话
        </Button>
      </div>

      <!-- 对话历史 -->
      <div v-if="hasMessages">
        <Card class="border-0 shadow-lg">
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <MessageSquare class="h-5 w-5 text-blue-500" />
              对话记录
              <Badge variant="secondary" class="ml-auto">{{ messages.length }} 条消息</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div class="space-y-4 max-h-96 overflow-y-auto pr-2">
              <div
                v-for="message in messages"
                :key="message.id"
                :class="[
                  'flex gap-3 transition-all duration-200 hover:bg-gray-50 dark:hover:bg-gray-800/50 rounded-lg p-2',
                  message.isUser ? 'justify-end' : 'justify-start'
                ]"
              >
                <div
                  :class="[
                    'flex gap-3 max-w-[80%]',
                    message.isUser ? 'flex-row-reverse' : 'flex-row'
                  ]"
                >
                  <!-- 头像 -->
                  <Avatar class="w-10 h-10 flex-shrink-0">
                    <AvatarFallback 
                      :class="message.isUser ? 'bg-blue-500 text-white' : 'bg-gray-600 text-white'"
                    >
                      <User v-if="message.isUser" class="h-5 w-5" />
                      <Bot v-else class="h-5 w-5" />
                    </AvatarFallback>
                  </Avatar>

                  <div class="flex flex-col gap-2">
                    <Card 
                      :class="[
                        'transition-all duration-200 hover:shadow-md',
                        message.isUser 
                          ? 'bg-blue-500 text-white border-blue-500' 
                          : 'bg-white dark:bg-gray-700 border-gray-200 dark:border-gray-600'
                      ]"
                    >
                      <CardContent class="p-4">
                        <div class="whitespace-pre-wrap break-words text-sm leading-relaxed">
                          {{ message.content }}
                        </div>
                      </CardContent>
                    </Card>
                    <div class="text-xs text-gray-500 dark:text-gray-400 px-1">
                      {{ formatTime(message.timestamp) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- 使用说明 -->
      <Card v-if="callState === 'idle'" class="border-0 shadow-lg bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Settings class="h-5 w-5 text-blue-500" />
            使用说明
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-3">
              <h4 class="font-medium text-gray-900 dark:text-white">基本操作</h4>
              <div class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <div class="flex items-center gap-2">
                  <Phone class="h-4 w-4 text-green-500" />
                  <span>点击绿色电话按钮开始语音通话</span>
                </div>
                <div class="flex items-center gap-2">
                  <Mic class="h-4 w-4 text-blue-500" />
                  <span>系统会自动录音并识别您的语音</span>
                </div>
                <div class="flex items-center gap-2">
                  <Pause class="h-4 w-4 text-orange-500" />
                  <span>AI回复时可以点击暂停按钮中断</span>
                </div>
                <div class="flex items-center gap-2">
                  <Volume2 class="h-4 w-4 text-purple-500" />
                  <span>支持静音控制和会话管理</span>
                </div>
                <div class="flex items-center gap-2">
                  <Database class="h-4 w-4 text-green-500" />
                  <span>选择知识库进行基于文档的智能问答</span>
                </div>
              </div>
            </div>
            <div class="space-y-3">
              <h4 class="font-medium text-gray-900 dark:text-white">技术特性</h4>
              <div class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <div class="flex items-center gap-2">
                  <Zap class="h-4 w-4 text-yellow-500" />
                  <span>基于FunAudioLLM引擎，识别速度比Whisper快15倍</span>
                </div>
                <div class="flex items-center gap-2">
                  <Heart class="h-4 w-4 text-red-500" />
                  <span>支持情感识别和声学事件检测</span>
                </div>
                <div class="flex items-center gap-2">
                  <Globe class="h-4 w-4 text-green-500" />
                  <span>支持50+种语言的语音识别</span>
                </div>
                <div class="flex items-center gap-2">
                  <Shield class="h-4 w-4 text-blue-500" />
                  <span>本地处理，保护用户隐私</span>
                </div>
              </div>
            </div>
          </div>
          </CardContent>
      </Card>
    </div>
  </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import {
  Mic,
  Phone,
  PhoneOff,
  Volume2,
  VolumeX,
  Pause,
  Trash2,
  RotateCcw,
  Settings,
  Bot,
  User,
  MessageCircle,
  MessageSquare,
  Cpu,
  AlertTriangle,
  Zap,
  Heart,
  Globe,
  Shield,
  Database
} from 'lucide-vue-next'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import Alert from '@/components/ui/Alert.vue'
import AlertDescription from '@/components/ui/AlertDescription.vue'
import { useVoiceStore } from '@/stores/voice'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import { formatTime } from '@/utils/voice-utils'
import KnowledgeBaseSelector from '@/components/KnowledgeBaseSelector.vue'
import { ref, computed, watch } from 'vue'
import type { KnowledgeBase } from '@/types'

const voiceStore = useVoiceStore()
const {
  messages,
  callState,
  isRecording,
  isAIPlaying,
  isMuted,
  conversationRounds,
  funAudioAvailable,
  hasMessages,
  canStartCall,
  selectedKnowledgeBase
} = storeToRefs(voiceStore)

const {
  checkServiceStatus,
  startCall,
  endCall,
  toggleMute,
  interruptAI,
  clearHistory,
  restartSession,
  getStatusText,
  setSelectedKnowledgeBase
} = voiceStore

// 知识库Store
const knowledgeBaseStore = useKnowledgeBaseStore()
const { currentKnowledgeBaseDocuments } = storeToRefs(knowledgeBaseStore)

// 本地知识库选择状态（用于KnowledgeBaseSelector组件）
const localSelectedKnowledgeBase = ref<KnowledgeBase | null>(null)

// 计算当前知识库的文档数量
const currentKnowledgeBaseDocumentsCount = computed(() => currentKnowledgeBaseDocuments.value.length)

// 监听本地知识库选择变化，同步到voice store
watch(localSelectedKnowledgeBase, (newKb) => {
  setSelectedKnowledgeBase(newKb)
  if (newKb) {
    knowledgeBaseStore.setSelectedKnowledgeBase(newKb)
  }
})

// 监听voice store中知识库选择变化，同步到本地
watch(selectedKnowledgeBase, (newKb) => {
  localSelectedKnowledgeBase.value = newKb
})

// 处理开始通话
async function handleStartCall() {
  try {
    await startCall()
  } catch (error: any) {
    alert(error.message)
  }
}

// 获取状态颜色
function getStatusColor() {
  switch (callState.value) {
    case 'idle':
      return 'secondary'
    case 'connecting':
      return 'default'
    case 'connected':
      return 'default'
    case 'listening':
      return 'default'
    case 'speaking':
      return 'default'
    case 'processing':
      return 'default'
    default:
      return 'secondary'
  }
}

onMounted(() => {
  checkServiceStatus()
  // 初始化知识库数据
  knowledgeBaseStore.initialize()
})
</script>