<template>
  <div class="flex h-full bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
    <!-- 对话列表面板 -->
    <div 
      :class="[
        'transition-all duration-300 ease-in-out flex-shrink-0',
        showConversationList ? 'w-72' : 'w-0'
      ]"
    >
      <ConversationList v-show="showConversationList" />
    </div>

    <!-- 主要内容区域 -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- 顶部工具栏 -->
      <div class="flex items-center justify-between p-3 border-b border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
        <div class="flex items-center gap-3">
          <button
            @click="toggleConversationList"
            class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            :title="showConversationList ? '隐藏对话列表' : '显示对话列表'"
          >
            <MessageSquare class="h-5 w-5 text-slate-600 dark:text-slate-400" />
          </button>
          <button
            @click="openDocumentDialog"
            class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="文档管理"
          >
            <FileText class="h-5 w-5 text-slate-600 dark:text-slate-400" />
          </button>
          <button
            @click="openKnowledgeBaseManager"
            class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="知识库管理"
          >
            <Database class="h-5 w-5 text-slate-600 dark:text-slate-400" />
          </button>
          <div class="flex flex-col">
            <h1 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {{ conversationStore.currentConversation?.title || '智能对话' }}
            </h1>
            <div v-if="conversationStore.currentConversation" class="flex items-center gap-2 text-xs text-slate-500">
              <span>{{ conversationStore.currentConversation.messageCount }} 条消息</span>
              <span v-if="conversationStore.currentConversation.historySessionId" class="flex items-center gap-1">
                <div class="w-1.5 h-1.5 rounded-full bg-green-500"></div>
                <span>已同步</span>
              </span>
              <span v-else-if="isHistorySyncEnabled" class="flex items-center gap-1">
                <div class="w-1.5 h-1.5 rounded-full bg-yellow-500"></div>
                <span>待同步</span>
              </span>
              <span v-else class="flex items-center gap-1">
                <CloudOff class="w-3 h-3 text-slate-400" />
                <span>本地模式</span>
              </span>
            </div>
          </div>
        </div>
        
        <div class="flex items-center gap-2">
          <Badge v-if="currentConversationRagDocsCount > 0" variant="outline" class="text-purple-600 border-purple-300">
            📚 {{ currentConversationRagDocsCount }} 个文档
          </Badge>
          <Badge v-if="selectedDocumentCount > 0" variant="outline" class="text-blue-600 border-blue-300">
            📄 已选 {{ selectedDocumentCount }}
          </Badge>
          <Badge v-if="localSelectedKnowledgeBase && !selectedDocumentCount" variant="outline" class="text-green-600 border-green-300">
            🗂️ {{ currentKnowledgeBaseDocumentsCount }} 个知识库文档
          </Badge>
          
          <KnowledgeBaseSelector v-model="localSelectedKnowledgeBase" />
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
                
                <!-- 处理状态 -->
                <div class="flex items-center gap-2 mt-1">
                  <div v-if="processedFile.processing" class="w-1.5 h-1.5 rounded-full bg-yellow-500 animate-pulse"></div>
                  <div v-else class="w-1.5 h-1.5 rounded-full bg-green-500"></div>
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

        <!-- 选中文档显示 -->
        <div v-if="selectedDocumentCount > 0" class="
          flex items-center gap-3 p-3 mb-4
          bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20
          border border-purple-200/50 dark:border-purple-800/50
          rounded-xl shadow-lg backdrop-blur-sm
          transition-all duration-300
        ">
          <!-- 多文档图标 -->
          <div class="flex-shrink-0">
            <div class="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center shadow-sm">
              <FileText class="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
          
          <!-- 文档详情 -->
          <div class="flex-1 min-w-0">
            <p class="font-semibold text-sm text-slate-900 dark:text-slate-100">
              已选择 {{ selectedDocumentCount }} 个文档
            </p>
            <p class="text-xs text-slate-600 dark:text-slate-400 truncate">
              {{ selectedDocumentsList.map(doc => doc.filename).join(', ') }}
            </p>
            
            <!-- RAG状态显示 -->
            <div v-if="ragEnabled" class="flex items-center gap-2 mt-1">
              <div class="w-1.5 h-1.5 rounded-full bg-purple-500"></div>
              <span class="text-xs text-purple-600 dark:text-purple-400 font-medium">
                🧠 多文档智能检索已启用
              </span>
              <Badge variant="secondary" class="text-xs px-1.5 py-0.5">
                多文档RAG
              </Badge>
            </div>
            <div v-else class="flex items-center gap-2 mt-1">
              <div class="w-1.5 h-1.5 rounded-full bg-gray-400"></div>
              <span class="text-xs text-gray-500 dark:text-gray-400 font-medium">
                📄 常规文本模式
              </span>
            </div>
          </div>
          
          <!-- 管理按钮 -->
          <button
            @click="showDocumentDialog = true"
            class="
              flex-shrink-0 p-1.5 rounded-lg
              hover:bg-purple-50 dark:hover:bg-purple-900/20
              text-purple-500 hover:text-purple-600 dark:text-purple-400 dark:hover:text-purple-300
              transition-all duration-200
              focus:outline-none focus:ring-2 focus:ring-purple-500/20
            "
          >
            <Settings class="h-4 w-4" />
          </button>
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
                        <div class="text-xs text-slate-600 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
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

  <!-- RAG文档管理弹窗 -->
  <RAGDocumentDialog 
    v-model:open="showDocumentDialog"
    @preview-document="handlePreviewDocument"
  />

  <!-- 文档预览弹窗 -->
  <DocumentPreviewDialog
    :is-open="showDocumentPreview"
    :document="selectedDocumentForPreview"
    @update:is-open="showDocumentPreview = $event"
  />
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
  PanelLeftClose,
  MessageSquare,
  FileText,
  Database,
  History,
  CloudOff,
  Settings
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
import { formatTime, formatFileSize, hasThinkTags, extractThinkContent } from '@/utils/voice-utils'
import { uploadFile, getDocumentInfo } from '@/utils/api'
import { getRagSuggestion, isFileRagSuitable } from '@/utils/rag-utils'
import RAGDocumentDialog from '@/components/RAGDocumentDialog.vue'
import DocumentPreviewDialog from '@/components/DocumentPreviewDialog.vue'
import ConversationList from '@/components/ConversationList.vue'
import KnowledgeBaseSelector from '@/components/KnowledgeBaseSelector.vue'
import { useConversationStore } from '@/stores/conversation'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import type { RAGDocument, KnowledgeBase } from '@/types'

