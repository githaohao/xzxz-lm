<template>
  <div class="min-h-full overflow-y-auto">
    <div class="container mx-auto p-4 max-w-4xl">
      <div class="text-center mb-8">
        <h1 class="text-4xl font-bold text-primary mb-4">
          小智小智 多模态聊天系统
        </h1>
        <p class="text-lg text-muted-foreground mb-8">
          基于 Vue 3.5 + TypeScript 构建的智能对话平台
        </p>
      </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
      <!-- 文本聊天卡片 -->
      <Card class="hover:shadow-lg transition-shadow cursor-pointer" @click="$router.push('/chat')">
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <MessageSquare class="h-6 w-6" />
            文本聊天
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p class="text-muted-foreground mb-4">
            支持文本对话、文件上传、OCR识别等多模态功能
          </p>
          <ul class="text-sm space-y-1">
            <li>• 实时流式响应</li>
            <li>• PDF/图片文件支持</li>
            <li>• OCR文字识别</li>
            <li>• 思考过程展示</li>
          </ul>
        </CardContent>
      </Card>

      <!-- 语音聊天卡片 -->
      <Card class="hover:shadow-lg transition-shadow cursor-pointer" @click="$router.push('/voice-chat')">
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Mic class="h-6 w-6" />
            语音聊天
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p class="text-muted-foreground mb-4">
            完整的语音对话体验，支持语音识别和语音合成
          </p>
          <ul class="text-sm space-y-1">
            <li>• FunAudioLLM引擎</li>
            <li>• 实时语音识别</li>
            <li>• TTS语音合成</li>
            <li>• 智能语音打断</li>
          </ul>
        </CardContent>
      </Card>

      <!-- 简洁语音卡片 -->
      <Card class="hover:shadow-lg transition-shadow cursor-pointer" @click="$router.push('/simple-voice-chat')">
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Phone class="h-6 w-6" />
            简洁语音
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p class="text-muted-foreground mb-4">
            类似ChatGPT的简洁语音通话界面
          </p>
          <ul class="text-sm space-y-1">
            <li>• 简洁设计风格</li>
            <li>• 按住说话模式</li>
            <li>• 动画效果</li>
            <li>• 移动端适配</li>
          </ul>
        </CardContent>
      </Card>
    </div>

    <!-- 系统状态 -->
    <Card>
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <Activity class="h-6 w-6" />
          系统状态
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="flex items-center justify-between p-3 bg-muted rounded-lg">
            <span class="font-medium">后端服务</span>
            <Badge :variant="backendStatus ? 'default' : 'destructive'">
              {{ backendStatus ? '正常' : '离线' }}
            </Badge>
          </div>
          <div class="flex items-center justify-between p-3 bg-muted rounded-lg">
            <span class="font-medium">FunAudioLLM</span>
            <Badge :variant="audioStatus ? 'default' : 'destructive'">
              {{ audioStatus ? '可用' : '不可用' }}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 功能特性 -->
    <div class="mt-8">
      <h2 class="text-2xl font-bold mb-6 text-center">核心特性</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
            <Zap class="h-4 w-4 text-primary-foreground" />
          </div>
          <div>
            <h3 class="font-semibold mb-2">实时流式响应</h3>
            <p class="text-muted-foreground text-sm">
              支持Server-Sent Events流式响应，实时显示AI思考和回复过程
            </p>
          </div>
        </div>

        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
            <FileText class="h-4 w-4 text-primary-foreground" />
          </div>
          <div>
            <h3 class="font-semibold mb-2">多模态支持</h3>
            <p class="text-muted-foreground text-sm">
              支持PDF文档、图片文件上传，自动OCR识别文字内容
            </p>
          </div>
        </div>

        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
            <Volume2 class="h-4 w-4 text-primary-foreground" />
          </div>
          <div>
            <h3 class="font-semibold mb-2">高性能语音</h3>
            <p class="text-muted-foreground text-sm">
              基于SenseVoice模型，比Whisper快15倍的语音识别速度
            </p>
          </div>
        </div>

        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
            <Smartphone class="h-4 w-4 text-primary-foreground" />
          </div>
          <div>
            <h3 class="font-semibold mb-2">响应式设计</h3>
            <p class="text-muted-foreground text-sm">
              完全响应式设计，支持桌面端和移动端的完美体验
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
  </div>  
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  MessageSquare, 
  Mic, 
  Phone, 
  Activity, 
  Zap, 
  FileText, 
  Volume2, 
  Smartphone 
} from 'lucide-vue-next'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { healthCheck, checkFunAudioStatus } from '@/utils/api'

const backendStatus = ref(false)
const audioStatus = ref(false)

// 检查系统状态
async function checkSystemStatus() {
  try {
    await healthCheck()
    backendStatus.value = true
  } catch (error) {
    console.error('后端服务检查失败:', error)
    backendStatus.value = false
  }

  try {
    audioStatus.value = await checkFunAudioStatus()
  } catch (error) {
    console.error('FunAudioLLM状态检查失败:', error)
    audioStatus.value = false
  }
}

onMounted(() => {
  checkSystemStatus()
})
</script> 