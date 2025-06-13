<template>
  <Popover v-model:open="isOpen">
    <PopoverTrigger asChild>
      <Button
        variant="outline"
        size="sm"
        class="gap-2 max-w-64"
        :class="selectedKnowledgeBase ? 'text-purple-600 border-purple-300' : ''"
      >
        <Database class="h-4 w-4" />
        <span class="truncate">
          {{ selectedKnowledgeBase ? selectedKnowledgeBase.name : '选择知识库' }}
        </span>
        <ChevronDown class="h-4 w-4 ml-auto" />
      </Button>
    </PopoverTrigger>
    
    <PopoverContent class="w-80 p-0" align="start">
      <div class="p-3 border-b border-slate-200 dark:border-slate-700">
        <h4 class="font-medium text-slate-900 dark:text-slate-100 mb-2">选择知识库</h4>
        <div class="relative">
          <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            v-model="searchQuery"
            placeholder="搜索知识库..."
            class="pl-10"
          />
        </div>
      </div>
      
      <ScrollArea class="max-h-64">
        <div class="p-2">
          <!-- 无知识库选项 -->
          <div
            :class="[
              'flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors',
              !selectedKnowledgeBase
                ? 'bg-blue-50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300'
                : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'
            ]"
            @click="selectKnowledgeBase(null)"
          >
            <div class="w-8 h-8 rounded-lg bg-slate-500 flex items-center justify-center">
              <FileText class="h-4 w-4 text-white" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="font-medium text-sm">无特定知识库</div>
              <div class="text-xs text-slate-500">使用所有可用文档</div>
            </div>
            <Check v-if="!selectedKnowledgeBase" class="h-4 w-4 text-blue-600" />
          </div>
          
          <!-- 知识库列表 -->
          <div
            v-for="kb in filteredKnowledgeBases"
            :key="kb.id"
            :class="[
              'flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors',
              selectedKnowledgeBase?.id === kb.id
                ? 'bg-blue-50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300'
                : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'
            ]"
            @click="selectKnowledgeBase(kb)"
          >
            <div 
              :style="{ backgroundColor: kb.color }"
              class="w-8 h-8 rounded-lg flex items-center justify-center"
            >
              <Database class="h-4 w-4 text-white" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="font-medium text-sm truncate">{{ kb.name }}</span>
                <Badge v-if="kb.isDefault" variant="secondary" class="text-xs">
                  默认
                </Badge>
              </div>
              <div class="text-xs text-slate-500">
                {{ knowledgeBaseStats[kb.id]?.totalDocuments || 0 }} 个文档
                <span v-if="knowledgeBaseStats[kb.id]?.totalDocuments > 1" class="text-purple-600">
                  • 支持全库检索
                </span>
              </div>
            </div>
            <Check v-if="selectedKnowledgeBase?.id === kb.id" class="h-4 w-4 text-blue-600" />
          </div>
          
          <!-- 空状态 -->
          <div v-if="filteredKnowledgeBases.length === 0 && searchQuery" class="p-4 text-center">
            <Search class="h-8 w-8 mx-auto text-slate-300 mb-2" />
            <p class="text-sm text-slate-500">未找到匹配的知识库</p>
          </div>
        </div>
      </ScrollArea>
      
      <div class="p-3 border-t border-slate-200 dark:border-slate-700">
        <Button
          @click="openKnowledgeBaseManager"
          variant="ghost"
          size="sm"
          class="w-full justify-start"
        >
          <Settings class="h-4 w-4 mr-2" />
          管理知识库
        </Button>
      </div>
    </PopoverContent>
  </Popover>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import {
  Database,
  FileText,
  Search,
  Check,
  ChevronDown,
  Settings
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import type { KnowledgeBase } from '@/types'

// Props
interface Props {
  modelValue?: KnowledgeBase | null
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: KnowledgeBase | null]
}>()

// 本地状态
const isOpen = ref(false)
const searchQuery = ref('')

// Store
const knowledgeBaseStore = useKnowledgeBaseStore()
const {
  knowledgeBases,
  knowledgeBaseStats
} = storeToRefs(knowledgeBaseStore)

const { initialize } = knowledgeBaseStore

// 计算属性
const selectedKnowledgeBase = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const filteredKnowledgeBases = computed(() => {
  if (!searchQuery.value) return knowledgeBases.value
  
  const query = searchQuery.value.toLowerCase()
  return knowledgeBases.value.filter(kb =>
    kb.name.toLowerCase().includes(query) ||
    (kb.description && kb.description.toLowerCase().includes(query))
  )
})

// 生命周期
onMounted(async () => {
  await initialize()
})

// 方法
function selectKnowledgeBase(kb: KnowledgeBase | null) {
  selectedKnowledgeBase.value = kb
  isOpen.value = false
  searchQuery.value = ''
}

function openKnowledgeBaseManager() {
  window.open('/knowledge-base', '_blank')
  isOpen.value = false
}
</script> 