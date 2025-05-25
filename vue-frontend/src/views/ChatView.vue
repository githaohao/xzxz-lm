<template>
  <div class="flex flex-col h-full bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
    <!-- 主要内容区域 -->
    <div class="flex-1 container mx-auto px-4 py-6 max-w-4xl flex flex-col">
      <!-- 文件处理状态 -->
      <div v-if="processedFile" class="mb-4">
        <Card class="border-dashed border-2 border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/50">
          <CardContent class="p-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                <Paperclip class="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div class="flex-1">
                <p class="font-medium text-slate-900 dark:text-slate-100">{{ processedFile.name }}</p>
                <p class="text-sm text-slate-500 dark:text-slate-400">{{ formatFileSize(processedFile.size) }}</p>
              </div>
              <Button 
                variant="ghost" 
                size="sm" 
                @click="setProcessedFile(null)"
                class="text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
              >
                <X class="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- 消息列表 -->
      <ScrollArea class="flex-1 pr-4">
        <div class="space-y-6 pb-4">
          <!-- 历史消息 -->
          <div
            v-for="message in messages"
            :key="message.id"
            :class="[
              'flex gap-4 max-w-full',
              message.isUser ? 'flex-row-reverse' : ''
            ]"
          >
            <!-- 头像 -->
            <Avatar class="w-10 h-10 flex-shrink-0">
              <AvatarFallback 
                :class="[
                  'text-white font-medium',
                  message.isUser 
                    ? 'bg-gradient-to-br from-green-500 to-emerald-600' 
                    : 'bg-gradient-to-br from-blue-500 to-purple-600'
                ]"
              >
                <User v-if="message.isUser" class="h-5 w-5" />
                <Bot v-else class="h-5 w-5" />
              </AvatarFallback>
            </Avatar>

            <div :class="['flex flex-col gap-2 max-w-[75%]', message.isUser ? 'items-end' : 'items-start']">
              <!-- 文件信息 -->
              <Card v-if="message.fileInfo" class="border-slate-200 dark:border-slate-700">
                <CardContent class="p-3">
                  <div class="flex items-center gap-2 text-sm">
                    <Paperclip class="h-4 w-4 text-slate-500" />
                    <span class="text-slate-700 dark:text-slate-300">{{ message.fileInfo.name }}</span>
                    <Badge variant="secondary" class="text-xs">
                      {{ formatFileSize(message.fileInfo.size) }}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              <!-- 消息内容 -->
              <Card 
                :class="[
                  'shadow-sm transition-all duration-200 hover:shadow-md',
                  message.isUser 
                    ? 'bg-gradient-to-br from-green-500 to-emerald-600 text-white border-green-200' 
                    : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700'
                ]"
              >
                <CardContent class="p-4">
                  <div v-if="!message.isUser && hasThinkTags(message.content)" class="space-y-3">
                    <!-- 思考内容（可折叠） -->
                    <details class="group">
                      <summary class="cursor-pointer text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 flex items-center gap-2">
                        <span class="text-base">🤔</span>
                        <span>查看思考过程</span>
                        <span class="text-xs opacity-60 group-open:hidden">(点击展开)</span>
                      </summary>
                      <div class="mt-3 p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
                        <div class="text-sm text-slate-600 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
                          {{ extractThinkContent(message.content).think }}
                        </div>
                      </div>
                    </details>
                    
                    <Separator class="my-3" />
                    
                    <!-- 实际回复内容 -->
                    <div class="text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed">
                      {{ extractThinkContent(message.content).content }}
                    </div>
                  </div>
                  <div v-else class="whitespace-pre-wrap leading-relaxed break-words">
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
            class="flex gap-4 max-w-full"
          >
            <Avatar class="w-10 h-10 flex-shrink-0">
              <AvatarFallback class="bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                <Bot class="h-5 w-5" />
              </AvatarFallback>
            </Avatar>

            <div class="flex flex-col gap-2 max-w-[75%] items-start">
              <Card class="bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 shadow-sm">
                <CardContent class="p-4">
                  <div v-if="hasThinkTags(currentStreamingMessage.content)" class="space-y-3">
                    <!-- 思考内容（可折叠） -->
                    <details class="group">
                      <summary class="cursor-pointer text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 flex items-center gap-2">
                        <span class="text-base">🤔</span>
                        <span>查看思考过程</span>
                        <span class="text-xs opacity-60 group-open:hidden">(点击展开)</span>
                      </summary>
                      <div class="mt-3 p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
                        <div class="text-sm text-slate-600 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
                          {{ extractThinkContent(currentStreamingMessage.content).think }}
                          <span v-if="currentStreamingMessage.isStreaming && !extractThinkContent(currentStreamingMessage.content).content" class="inline-block w-2 h-5 bg-blue-500 animate-pulse ml-1">▋</span>
                        </div>
                      </div>
                    </details>
                    
                    <Separator v-if="extractThinkContent(currentStreamingMessage.content).content" class="my-3" />
                    
                    <!-- 实际回复内容 -->
                    <div v-if="extractThinkContent(currentStreamingMessage.content).content" class="text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed">
                      {{ extractThinkContent(currentStreamingMessage.content).content }}
                      <span v-if="currentStreamingMessage.isStreaming" class="inline-block w-2 h-5 bg-blue-500 animate-pulse ml-1">▋</span>
                    </div>
                  </div>
                  <div v-else class="text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed break-words">
                    {{ currentStreamingMessage.content }}
                    <span v-if="currentStreamingMessage.isStreaming" class="inline-block w-2 h-5 bg-blue-500 animate-pulse ml-1">▋</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </ScrollArea>

      <!-- 输入区域 -->
      <div class="mt-5">
        <Card class="border-slate-200 dark:border-slate-700 shadow-lg bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm">
          <CardContent class="p-4">
            <div class="flex gap-3">
              <div class="flex-1 relative">
                <Textarea
                  v-model="inputMessage"
                  placeholder="输入消息，支持拖拽文件..."
                  class="min-h-[60px] max-h-32 resize-none pr-12 border-slate-200 dark:border-slate-700 focus:border-blue-500 dark:focus:border-blue-400 transition-colors"
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
                  size="sm"
                  class="absolute right-2 top-2 h-8 w-8 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
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
                class="px-6"
              >
                <X class="h-4 w-4 mr-2" />
                取消
              </Button>
              <Button
                v-else
                @click="handleSend"
                :disabled="(!inputMessage.trim() && !processedFile) || isLoading"
                class="px-6 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white border-0"
              >
                <Send class="h-4 w-4 mr-2" />
                发送
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
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
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
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