const chatStore = useChatStore()
const {
  messages,
  isLoading,
  processingStatus,
  currentStreamingMessage,
  processedFile,
  isHistorySyncEnabled
} = storeToRefs(chatStore)

const { 
  sendMessage, 
  cancelRequest, 
  setProcessedFile,
} = chatStore

const inputMessage = ref('')
const fileInput = ref<HTMLInputElement>()
const isDragging = ref(false)
const ragEnabled = ref(true) // 默认启用RAG
const showDocumentDialog = ref(false) // 文档管理弹窗
const showDocumentPreview = ref(false) // 文档预览弹窗
const selectedDocumentForPreview = ref<RAGDocument | null>(null) // 要预览的文档
const showConversationList = ref(true) // 显示对话列表
// RAG Store
const ragStore = useRAGStore()
const { selectedCount: selectedDocumentCount, selectedDocumentsList } = storeToRefs(ragStore)

// 对话Store
const conversationStore = useConversationStore()
const { currentConversationRagDocs } = storeToRefs(conversationStore)

// 知识库Store
const knowledgeBaseStore = useKnowledgeBaseStore()
const { selectedKnowledgeBase, currentKnowledgeBaseDocuments } = storeToRefs(knowledgeBaseStore)

// 本地知识库选择状态（用于KnowledgeBaseSelector组件）
const localSelectedKnowledgeBase = ref<KnowledgeBase | null>(null)

// 计算当前对话的RAG文档数量
const currentConversationRagDocsCount = computed(() => currentConversationRagDocs.value.length)

// 计算当前知识库的文档数量
const currentKnowledgeBaseDocumentsCount = computed(() => currentKnowledgeBaseDocuments.value.length)

// 监听本地知识库选择变化，同步到store
watch(localSelectedKnowledgeBase, (newKb) => {
  knowledgeBaseStore.setSelectedKnowledgeBase(newKb)
})

// 监听store中知识库选择变化，同步到本地
watch(selectedKnowledgeBase, (newKb) => {
  localSelectedKnowledgeBase.value = newKb
})

