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
                <Bot class="h-16 w-16 text-white" />
              </div>
            </Avatar>
            
            <!-- 说话动画 -->
            <div 
              v-if="isAIPlaying" 
              class="absolute inset-0 rounded-full border-4 border-blue-300 animate-ping"
            />
            
            <!-- 录音指示器 -->
            <div 
              v-if="callState === 'listening'" 
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
            AI 语音助手
          </h2>
          <Badge 
            :variant="getStatusVariant()" 
            class="text-sm px-3 py-1"
          >
            {{ getStatusText() }}
          </Badge>
          
          <!-- 语音识别进度条 -->
          <div v-if="callState === 'processing'" class="w-full max-w-xs mx-auto">
            <Progress :value="processingProgress" class="h-2" />
            <p class="text-xs text-gray-500 mt-1">正在处理语音...</p>
          </div>
        </div>

        <!-- 通话控制 -->
        <div class="flex justify-center">
          <div v-if="callState === 'idle'">
            <Button
              @click="handleStartCall"
              size="lg"
              class="rounded-full w-20 h-20 bg-green-500 hover:bg-green-600 shadow-lg transition-all duration-200 hover:scale-105"
              :disabled="!canStartCall"
            >
              <Phone class="h-8 w-8" />
            </Button>
          </div>
          <div v-else class="flex items-center gap-6">
            <!-- 结束通话 -->
            <Button
              @click="endCall"
              size="lg"
              variant="destructive"
              class="rounded-full w-16 h-16 shadow-lg transition-all duration-200 hover:scale-105"
            >
              <PhoneOff class="h-6 w-6" />
            </Button>

            <!-- 静音 -->
            <Button
              @click="toggleMute"
              :variant="isMuted ? 'default' : 'outline'"
              size="lg"
              class="rounded-full w-14 h-14 shadow-lg transition-all duration-200 hover:scale-105"
            >
              <Volume2 v-if="!isMuted" class="h-5 w-5" />
              <VolumeX v-else class="h-5 w-5" />
            </Button>
          </div>
        </div>

        <!-- 语音引擎状态提示 -->
        <div v-if="!funAudioAvailable" class="flex justify-center">
          <Alert variant="destructive" class="max-w-md">
            <AlertTriangle class="h-4 w-4" />
            <AlertDescription>
              语音引擎不可用，请检查后端服务状态
            </AlertDescription>
          </Alert>
        </div>


        <!-- 使用提示 -->
        <Card v-if="callState === 'idle'" class="bg-white/80 dark:bg-gray-800/80 backdrop-blur border-0 shadow-lg">
          <CardContent class="p-6">
            <div class="text-center space-y-4">
              <div class="flex items-center justify-center gap-2 mb-3">
                <Mic class="h-5 w-5 text-blue-500" />
                <span class="font-medium text-gray-700 dark:text-gray-300">
                  点击绿色按钮开始语音对话
                </span>
              </div>
              
              <div class="flex items-center justify-center gap-6 text-xs text-gray-500">
                <div class="flex items-center gap-2">
                  <div class="w-2 h-2 rounded-full bg-green-500"></div>
                  <span>FunAudioLLM</span>
                </div>
                <div class="flex items-center gap-2">
                  <div class="w-2 h-2 rounded-full bg-blue-500"></div>
                  <span>{{ conversationRounds }} 轮对话</span>
                </div>
                <div class="flex items-center gap-2">
                  <div class="w-2 h-2 rounded-full bg-purple-500"></div>
                  <span>高性能识别</span>
                </div>
              </div>
              
              <!-- 功能特性 -->
              <div class="grid grid-cols-2 gap-3 mt-4 text-xs text-gray-600 dark:text-gray-400">
                <div class="flex items-center gap-2">
                  <Zap class="h-3 w-3 text-yellow-500" />
                  <span>比Whisper快15倍</span>
                </div>
                <div class="flex items-center gap-2">
                  <Heart class="h-3 w-3 text-red-500" />
                  <span>情感识别</span>
                </div>
                <div class="flex items-center gap-2">
                  <Globe class="h-3 w-3 text-green-500" />
                  <span>多语言支持</span>
                </div>
                <div class="flex items-center gap-2">
                  <Shield class="h-3 w-3 text-blue-500" />
                  <span>隐私保护</span>
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
import { storeToRefs } from 'pinia'
import {
  Bot,
  Phone,
  PhoneOff,
  Volume2,
  VolumeX,
  User,
  Mic,
  AlertTriangle,
  Zap,
  Heart,
  Globe,
  Shield
} from 'lucide-vue-next'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import Progress from '@/components/ui/Progress.vue'
import Alert from '@/components/ui/Alert.vue'
import AlertDescription from '@/components/ui/AlertDescription.vue'
import { useVoiceStore } from '@/stores/voice'
import { formatTime } from '@/utils/voice-utils'

const voiceStore = useVoiceStore()
const {
  messages,
  callState,
  isAIPlaying,
  isMuted,
  conversationRounds,
  canStartCall,
  funAudioAvailable
} = storeToRefs(voiceStore)

const {
  checkServiceStatus,
  startCall,
  endCall,
  toggleMute,
  getStatusText
} = voiceStore

// 处理进度
const processingProgress = ref(0)

// 最近的6条消息
const recentMessages = computed(() => {
  return messages.value.slice(-6)
})

// 获取状态变体
function getStatusVariant() {
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

// 处理开始通话
async function handleStartCall() {
  try {
    await startCall()
  } catch (error: any) {
    alert(error.message)
  }
}

// 模拟处理进度
function simulateProcessingProgress() {
  if (callState.value === 'processing') {
    processingProgress.value = 0
    const interval = setInterval(() => {
      processingProgress.value += 10
      if (processingProgress.value >= 100 || callState.value !== 'processing') {
        clearInterval(interval)
        processingProgress.value = 0
      }
    }, 100)
  }
}

// 监听状态变化
watch(callState, (newState: string) => {
  if (newState === 'processing') {
    simulateProcessingProgress()
  }
})

onMounted(() => {
  checkServiceStatus()
})
</script> 