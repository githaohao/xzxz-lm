<script setup lang="ts">
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import { MetricsCard } from '@/components/ui/metrics-card'
import { CodeBlock } from '@/components/ui/code-block'
import { StatusBadge } from '@/components/ui/status-badge'
import { DashboardLayout } from '@/components/ui/dashboard-layout'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import { ThemeSelector } from '@/components/ui/theme-selector'

const sidebarCollapsed = ref(false)
const showSidebar = ref(true)

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const sampleCode = `import { xai } from '@x.ai/sdk'

const client = xai({
  apiKey: process.env.XAI_API_KEY
})

async function chat() {
  const response = await client.chat.completions.create({
    model: 'grok-beta',
    messages: [
      { role: 'user', content: 'Hello, Grok!' }
    ]
  })
  
  return response.choices[0].message.content
}`
</script>

<template>
  <DashboardLayout 
    :sidebar-collapsed="sidebarCollapsed"
    :show-sidebar="showSidebar"
    @toggle-sidebar="toggleSidebar"
  >
    <!-- 侧边栏内容 -->
    <template #sidebar-content>
      <nav class="space-y-2">
        <a href="#" class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-sidebar-accent text-sidebar-foreground">
          <span class="text-sm">📊</span>
          <span v-if="!sidebarCollapsed" class="text-sm">仪表板</span>
        </a>
        <a href="#" class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-sidebar-accent text-sidebar-foreground">
          <span class="text-sm">🔑</span>
          <span v-if="!sidebarCollapsed" class="text-sm">API 密钥</span>
        </a>
        <a href="#" class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-sidebar-accent text-sidebar-foreground">
          <span class="text-sm">📈</span>
          <span v-if="!sidebarCollapsed" class="text-sm">使用统计</span>
        </a>
        <a href="#" class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-sidebar-accent text-sidebar-foreground">
          <span class="text-sm">💰</span>
          <span v-if="!sidebarCollapsed" class="text-sm">费用管理</span>
        </a>
      </nav>
    </template>

    <!-- 头部右侧 -->
    <template #header-right>
      <StatusBadge status="online" text="系统正常" />
      <ThemeSelector />
      <Button variant="gradient" size="sm">
        新建项目
      </Button>
    </template>

    <!-- 主要内容 -->
    <div class="space-y-8">
      <!-- 页面标题 -->
      <div class="space-y-2">
        <h1 class="text-3xl font-bold gradient-text">
          x.ai 风格组件库展示
        </h1>
        <p class="text-muted-foreground">
          基于 x.ai/grok 设计风格优化的现代化组件库
        </p>
      </div>

      <!-- 指标卡片展示 -->
      <section class="space-y-4">
        <h2 class="text-xl font-semibold">指标卡片 (MetricsCard)</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricsCard
            title="API 调用"
            value="12,847"
            subtitle="本月总计"
            icon="📊"
            trend="up"
            trend-value="+12.3%"
            :gradient="true"
          />
          <MetricsCard
            title="活跃用户"
            value="1,234"
            subtitle="当前在线"
            icon="👥"
            trend="up"
            trend-value="+5.2%"
            badge="实时"
            badge-variant="secondary"
          />
          <MetricsCard
            title="成本"
            value="$89.42"
            subtitle="本月花费"
            icon="💰"
            trend="down"
            trend-value="-3.1%"
          />
          <MetricsCard
            title="响应时间"
            value="142ms"
            subtitle="平均延迟"
            icon="⚡"
            trend="neutral"
            trend-value="稳定"
          />
        </div>
      </section>

      <!-- 按钮变体展示 -->
      <section class="space-y-4">
        <h2 class="text-xl font-semibold">按钮变体 (Button)</h2>
        <div class="flex flex-wrap gap-4">
          <Button variant="default">默认按钮</Button>
          <Button variant="gradient">渐变按钮</Button>
          <Button variant="gradient-secondary">次要渐变</Button>
          <Button variant="neon">霓虹效果</Button>
          <Button variant="outline">轮廓按钮</Button>
          <Button variant="ghost">幽灵按钮</Button>
        </div>
      </section>

      <!-- 状态指示器展示 -->
      <section class="space-y-4">
        <h2 class="text-xl font-semibold">状态指示器 (StatusBadge)</h2>
        <div class="flex flex-wrap gap-4">
          <StatusBadge status="online" />
          <StatusBadge status="offline" />
          <StatusBadge status="warning" />
          <StatusBadge status="error" />
          <StatusBadge status="processing" />
        </div>
        
        <div class="flex flex-wrap gap-4">
          <StatusBadge status="online" size="sm" />
          <StatusBadge status="warning" size="md" />
          <StatusBadge status="error" size="lg" />
        </div>
      </section>

      <!-- 主题切换器展示 -->
      <section class="space-y-4">
        <h2 class="text-xl font-semibold">主题切换器</h2>
        
        <div class="space-y-6">
          <!-- 简单切换器 -->
          <div>
            <h3 class="text-sm font-medium mb-3">简单切换器 (ThemeToggle)</h3>
            <div class="flex flex-wrap gap-4 items-center">
              <ThemeToggle />
              <p class="text-sm text-muted-foreground">
                点击切换主题：浅色 → 深色 → 跟随系统
              </p>
            </div>
          </div>
          
          <!-- 下拉选择器 -->
          <div>
            <h3 class="text-sm font-medium mb-3">下拉选择器 (ThemeSelector)</h3>
            <div class="flex flex-wrap gap-4 items-center">
              <ThemeSelector />
              <p class="text-sm text-muted-foreground">
                点击打开下拉菜单选择主题模式
              </p>
            </div>
          </div>
        </div>
        
        <div class="p-4 rounded-lg border border-border/50 bg-muted/20">
          <h3 class="text-sm font-medium mb-2">功能特性：</h3>
          <ul class="text-sm text-muted-foreground space-y-1">
            <li>• 支持浅色、深色、跟随系统三种模式</li>
            <li>• 自动检测系统主题变化并实时更新</li>
            <li>• 本地存储用户偏好设置</li>
            <li>• 实时切换，无需刷新页面</li>
            <li>• 响应式设计，移动端友好</li>
          </ul>
        </div>
      </section>

      <!-- 代码块展示 -->
      <section class="space-y-4">
        <h2 class="text-xl font-semibold">代码块 (CodeBlock)</h2>
        <CodeBlock
          :code="sampleCode"
          language="javascript"
          filename="xai-example.js"
        />
      </section>

      <!-- 颜色主题展示 -->
      <section class="space-y-4">
        <h2 class="text-xl font-semibold">颜色主题</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div class="space-y-2">
            <div class="w-full h-16 bg-primary rounded-lg"></div>
            <p class="text-sm text-center">Primary</p>
          </div>
          <div class="space-y-2">
            <div class="w-full h-16 bg-secondary rounded-lg"></div>
            <p class="text-sm text-center">Secondary</p>
          </div>
          <div class="space-y-2">
            <div class="w-full h-16 bg-accent rounded-lg"></div>
            <p class="text-sm text-center">Accent</p>
          </div>
          <div class="space-y-2">
            <div class="w-full h-16 bg-muted rounded-lg"></div>
            <p class="text-sm text-center">Muted</p>
          </div>
          <div class="space-y-2">
            <div class="w-full h-16 bg-gradient-to-r from-primary to-blue-600 rounded-lg"></div>
            <p class="text-sm text-center">渐变主色</p>
          </div>
          <div class="space-y-2">
            <div class="w-full h-16 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-lg"></div>
            <p class="text-sm text-center">渐变次色</p>
          </div>
        </div>
      </section>
    </div>
  </DashboardLayout>
</template> 