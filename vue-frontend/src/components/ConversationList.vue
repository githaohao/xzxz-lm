<template>
  <!-- 包装所有内容在一个根元素中以解决 v-show 指令警告 -->
  <div>
    <div class="h-full flex flex-col bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700">
      <!-- 顶部操作栏 -->
      <div class="p-4 border-b border-slate-200 dark:border-slate-700">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">对话列表</h2>
          <Button 
            @click="createNewConversation" 
            size="sm" 
            class="h-8 px-3"
          >
            <Plus class="h-4 w-4 mr-1" />
            新建
          </Button>
        </div>
        
        <!-- 搜索框 -->
        <div class="relative">
          <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索对话..."
            class="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 dark:border-slate-600 rounded-lg bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      <!-- 对话列表 -->
      <div class="flex-1 overflow-y-auto scrollbar-thin scrollbar-track-slate-100 scrollbar-thumb-slate-300 dark:scrollbar-track-slate-800 dark:scrollbar-thumb-slate-600 hover:scrollbar-thumb-slate-400 dark:hover:scrollbar-thumb-slate-500">
        <div v-if="filteredConversations.length === 0" class="flex items-center justify-center min-h-[200px] p-8 text-center text-slate-500">
          <div>
            <MessageCircle class="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p class="text-sm">{{ searchQuery ? '未找到匹配的对话' : '暂无对话' }}</p>
            <p v-if="!searchQuery" class="text-xs mt-1 opacity-75">点击"新建"按钮开始第一个对话</p>
          </div>
        </div>
        
        <div 
          v-for="conversation in filteredConversations"
          :key="conversation.id"
          :class="[
            'group relative p-4 border-b border-slate-100 dark:border-slate-800 cursor-pointer transition-colors',
            conversation.isActive 
              ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-l-blue-500' 
              : 'hover:bg-slate-50 dark:hover:bg-slate-800'
          ]"
          @click="selectConversation(conversation.id)"
        >
          <!-- 对话内容 -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-1">
              <h3 
                class="text-sm font-medium text-slate-900 dark:text-slate-100 truncate"
                :class="{ 'text-blue-700 dark:text-blue-300': conversation.isActive }"
              >
                {{ conversation.title }}
              </h3>
              <time class="text-xs text-slate-500 ml-2 flex-shrink-0">
                {{ formatTime(conversation.updatedAt) }}
              </time>
            </div>
            
            <p v-if="conversation.lastMessage" class="text-xs text-slate-600 dark:text-slate-400 truncate">
              {{ conversation.lastMessage }}
            </p>
            
            <div class="flex items-center gap-2 mt-2">
              <Badge variant="secondary" class="text-xs">
                {{ conversation.messageCount }} 条消息
              </Badge>
              <Badge 
                v-if="getConversationRagDocsCount(conversation.id) > 0" 
                variant="outline" 
                class="text-xs text-purple-600 border-purple-300"
              >
                📚 {{ getConversationRagDocsCount(conversation.id) }} 个文档
              </Badge>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" class="h-6 w-6 p-0">
                  <MoreVertical class="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem @click.stop="editConversationTitle(conversation.id)">
                  <Edit2 class="h-4 w-4 mr-2" />
                  重命名
                </DropdownMenuItem>
                <DropdownMenuItem @click.stop="clearConversationMessages(conversation.id)">
                  <Trash2 class="h-4 w-4 mr-2" />
                  清空消息
                </DropdownMenuItem>
                <DropdownMenuItem 
                  @click.stop="deleteConversation(conversation.id)"
                  class="text-red-600 focus:text-red-600"
                >
                  <X class="h-4 w-4 mr-2" />
                  删除对话
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      <!-- 底部统计 -->
      <div class="p-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-center">
        <p class="text-xs text-slate-500">
          总计 {{ conversationStore.conversations.length }} 个对话
        </p>
      </div>
    </div>

    <!-- 重命名对话框 -->
    <Dialog v-model:open="showRenameDialog">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>重命名对话</DialogTitle>
        </DialogHeader>
        <div class="space-y-4">
          <div>
            <label class="text-sm font-medium text-slate-700 dark:text-slate-300">对话标题</label>
            <input
              v-model="newTitle"
              type="text"
              class="mt-1 block w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="输入新的对话标题"
              @keyup.enter="confirmRename"
            />
          </div>
          <div class="flex justify-end gap-2">
            <Button variant="outline" @click="showRenameDialog = false">取消</Button>
            <Button @click="confirmRename">确认</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { 
  Plus, 
  Search, 
  MessageCircle, 
  MoreVertical, 
  Edit2, 
  Trash2, 
  X 
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { useConversationStore } from '@/stores/conversation'
import { useChatHistoryStore } from '@/stores/chatHistory'
import { useChatStore } from '@/stores/chat'

const conversationStore = useConversationStore()
const chatHistoryStore = useChatHistoryStore()
const chatStore = useChatStore()
const { conversations } = storeToRefs(conversationStore)

// 状态
const searchQuery = ref('')
const showRenameDialog = ref(false)
const editingConversationId = ref<string | null>(null)
const newTitle = ref('')

// 计算属性
const filteredConversations = computed(() => {
  if (!searchQuery.value.trim()) {
    return conversations.value
  }
  
  const query = searchQuery.value.toLowerCase()
  return conversations.value.filter(conv =>
    conv.title.toLowerCase().includes(query) ||
    conv.lastMessage?.toLowerCase().includes(query)
  )
})

// 方法
async function createNewConversation() {
  try {
    // 1. 先创建本地对话
    const newConv = conversationStore.createConversation()
    console.log('✅ 创建本地对话:', newConv.title)

    // 2. 如果启用了历史同步，调用后端API创建聊天会话
    if (chatStore.isHistorySyncEnabled) {
      console.log('🔄 正在创建远程聊天会话...')
      
      const sessionData = {
        title: newConv.title,
        description: '多模态AI智能聊天对话',
        tags: ['chat', 'ai', 'conversation']
      }

      const remoteSession = await chatHistoryStore.createSession(sessionData)
      
      if (remoteSession) {
        // 将远程会话ID关联到本地对话
        conversationStore.updateConversationHistorySession(newConv.id, remoteSession.id)
        console.log('✅ 远程聊天会话创建成功:', remoteSession.id)
      } else {
        console.warn('⚠️ 远程聊天会话创建失败，仅保留本地对话')
      }
    } else {
      console.log('📝 历史同步已禁用，仅创建本地对话')
    }

  } catch (error) {
    console.error('❌ 创建对话时出错:', error)
    // 即使后端调用失败，也不影响本地对话的使用
  }
}

function selectConversation(conversationId: string) {
  conversationStore.setCurrentConversation(conversationId)
}

function getConversationRagDocsCount(conversationId: string): number {
  const data = conversationStore.conversationData.get(conversationId)
  return data?.ragDocuments.length || 0
}

function editConversationTitle(conversationId: string) {
  const conversation = conversations.value.find(c => c.id === conversationId)
  if (conversation) {
    editingConversationId.value = conversationId
    newTitle.value = conversation.title
    showRenameDialog.value = true
  }
}

function confirmRename() {
  if (editingConversationId.value && newTitle.value.trim()) {
    conversationStore.updateConversationTitle(editingConversationId.value, newTitle.value.trim())
    showRenameDialog.value = false
    editingConversationId.value = null
    newTitle.value = ''
  }
}

function clearConversationMessages(conversationId: string) {
  if (confirm('确定要清空此对话的所有消息吗？')) {
    conversationStore.clearConversationMessages(conversationId)
  }
}

function deleteConversation(conversationId: string) {
  const conversation = conversations.value.find(c => c.id === conversationId)
  if (conversation && confirm(`确定要删除对话"${conversation.title}"吗？`)) {
    conversationStore.deleteConversation(conversationId)
  }
}

function formatTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script> 