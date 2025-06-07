<template>
  <div class="relative" ref="dropdownRef">
    <!-- 用户头像触发器 -->
    <button
      @click="toggleDropdown"
      class="flex items-center space-x-3 text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring transition-all duration-200 hover:shadow-md"
    >
      <div class="relative">
        <img
          :src="userAvatar"
          :alt="userDisplayName"
          class="w-8 h-8 rounded-full object-cover border-2 border-card shadow-sm"
        />
        <div
          v-if="authStore.isLoggedIn"
          class="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 border-2 border-card rounded-full"
          title="在线"
        ></div>
      </div>
      <span class="font-medium text-foreground hidden sm:block">{{ userDisplayName }}</span>
      <svg
        class="w-4 h-4 text-muted-foreground transition-transform duration-200"
        :class="{ 'rotate-180': isDropdownOpen }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- 下拉菜单 -->
    <Transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <div
        v-if="isDropdownOpen"
        class="absolute right-0 z-50 mt-2 w-80 bg-popover rounded-lg shadow-lg ring-1 ring-border ring-opacity-5 focus:outline-none"
      >
        <div class="p-4">
          <!-- 用户信息头部 -->
          <div class="flex items-center space-x-4 mb-4 pb-4 border-b border-border">
            <div class="relative">
              <img
                :src="userAvatar"
                :alt="userDisplayName"
                class="w-12 h-12 rounded-full object-cover border-2 border-border"
              />
              <!-- 上传头像按钮 -->
              <label
                for="avatar-upload"
                class="absolute -bottom-1 -right-1 w-6 h-6 bg-primary rounded-full flex items-center justify-center cursor-pointer hover:bg-primary/80 transition-colors duration-200"
                title="更换头像"
              >
                <svg class="w-3 h-3 text-primary-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </label>
              <input
                id="avatar-upload"
                type="file"
                accept="image/*"
                @change="handleAvatarUpload"
                class="hidden"
              />
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="text-lg font-semibold text-popover-foreground truncate">{{ userDisplayName }}</h3>
              <p class="text-sm text-muted-foreground truncate">{{ authStore.userProfile?.email || '未设置邮箱' }}</p>
              <div class="flex flex-wrap gap-1 mt-1">
                <span
                  v-for="role in authStore.userRoles"
                  :key="role"
                  class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary/10 text-primary"
                >
                  {{ role }}
                </span>
              </div>
            </div>
          </div>

          <!-- 用户详细信息 -->
          <div v-if="authStore.userProfile" class="space-y-3 mb-4 pb-4 border-b border-border">
            <div class="flex items-center justify-between text-sm">
              <span class="text-muted-foreground">用户名</span>
              <span class="text-popover-foreground font-medium">{{ authStore.userProfile.userName }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-muted-foreground">昵称</span>
              <span class="text-popover-foreground font-medium">{{ authStore.userProfile.nickName || '未设置' }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-muted-foreground">手机号</span>
              <span class="text-popover-foreground font-medium">{{ authStore.userProfile.phonenumber || '未设置' }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-muted-foreground">部门</span>
              <span class="text-popover-foreground font-medium">{{ authStore.userProfile.dept?.deptName || '未分配' }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-muted-foreground">创建时间</span>
              <span class="text-popover-foreground font-medium">{{ formatDate(authStore.userProfile.createTime) }}</span>
            </div>
          </div>

          <!-- 快捷操作 -->
          <div class="space-y-2">
            <button
              @click="openProfile"
              class="w-full flex items-center px-3 py-2 text-sm text-popover-foreground rounded-md hover:bg-accent hover:text-accent-foreground transition-colors duration-200"
            >
              <svg class="w-4 h-4 mr-3 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              个人资料
            </button>
            <button
              @click="openSettings"
              class="w-full flex items-center px-3 py-2 text-sm text-popover-foreground rounded-md hover:bg-accent hover:text-accent-foreground transition-colors duration-200"
            >
              <svg class="w-4 h-4 mr-3 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              系统设置
            </button>
            <div class="border-t border-border pt-2">
              <button
                @click="handleLogout"
                :disabled="authStore.isLoading"
                class="w-full flex items-center px-3 py-2 text-sm text-destructive rounded-md hover:bg-destructive/10 transition-colors duration-200 disabled:opacity-50"
              >
                <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                {{ authStore.isLoading ? '退出中...' : '退出登录' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 状态
const isDropdownOpen = ref(false)
const dropdownRef = ref<HTMLElement>()

// 计算属性
const userDisplayName = computed(() => {
  if (!authStore.isLoggedIn) {
    return '未登录'
  }
  return authStore.userProfile?.nickName || authStore.userProfile?.userName || '用户'
})

const userAvatar = computed(() => {
  if (!authStore.isLoggedIn) {
    return '/default-avatar.svg'
  }
  return authStore.userProfile?.avatar || '/default-avatar.svg'
})

// 方法
const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const closeDropdown = () => {
  isDropdownOpen.value = false
}

// 处理头像上传
const handleAvatarUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return

  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件')
    return
  }

  // 验证文件大小（限制为2MB）
  if (file.size > 2 * 1024 * 1024) {
    alert('图片大小不能超过2MB')
    return
  }

  try {
    const result = await authStore.uploadUserAvatar(file)
    if (result.success) {
      alert('头像上传成功')
    } else {
      alert(result.message || '头像上传失败')
    }
  } catch (error) {
    console.error('头像上传失败:', error)
    alert('头像上传失败')
  }

  // 清空文件输入
  target.value = ''
}

// 打开个人资料
const openProfile = () => {
  closeDropdown()
  // TODO: 跳转到个人资料页面
  console.log('打开个人资料')
}

// 打开系统设置
const openSettings = () => {
  closeDropdown()
  // TODO: 跳转到系统设置页面
  console.log('打开系统设置')
}

// 处理退出登录
const handleLogout = async () => {
  try {
    await authStore.logout()
    closeDropdown()
    // 跳转到登录页面
    await router.push('/login')
  } catch (error) {
    console.error('退出登录失败:', error)
  }
}

// 格式化日期
const formatDate = (dateString?: string): string => {
  if (!dateString) return '未知'
  try {
    return new Date(dateString).toLocaleDateString('zh-CN')
  } catch {
    return '未知'
  }
}

// 点击外部关闭下拉菜单
const handleClickOutside = (event: Event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* 自定义样式 */
.rotate-180 {
  transform: rotate(180deg);
}
</style> 