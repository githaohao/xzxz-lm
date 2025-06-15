<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
    <div class="container mx-auto p-4 max-w-2xl">
      <div class="space-y-6">
        <!-- AI头像区域 -->
        <div class="flex justify-center pt-8">
          <div class="relative">
            <Avatar class="w-32 h-32">
              <div 
                :class="[
                  'w-full h-full rounded-full flex items-center justify-center transition-all duration-300',
                  isAIPlaying ? 'bg-blue-500 animate-pulse' : 'bg-blue-600'
                ]"
              >
                <Bot class="h-16 w-16 !text-white" />
              </div>
            </Avatar>
            
            <!-- 说话动画 -->
            <div 
              v-if="isAIPlaying" 
              class="absolute inset-0 rounded-full border-4 border-blue-300 animate-ping"
            />
            
            <!-- 录音指示器 -->
            <div 
              v-if="connectionState === 'listening'" 
              class="absolute -bottom-2 -right-2"
            >
              <div class="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center animate-pulse">
                <div class="w-2 h-2 bg-white rounded-full"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 状态文本和进度 -->
        <div class="text-center space-y-3">
          <h2 class="text-2xl font-bold text-gray-800 dark:text-white mb-2">
            AI 语音助手 - 流式传输
          </h2>
          <Badge 
            :variant="getStatusVariant()" 
            class="text-sm px-3 py-1"
          >
            {{ getStatusText() }}
          </Badge>
          
          <!-- WebSocket连接状态指示器 -->
          <div class="flex items-center justify-center gap-2 text-xs">
            <div 
              :class="[
                'w-2 h-2 rounded-full',
                isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
              ]"
            ></div>
            <span :class="isConnected ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
              {{ isConnected ? 'WebSocket已连接 - 流式模式' : 'WebSocket未连接' }}
            </span>
          </div>
          
          <!-- 当前播放的文字 -->
          <div v-if="currentPlayingText" class="max-w-md mx-auto">
            <div class="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-3">
              <div class="flex items-center gap-2 mb-1">
                <div class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
                <span class="text-xs text-blue-600 dark:text-blue-400">正在播放</span>
              </div>
              <p class="text-sm text-gray-700 dark:text-gray-300">{{ currentPlayingText }}</p>
            </div>
          </div>
          
          <!-- 语音识别进度条 -->
          <div v-if="connectionState === 'processing'" class="w-full max-w-xs mx-auto">
            <Progress :value="processingProgress" class="h-2" />
            <p class="text-xs text-gray-500 mt-1">正在处理语音...</p>
          </div>
        </div>

        <!-- 通话控制 -->
        <div class="flex justify-center">
          <div v-if="!isConnected">
            <Button
              @click="handleConnect"
              size="lg"
              class="rounded-full w-20 h-20 bg-green-500 hover:bg-green-600 shadow-lg transition-all duration-200 hover:scale-105"
              :disabled="connectionState === 'connecting'"
            >
              <Phone class="h-8 w-8" />
            </Button>
          </div>
          <div v-else class="flex items-center gap-6">
            <!-- 录音按钮 -->
            <Button
              @click="handleRecording"
              :variant="isRecording ? 'destructive' : 'default'"
              size="lg"
              class="rounded-full w-16 h-16 shadow-lg transition-all duration-200 hover:scale-105"
              :disabled="!canRecord && !isRecording"
            >
              <Mic v-if="!isRecording" class="h-6 w-6" />
              <Square v-else class="h-6 w-6" />
            </Button>

            <!-- 断开连接 -->
            <Button
              @click="handleDisconnect"
              size="lg"
              variant="destructive"
              class="rounded-full w-16 h-16 shadow-lg transition-all duration-200 hover:scale-105"
            >
              <PhoneOff class="h-6 w-6" />
            </Button>

            <!-- 停止播放 -->
            <Button
              @click="handleStopAudio"
              :variant="isAIPlaying ? 'default' : 'outline'"
              size="lg"
              class="rounded-full w-14 h-14 shadow-lg transition-all duration-200 hover:scale-105"
              :disabled="!isAIPlaying"
            >
              <VolumeX class="h-5 w-5" />
            </Button>
          </div>
        </div>

        <!-- WebSocket连接状态提示 -->
        <div v-if="connectionState === 'connecting'" class="flex justify-center">
          <Alert class="max-w-md">
            <AlertTriangle class="h-4 w-4" />
            <AlertDescription>
              正在连接WebSocket语音服务...
            </AlertDescription>
          </Alert>
        </div>

        <!-- 错误提示 -->
        <div v-if="errorMessage" class="flex justify-center">
          <Alert variant="destructive" class="max-w-md">
            <AlertTriangle class="h-4 w-4" />
            <AlertDescription>
              {{ errorMessage }}
            </AlertDescription>
          </Alert>
        </div>

        <!-- 使用提示 -->
        <Card v-if="!isConnected" class="bg-white/80 dark:bg-gray-800/80 backdrop-blur border-0 shadow-lg">
          <CardContent class="p-6">
            <div class="text-center space-y-4">
              <div class="flex items-center justify-center gap-2 mb-3">
                <Mic class="h-5 w-5 text-blue-500" />
                <span class="font-medium text-gray-700 dark:text-gray-300">
                  点击绿色按钮连接WebSocket语音服务
                </span>
              </div>
              
              <div class="flex items-center justify-center gap-6 text-xs text-gray-500">
                <div class="flex items-center gap-2">
                  <div class="w-2 h-2 rounded-full bg-green-500"></div>
                  <span>WebSocket流式传输</span>
                </div>
                <div class="flex items-center gap-2">
                  <div class="w-2 h-2 rounded-full bg-blue-500"></div>
                  <span>{{ messages.length }} 条消息</span>
                </div>
                <div class="flex items-center gap-2">
                  <div class="w-2 h-2 rounded-full bg-purple-500"></div>
                  <span>零延迟传输</span>
                </div>
              </div>
              
              <!-- 功能特性 -->
              <div class="grid grid-cols-2 gap-3 mt-4 text-xs text-gray-600 dark:text-gray-400">
                <div class="flex items-center gap-2">
                  <Zap class="h-3 w-3 text-yellow-500" />
                  <span>无base64编码</span>
                </div>
                <div class="flex items-center gap-2">
                  <Heart class="h-3 w-3 text-red-500" />
                  <span>二进制传输</span>
                </div>
                <div class="flex items-center gap-2">
                  <Globe class="h-3 w-3 text-green-500" />
                  <span>实时流式</span>
                </div>
                <div class="flex items-center gap-2">
                  <Shield class="h-3 w-3 text-blue-500" />
                  <span>高性能</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- 消息历史 -->
        <Card v-if="messages.length > 0" class="bg-white/80 dark:bg-gray-800/80 backdrop-blur border-0 shadow-lg">
          <CardContent class="p-4">
            <div class="space-y-3 max-h-60 overflow-y-auto">
              <div 
                v-for="message in recentMessages" 
                :key="message.id"
                :class="[
                  'flex gap-3 p-3 rounded-lg',
                  message.isUser 
                    ? 'bg-blue-50 dark:bg-blue-900/30 ml-8' 
                    : 'bg-gray-50 dark:bg-gray-700/30 mr-8'
                ]"
              >
                <Avatar class="w-8 h-8 flex-shrink-0">
                  <div 
                    :class="[
                      'w-full h-full rounded-full flex items-center justify-center',
                      message.isUser ? 'bg-blue-500' : 'bg-gray-600'
                    ]"
                  >
                    <User v-if="message.isUser" class="h-4 w-4 !text-white" />
                    <Bot v-else class="h-4 w-4 !text-white" />
                  </div>
                </Avatar>
                <div class="flex-1 min-w-0">
                  <p class="text-sm text-gray-700 dark:text-gray-300 break-words">
                    {{ message.content }}
                  </p>
                  <p class="text-xs text-gray-500 mt-1">
                    {{ formatTime(message.timestamp) }}
                  </p>
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
import { computed, onMounted, ref, watch } from 'vue'
import {
  Bot,
  Phone,
  PhoneOff,
  VolumeX,
  User,
  Mic,
  AlertTriangle,
  Zap,
  Heart,
  Globe,
  Shield,
  Square
} from 'lucide-vue-next'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar } from '@/components/ui/avatar'
import Progress from '@/components/ui/Progress.vue'
import Alert from '@/components/ui/Alert.vue'
import AlertDescription from '@/components/ui/AlertDescription.vue'
import { formatTime } from '@/utils/voice-utils'
import { useWebSocketVoice } from '@/composables/useWebSocketVoice'
import type { VoiceMessage, CallState } from '@/types'

