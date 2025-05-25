<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-6">
    <div class="container mx-auto max-w-6xl">
      <div class="space-y-8">
        <!-- 页面标题 -->
        <div class="text-center">
          <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Shadcn-UI 组件展示
          </h1>
          <p class="text-lg text-gray-600 dark:text-gray-400">
            语音聊天系统的现代化界面组件
          </p>
        </div>

        <!-- 组件展示网格 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- 头像组件 -->
          <Card class="border-0 shadow-lg">
            <CardHeader>
              <CardTitle class="flex items-center gap-2">
                <User class="h-5 w-5 text-blue-500" />
                Avatar 头像组件
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="flex items-center gap-4">
                <Avatar class="w-12 h-12">
                  <AvatarFallback class="bg-blue-500 text-white">
                    <User class="h-6 w-6" />
                  </AvatarFallback>
                </Avatar>
                <Avatar class="w-16 h-16">
                  <AvatarFallback class="bg-green-500 text-white">
                    <Bot class="h-8 w-8" />
                  </AvatarFallback>
                </Avatar>
                <Avatar class="w-20 h-20">
                  <AvatarFallback class="bg-purple-500 text-white">
                    <Mic class="h-10 w-10" />
                  </AvatarFallback>
                </Avatar>
              </div>
            </CardContent>
          </Card>

          <!-- 按钮组件 -->
          <Card class="border-0 shadow-lg">
            <CardHeader>
              <CardTitle class="flex items-center gap-2">
                <MousePointer class="h-5 w-5 text-green-500" />
                Button 按钮组件
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="flex flex-wrap gap-3">
                <Button variant="default">默认按钮</Button>
                <Button variant="destructive">危险按钮</Button>
                <Button variant="outline">轮廓按钮</Button>
                <Button variant="secondary">次要按钮</Button>
              </div>
              <div class="flex gap-3">
                <Button size="sm">小按钮</Button>
                <Button size="lg">大按钮</Button>
                <Button class="rounded-full w-12 h-12">
                  <Phone class="h-5 w-5" />
                </Button>
              </div>
            </CardContent>
          </Card>

          <!-- 徽章组件 -->
          <Card class="border-0 shadow-lg">
            <CardHeader>
              <CardTitle class="flex items-center gap-2">
                <Tag class="h-5 w-5 text-yellow-500" />
                Badge 徽章组件
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="flex flex-wrap gap-3">
                <Badge variant="default">默认</Badge>
                <Badge variant="secondary">次要</Badge>
                <Badge variant="destructive">错误</Badge>
                <Badge variant="outline">轮廓</Badge>
              </div>
              <div class="flex gap-3">
                <Badge class="bg-green-500">在线</Badge>
                <Badge class="bg-yellow-500">处理中</Badge>
                <Badge class="bg-blue-500">连接中</Badge>
              </div>
            </CardContent>
          </Card>

          <!-- 进度条组件 -->
          <Card class="border-0 shadow-lg">
            <CardHeader>
              <CardTitle class="flex items-center gap-2">
                <BarChart3 class="h-5 w-5 text-purple-500" />
                Progress 进度条组件
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="space-y-3">
                <div>
                  <div class="flex justify-between text-sm mb-1">
                    <span>语音识别进度</span>
                    <span>75%</span>
                  </div>
                  <Progress :value="75" class="h-2" />
                </div>
                <div>
                  <div class="flex justify-between text-sm mb-1">
                    <span>处理进度</span>
                    <span>45%</span>
                  </div>
                  <Progress :value="45" class="h-3 bg-blue-100" />
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- 警告组件 -->
          <Card class="border-0 shadow-lg">
            <CardHeader>
              <CardTitle class="flex items-center gap-2">
                <AlertTriangle class="h-5 w-5 text-red-500" />
                Alert 警告组件
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <Alert>
                <Info class="h-4 w-4" />
                <AlertDescription>
                  这是一个信息提示，用于显示重要信息。
                </AlertDescription>
              </Alert>
              <Alert variant="destructive">
                <AlertTriangle class="h-4 w-4" />
                <AlertDescription>
                  这是一个错误警告，语音引擎不可用。
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>

          <!-- 骨架屏组件 -->
          <Card class="border-0 shadow-lg">
            <CardHeader>
              <CardTitle class="flex items-center gap-2">
                <Loader2 class="h-5 w-5 text-gray-500" />
                Skeleton 骨架屏组件
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="space-y-3">
                <div class="flex items-center gap-3">
                  <Skeleton class="w-12 h-12 rounded-full" />
                  <div class="space-y-2 flex-1">
                    <Skeleton class="h-4 w-3/4" />
                    <Skeleton class="h-3 w-1/2" />
                  </div>
                </div>
                <Skeleton class="h-20 w-full rounded-lg" />
                <div class="flex gap-2">
                  <Skeleton class="h-8 w-16 rounded" />
                  <Skeleton class="h-8 w-20 rounded" />
                  <Skeleton class="h-8 w-12 rounded" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- 语音聊天界面预览 -->
        <Card class="border-0 shadow-xl">
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Mic class="h-6 w-6 text-blue-500" />
              语音聊天界面预览
            </CardTitle>
          </CardHeader>
          <CardContent class="p-8">
            <div class="max-w-2xl mx-auto space-y-6">
              <!-- AI头像 -->
              <div class="flex justify-center">
                <div class="relative">
                  <Avatar class="w-24 h-24">
                    <div class="w-full h-full rounded-full bg-gradient-to-r from-blue-500 to-blue-600 flex items-center justify-center">
                      <Bot class="h-12 w-12 text-white" />
                    </div>
                  </Avatar>
                  <div class="absolute -bottom-1 -right-1">
                    <div class="w-6 h-6 bg-green-500 rounded-full border-2 border-white flex items-center justify-center">
                      <div class="w-2 h-2 bg-white rounded-full"></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 状态 -->
              <div class="text-center space-y-2">
                <h3 class="text-xl font-semibold">AI 语音助手</h3>
                <Badge variant="default" class="px-3 py-1">
                  准备就绪
                </Badge>
              </div>

              <!-- 控制按钮 -->
              <div class="flex justify-center gap-4">
                <Button
                  size="lg"
                  class="rounded-full w-16 h-16 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 shadow-lg transition-all duration-200 hover:scale-105"
                >
                  <Phone class="h-6 w-6" />
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  class="rounded-full w-12 h-12 transition-all duration-200 hover:scale-105"
                >
                  <Volume2 class="h-5 w-5" />
                </Button>
              </div>

              <!-- 示例对话 -->
              <div class="space-y-3">
                <div class="flex justify-end">
                  <div class="flex items-start gap-2 max-w-[80%]">
                    <Card class="bg-blue-500 text-white border-blue-500">
                      <CardContent class="p-3">
                        <p class="text-sm">你好，请介绍一下 FunAudioLLM</p>
                      </CardContent>
                    </Card>
                    <Avatar class="w-8 h-8">
                      <AvatarFallback class="bg-blue-500 text-white">
                        <User class="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                  </div>
                </div>
                <div class="flex justify-start">
                  <div class="flex items-start gap-2 max-w-[80%]">
                    <Avatar class="w-8 h-8">
                      <AvatarFallback class="bg-gray-600 text-white">
                        <Bot class="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                    <Card class="bg-white dark:bg-gray-700">
                      <CardContent class="p-3">
                        <p class="text-sm">FunAudioLLM 是一个高性能的语音识别系统，比 Whisper 快 15 倍，支持情感识别和多语言处理。</p>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </div>

              <!-- 功能特性 -->
              <div class="grid grid-cols-2 gap-3 text-xs text-gray-600 dark:text-gray-400">
                <div class="flex items-center gap-2">
                  <Zap class="h-3 w-3 text-yellow-500" />
                  <span>高速识别</span>
                </div>
                <div class="flex items-center gap-2">
                  <Heart class="h-3 w-3 text-red-500" />
                  <span>情感分析</span>
                </div>
                <div class="flex items-center gap-2">
                  <Globe class="h-3 w-3 text-green-500" />
                  <span>多语言</span>
                </div>
                <div class="flex items-center gap-2">
                  <Shield class="h-3 w-3 text-blue-500" />
                  <span>隐私保护</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  User,
  Bot,
  Mic,
  Phone,
  Volume2,
  MousePointer,
  Tag,
  BarChart3,
  AlertTriangle,
  Info,
  Loader2,
  Zap,
  Heart,
  Globe,
  Shield
} from 'lucide-vue-next'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import Progress from '@/components/ui/Progress.vue'
import Alert from '@/components/ui/Alert.vue'
import AlertDescription from '@/components/ui/AlertDescription.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
</script> 