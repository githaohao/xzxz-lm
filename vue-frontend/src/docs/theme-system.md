# 主题系统使用指南

## 概述

我们的组件库支持完整的主题系统，包括浅色模式、深色模式和跟随系统设置。主题系统基于 CSS 变量和 Tailwind CSS 的深色模式实现。

## 主要特性

- 🌙 **深色模式优先**：默认采用深色主题，符合现代 AI 产品的设计趋势
- 🔄 **自动跟随系统**：可以自动检测并跟随用户的系统主题设置
- 💾 **持久化存储**：用户的主题偏好会保存在本地存储中
- ⚡ **实时切换**：主题切换无需刷新页面，实时生效
- 📱 **响应式设计**：在移动端和桌面端都有良好的体验

## 使用方法

### 1. 在组件中使用主题 Hook

```typescript
import { useTheme } from '@/composables/useTheme'

export default {
  setup() {
    const { theme, isDark, setTheme, toggleTheme } = useTheme()
    
    return {
      theme,      // 当前主题：'light' | 'dark' | 'system'
      isDark,     // 是否为深色模式
      setTheme,   // 设置主题
      toggleTheme // 切换主题
    }
  }
}
```

### 2. 使用主题切换组件

#### 简单切换器
```vue
<template>
  <ThemeToggle />
</template>
```

#### 下拉选择器
```vue
<template>
  <ThemeSelector />
</template>
```

### 3. 在CSS中使用主题变量

```css
.my-component {
  background-color: hsl(var(--background));
  color: hsl(var(--foreground));
  border: 1px solid hsl(var(--border));
}
```

### 4. 在Tailwind类中使用

```vue
<template>
  <div class="bg-background text-foreground border border-border">
    内容
  </div>
</template>
```

## 可用的颜色变量

### 基础颜色
- `--background` / `bg-background` - 背景色
- `--foreground` / `text-foreground` - 前景色
- `--border` / `border-border` - 边框色

### 语义化颜色
- `--primary` / `bg-primary` - 主色调
- `--secondary` / `bg-secondary` - 次要色
- `--accent` / `bg-accent` - 强调色
- `--muted` / `bg-muted` - 柔和色
- `--destructive` / `bg-destructive` - 危险色

### 卡片和弹出层
- `--card` / `bg-card` - 卡片背景
- `--popover` / `bg-popover` - 弹出层背景

## 主题配置

### 深色主题（默认）
```css
:root {
  --background: 0 0% 6%;
  --foreground: 0 0% 98%;
  --primary: 210 100% 60%;
  /* ... 其他变量 */
}
```

### 浅色主题
```css
.light {
  --background: 0 0% 100%;
  --foreground: 0 0% 3.9%;
  --primary: 210 100% 50%;
  /* ... 其他变量 */
}
```

## 最佳实践

1. **优先使用语义化颜色**：使用 `bg-primary` 而不是 `bg-blue-500`
2. **测试两种模式**：确保组件在浅色和深色模式下都有良好的视觉效果
3. **使用透明度**：利用 `/50` 等透明度修饰符创建层次感
4. **遵循设计系统**：使用预定义的颜色变量而不是自定义颜色

## 扩展主题

如果需要添加新的颜色变量：

1. 在 `globals.css` 中定义CSS变量
2. 在 `tailwind.config.js` 中添加对应的Tailwind颜色
3. 确保为浅色和深色模式都提供合适的值

```css
/* globals.css */
:root {
  --new-color: 120 100% 50%;
}

.light {
  --new-color: 120 50% 40%;
}
```

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        'new-color': 'hsl(var(--new-color))'
      }
    }
  }
}
``` 