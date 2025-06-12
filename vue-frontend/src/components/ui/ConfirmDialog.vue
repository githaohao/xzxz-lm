<template>
  <Dialog v-model:open="isOpen">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2">
          <div class="flex h-10 w-10 items-center justify-center rounded-full" :class="iconBackgroundClass">
            <component :is="iconComponent" class="h-6 w-6" :class="iconClass" />
          </div>
          <span>{{ title }}</span>
        </DialogTitle>
      </DialogHeader>
      <div class="space-y-4">
        <div>
          <p class="text-sm text-slate-600 dark:text-slate-400 mb-2">
            {{ description }}
          </p>
          <div v-if="details" class="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border">
            <p class="text-sm font-medium text-slate-900 dark:text-slate-100">
              {{ details }}
            </p>
            <p v-if="subDetails" class="text-xs text-slate-500 mt-1">
              {{ subDetails }}
            </p>
          </div>
          <p v-if="warningText" class="text-xs mt-2" :class="warningClass">
            ⚠️ {{ warningText }}
          </p>
        </div>
        <div class="flex justify-end gap-2">
          <Button variant="outline" @click="cancel">{{ cancelText }}</Button>
          <Button :variant="confirmVariant" @click="confirm" :disabled="loading">
            <component v-if="loading" :is="Loader2" class="h-4 w-4 mr-1 animate-spin" />
            <component v-else-if="confirmIcon" :is="confirmIcon" class="h-4 w-4 mr-1" />
            {{ confirmText }}
          </Button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { 
  AlertTriangle, 
  Trash2, 
  X,
  Loader2,
  type LucideIcon
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'

// Props
interface Props {
  open?: boolean
  title?: string
  description?: string
  details?: string
  subDetails?: string
  warningText?: string
  confirmText?: string
  cancelText?: string
  type?: 'danger' | 'warning' | 'info'
  loading?: boolean
  confirmIcon?: LucideIcon
}

const props = withDefaults(defineProps<Props>(), {
  open: false,
  title: '确认操作',
  description: '确定要执行此操作吗？',
  confirmText: '确认',
  cancelText: '取消',
  type: 'warning',
  loading: false
})

// Emits
const emit = defineEmits<{
  'update:open': [value: boolean]
  'confirm': []
  'cancel': []
}>()

// State
const isOpen = ref(props.open)

// 监听外部 open 状态变化
watch(() => props.open, (newVal) => {
  isOpen.value = newVal
})

// 监听内部 open 状态变化并向外发射
watch(isOpen, (newVal) => {
  emit('update:open', newVal)
})

// 计算属性
const iconComponent = computed(() => {
  switch (props.type) {
    case 'danger':
      return X
    case 'warning':
      return AlertTriangle
    default:
      return AlertTriangle
  }
})

const iconBackgroundClass = computed(() => {
  switch (props.type) {
    case 'danger':
      return 'bg-red-100 dark:bg-red-900/20'
    case 'warning':
      return 'bg-amber-100 dark:bg-amber-900/20'
    default:
      return 'bg-blue-100 dark:bg-blue-900/20'
  }
})

const iconClass = computed(() => {
  switch (props.type) {
    case 'danger':
      return 'text-red-600 dark:text-red-400'
    case 'warning':
      return 'text-amber-600 dark:text-amber-400'
    default:
      return 'text-blue-600 dark:text-blue-400'
  }
})

const confirmVariant = computed(() => {
  switch (props.type) {
    case 'danger':
      return 'destructive'
    case 'warning':
      return 'default'
    default:
      return 'default'
  }
})

const warningClass = computed(() => {
  switch (props.type) {
    case 'danger':
      return 'text-red-600 dark:text-red-400'
    case 'warning':
      return 'text-amber-600 dark:text-amber-400'
    default:
      return 'text-blue-600 dark:text-blue-400'
  }
})

// 方法
function confirm() {
  emit('confirm')
}

function cancel() {
  isOpen.value = false
  emit('cancel')
}
</script> 