<template>
  <div class="container mx-auto p-4 max-w-4xl">
    <div class="space-y-4">
      <!-- 处理状态显示 -->
      <div v-if="processingStatus" class="text-center">
        <Badge variant="outline" class="px-4 py-2">
          <Loader2 class="h-4 w-4 mr-2 animate-spin" />
          {{ processingStatus }}
        </Badge>
      </div>

      <!-- 文件处理状态 -->
      <div v-if="processedFile" class="mb-4">
        <Card>
          <CardContent class="p-4">
            <div class="flex items-center gap-2 text-sm">
              <Paperclip class="h-4 w-4" />
              <span>{{ processedFile.name }}</span>
              <Badge variant="outline" class="text-xs">
                {{ formatFileSize(processedFile.size) }}
              </Badge>
              <Button 
                variant="ghost" 
                size="sm" 
                @click="setProcessedFile(null)"
                class="ml-auto"
              >
                <X class="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- 消息列表 -->
      <div class="space-y-4 min-h-[400px] max-h-[600px] overflow-y-auto">
        <!-- 历史消息 -->
        <div
          v-for="message in messages"
          :key="message.id"
          :class="[
            'flex gap-3 max-w-4xl',
            message.isUser ? 'ml-auto flex-row-reverse' : ''
          ]"
        >
          <!-- 头像 -->
          <div class="flex-shrink-0">
            <div 
              :class="[
                'w-8 h-8 rounded-full flex items-center justify-center',
                message.isUser ? 'bg-primary' : 'bg-blue-600'
              ]"
            >
              <User v-if="message.isUser" class="h-4 w-4 text-primary-foreground" />
              <Bot v-else class="h-4 w-4 text-white" />
            </div>
          </div>

          <div :class="['flex flex-col gap-2 max-w-[80%]', message.isUser ? 'items-end' : 'items-start']">
            <!-- 文件信息 -->
            <Card v-if="message.fileInfo" class="p-2">
              <div class="flex items-center gap-2 text-sm">
                <Paperclip class="h-4 w-4" />
                <span>{{ message.fileInfo.name }}</span>
                <Badge variant="outline" class="text-xs">
                  {{ formatFileSize(message.fileInfo.size) }}
                </Badge>
              </div>
            </Card>

            <!-- 消息内容 -->
            <Card :class="message.isUser ? 'bg-primary text-primary-foreground' : ''">
              <CardContent class="p-3">
                <div v-if="!message.isUser && hasThinkTags(message.content)" class="space-y-2">
                  <!-- 思考内容（可折叠） -->
                  <details class="group">
                    <summary class="cursor-pointer text-sm text-muted-foreground hover:text-foreground">
                      🤔 查看思考过程
                    </summary>
                    <div class="mt-2 p-2 bg-muted rounded text-sm whitespace-pre-wrap">
                      {{ extractThinkContent(message.content).think }}
                    </div>
                  </details>
                  <!-- 实际回复内容 -->
                  <div class="whitespace-pre-wrap break-words">
                    {{ extractThinkContent(message.content).content }}
                  </div>
                </div>
                <div v-else class="whitespace-pre-wrap break-words">
                  {{ message.content }}
                </div>
              </CardContent>
            </Card>

            <!-- 时间戳 -->
            <div class="text-xs text-muted-foreground">
              {{ formatTime(message.timestamp) }}
            </div>
          </div>
        </div>

        <!-- 当前流式消息 -->
        <div
          v-if="currentStreamingMessage"
          class="flex gap-3 max-w-4xl"
        >
          <div class="flex-shrink-0">
            <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
              <Bot class="h-4 w-4 text-white" />
            </div>
          </div>

          <div class="flex flex-col gap-2 max-w-[80%] items-start">
            <Card>
              <CardContent class="p-3">
                <div class="whitespace-pre-wrap break-words">
                  {{ currentStreamingMessage.content }}
                  <span v-if="currentStreamingMessage.isStreaming" class="animate-pulse">▋</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <Card>
        <CardContent class="p-4">
          <div class="flex gap-2">
            <div class="flex-1 relative">
              <Textarea
                v-model="inputMessage"
                placeholder="输入消息，支持拖拽文件..."
                class="min-h-[52px] max-h-32 resize-none pr-12"
                :disabled="isLoading"
                @keydown.enter.exact.prevent="handleSend"
                @drop.prevent="handleFileDrop"
                @dragover.prevent
              />
              
              <input
                ref="fileInput"
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.wav,.mp3"
                @change="handleFileSelect"
                class="hidden"
              />
              <Button
                variant="ghost"
                size="icon"
                class="absolute right-2 top-2 h-8 w-8"
                @click="fileInput?.click()"
                :disabled="isLoading"
              >
                <Paperclip class="h-4 w-4" />
              </Button>
            </div>

            <Button
              v-if="isLoading"
              variant="destructive"
              @click="cancelRequest"
            >
              取消
            </Button>
            <Button
              v-else
              @click="handleSend"
              :disabled="(!inputMessage.trim() && !processedFile) || isLoading"
            >
              <Send class="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { 
  Send, 
  Paperclip, 
  Bot, 
  User, 
  Loader2,
  X
} from 'lucide-vue-next'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Textarea from '@/components/ui/Textarea.vue'
import { useChatStore } from '@/stores/chat'
import { formatTime, formatFileSize, hasThinkTags, extractThinkContent } from '@/utils'
import { uploadFile } from '@/utils/api'

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

// 发送消息
async function handleSend() {
  if (!inputMessage.value.trim() && !processedFile.value) return

  await sendMessage(inputMessage.value, processedFile.value || undefined)
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
  const file = event.dataTransfer?.files[0]
  if (file) {
    await processFile(file)
  }
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
    setProcessedFile(result)
    
    console.log('✅ 文件处理完成:', result)
  } catch (error: any) {
    console.error('❌ 文件处理失败:', error)
    setProcessedFile(null)
    alert(`文件处理失败: ${error.message}`)
  }
}
</script> 