// WebSocket配置
const WEBSOCKET_URL = 'ws://localhost:3001/api/lm/voice/ws/voice'

// 状态管理
const messages = ref<VoiceMessage[]>([])
const errorMessage = ref('')
const processingProgress = ref(0)

// WebSocket语音客户端
const {
  connectionState,
  isConnected,
  isRecording,
  isAIPlaying,
  currentPlayingText,
  canRecord,
  connect,
  disconnect,
  startRecording,
  stopRecording,
  stopAudio
} = useWebSocketVoice({
  url: WEBSOCKET_URL,
  sessionId: `simple-voice-${Date.now()}`,
  language: 'auto',
  onMessage: (message: VoiceMessage) => {
    messages.value.push(message)
    console.log('收到消息:', message)
  },
  onStatusChange: (status: CallState) => {
    console.log('状态变化:', status)
  },
  onError: (error: Error) => {
    errorMessage.value = error.message
    console.error('WebSocket错误:', error)
    setTimeout(() => {
      errorMessage.value = ''
    }, 5000)
  }
})

// 最近的6条消息
const recentMessages = computed(() => {
  return messages.value.slice(-6)
})

// 获取状态变体
function getStatusVariant() {
  switch (connectionState.value) {
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

// 获取状态文本
function getStatusText() {
  switch (connectionState.value) {
    case 'idle':
      return '未连接'
    case 'connecting':
      return '连接中...'
    case 'connected':
      return '已连接'
    case 'listening':
      return '正在录音'
    case 'speaking':
      return 'AI回复中'
    case 'processing':
      return '处理中...'
    default:
      return '未知状态'
  }
}

// 处理连接
async function handleConnect() {
  try {
    errorMessage.value = ''
    await connect()
  } catch (error: any) {
    errorMessage.value = error.message
  }
}

// 处理断开连接
function handleDisconnect() {
  disconnect()
  errorMessage.value = ''
}

// 处理录音
async function handleRecording() {
  try {
    if (isRecording.value) {
      stopRecording()
    } else {
      await startRecording()
    }
  } catch (error: any) {
    errorMessage.value = error.message
  }
}

// 处理停止音频
function handleStopAudio() {
  stopAudio()
}

// 模拟处理进度
function simulateProcessingProgress() {
  if (connectionState.value === 'processing') {
    processingProgress.value = 0
    const interval = setInterval(() => {
      processingProgress.value += 10
      if (processingProgress.value >= 100 || connectionState.value !== 'processing') {
        clearInterval(interval)
        processingProgress.value = 0
      }
    }, 100)
  }
}

// 监听状态变化
watch(connectionState, (newState: CallState) => {
  if (newState === 'processing') {
    simulateProcessingProgress()
  }
})

onMounted(() => {
  console.log('SimpleVoiceChatView mounted - WebSocket流式传输模式')
})
</script> 