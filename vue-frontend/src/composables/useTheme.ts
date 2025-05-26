import { ref, onMounted, onUnmounted, watch, readonly } from 'vue'

export type Theme = 'light' | 'dark' | 'system'

const theme = ref<Theme>('system')
const isDark = ref(false)

// 全局状态，避免重复初始化
let isInitialized = false
let mediaQuery: MediaQueryList | null = null

export function useTheme() {
  // 检测系统主题
  const getSystemTheme = () => {
    if (typeof window === 'undefined') return 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }

  // 应用主题到DOM
  const applyTheme = (currentTheme: Theme) => {
    if (typeof document === 'undefined') return
    
    const root = document.documentElement
    
    if (currentTheme === 'system') {
      const systemTheme = getSystemTheme()
      isDark.value = systemTheme === 'dark'
      
      if (systemTheme === 'dark') {
        root.classList.add('dark')
        root.classList.remove('light')
      } else {
        root.classList.add('light')
        root.classList.remove('dark')
      }
    } else {
      isDark.value = currentTheme === 'dark'
      
      if (currentTheme === 'dark') {
        root.classList.add('dark')
        root.classList.remove('light')
      } else {
        root.classList.add('light')
        root.classList.remove('dark')
      }
    }
  }

  // 设置主题
  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme
    try {
      localStorage.setItem('theme', newTheme)
    } catch (error) {
      console.warn('无法保存主题设置到localStorage:', error)
    }
    applyTheme(newTheme)
  }

  // 切换主题
  const toggleTheme = () => {
    const themes: Theme[] = ['light', 'dark', 'system']
    const currentIndex = themes.indexOf(theme.value)
    const nextTheme = themes[(currentIndex + 1) % themes.length]
    setTheme(nextTheme)
  }

  // 监听系统主题变化
  const handleSystemThemeChange = () => {
    if (theme.value === 'system') {
      applyTheme('system')
    }
  }

  onMounted(() => {
    if (isInitialized) return
    
    // 从localStorage读取保存的主题设置
    let savedTheme: Theme = 'system'
    try {
      const stored = localStorage.getItem('theme') as Theme
      if (stored && ['light', 'dark', 'system'].includes(stored)) {
        savedTheme = stored
      }
    } catch (error) {
      console.warn('无法从localStorage读取主题设置:', error)
    }
    
    theme.value = savedTheme

    // 应用初始主题
    applyTheme(theme.value)

    // 监听系统主题变化
    if (typeof window !== 'undefined') {
      mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      mediaQuery.addEventListener('change', handleSystemThemeChange)
    }
    
    isInitialized = true
  })

  onUnmounted(() => {
    // 清理事件监听器
    if (mediaQuery) {
      mediaQuery.removeEventListener('change', handleSystemThemeChange)
    }
  })

  // 监听主题变化
  watch(theme, (newTheme) => {
    applyTheme(newTheme)
  })

  return {
    theme: readonly(theme),
    isDark: readonly(isDark),
    setTheme,
    toggleTheme,
    getSystemTheme
  }
} 