// 新增：滚动区域引用
const scrollAreaRef = ref<InstanceType<typeof ScrollArea>>()
const isUserScrolling = ref(false)
const scrollTimeout = ref<number | null>(null)
const isAtBottom = ref(true)

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
  
  // 如果有选中的文档，支持多文档处理
  if (selectedDocumentCount.value > 0) {
    const selectedDocs = selectedDocumentsList.value
    if (selectedDocs.length > 0) {
      if (selectedDocs.length === 1) {
        // 单文档处理
        const doc = selectedDocs[0]
        fileToSend = {
          name: doc.filename,
          type: doc.file_type,
          size: doc.total_length,
          content: '', // 内容会在后端检索时获取
          doc_id: doc.doc_id,
          ocrCompleted: true,
          rag_enabled: ragEnabled.value
        }
      } else {
        // 多文档处理 - 将多个文档信息合并
        const docIds = selectedDocs.map(doc => doc.doc_id)
        const totalSize = selectedDocs.reduce((sum, doc) => sum + doc.total_length, 0)
        const docNames = selectedDocs.map(doc => doc.filename).join(', ')
        
        // 创建多文档ProcessedFile，使用JSON格式存储多文档信息
        fileToSend = {
          name: `${selectedDocs.length}个文档: ${docNames}`,
          type: 'multimodal/documents',
          size: totalSize,
          content: '', // 内容会在后端检索时获取
          doc_id: JSON.stringify({
            type: 'multiple',
            doc_ids: docIds,
            documents: selectedDocs.map(doc => ({
              doc_id: doc.doc_id,
              filename: doc.filename,
              file_type: doc.file_type,
              total_length: doc.total_length
            }))
          }),
          ocrCompleted: true,
          rag_enabled: ragEnabled.value
        }
      }
    }
  } else if (localSelectedKnowledgeBase.value) {
    // 如果选择了知识库但没有选中具体文档，使用知识库中的所有文档
    const kbDocuments = currentKnowledgeBaseDocuments.value
    
    if (kbDocuments.length > 0) {
      if (kbDocuments.length === 1) {
        // 单文档处理
        const doc = kbDocuments[0]
        fileToSend = {
          name: doc.filename,
          type: doc.file_type,
          size: doc.total_length,
          content: '', // 内容会在后端检索时获取
          doc_id: doc.doc_id,
          ocrCompleted: true,
          rag_enabled: ragEnabled.value
        }
      } else {
        // 多文档处理 - 使用知识库进行RAG检索
        const totalSize = kbDocuments.reduce((sum, doc) => sum + doc.total_length, 0)
        const kbName = localSelectedKnowledgeBase.value.name
        
        // 创建知识库ProcessedFile，只传递knowledge_base_id
        fileToSend = {
          name: `知识库"${kbName}"(${kbDocuments.length}个文档)`,
          type: 'multimodal/knowledge-base',
          size: totalSize,
          content: '', // 内容会在后端检索时获取
          knowledge_base_id: localSelectedKnowledgeBase.value.id, // 直接使用knowledge_base_id字段
          ocrCompleted: true,
          rag_enabled: ragEnabled.value
        }
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
    setProcessedFile(null)
    
    console.log('📁 开始处理文件:', file.name, '大小:', formatFileSize(file.size))
    
    // 获取当前会话的session_id
    const sessionId = conversationStore.currentConversation?.historySessionId
    
    // 上传并处理文件
    const result = await uploadFile(file, sessionId)
    
    // 设置文件状态
    setProcessedFile(result)
    
    if (result.ocrCompleted && result.doc_id) {
      console.log('✅ 文件处理完成，已自动关联到当前会话:', result)
      
      // 如果有session_id，文档已经在后端自动关联到会话
      if (sessionId) {
        console.log('📚 文档已通过后端自动关联到会话:', sessionId)
      } else {
        console.log('⚠️ 当前会话未关联到云端，文档仅保存在本地')
        
        // 只有在没有session_id时才手动添加到本地对话
        if (conversationStore.currentConversation && result.doc_id) {
          try {
            const docInfo = await getDocumentInfo(result.doc_id)
            
            const uploadedDoc: RAGDocument = {
              doc_id: result.doc_id,
              filename: result.name,
              file_type: result.type,
              chunk_count: docInfo?.chunk_count || 0,
              total_length: docInfo?.total_length || result.size,
              created_at: docInfo?.created_at || new Date().toISOString()
            }
            
            conversationStore.addRagDocumentToConversation(
              conversationStore.currentConversation.id, 
              uploadedDoc
            )
            console.log('📚 文档已手动关联到本地对话:', uploadedDoc.filename)
          } catch (error) {
            console.warn('⚠️ 获取文档信息失败:', error)
          }
        }
      }
    } else {
      console.log('⏳ 文件上传成功，处理中:', result)
    }
  } catch (error: any) {
    console.error('❌ 文件处理失败:', error)
    setProcessedFile(null)
    alert(`文件处理失败: ${error.message}`)
  }
}

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

// 打开文档管理弹窗
function openDocumentDialog() {
  showDocumentDialog.value = true
}

// 切换对话列表显示
function toggleConversationList() {
  showConversationList.value = !showConversationList.value
}

// 计算智能建议
const ragSuggestion = computed(() => {
  if (!processedFile.value?.content || !inputMessage.value) return null
  return getRagSuggestion(inputMessage.value, processedFile.value.content)
})

// 打开知识库管理
function openKnowledgeBaseManager() {
  // 跳转到知识库管理页面
  window.open('/knowledge-base', '_blank')
}

// 处理预览文档
function handlePreviewDocument(document: RAGDocument) {
  console.log('📖 预览文档:', document.filename)
  selectedDocumentForPreview.value = document
  showDocumentPreview.value = true
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
</script>