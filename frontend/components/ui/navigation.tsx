'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { MessageCircle, Phone, Bot } from 'lucide-react'

export default function Navigation() {
  const pathname = usePathname()

  const navItems = [
    {
      href: '/',
      label: '文本聊天',
      icon: MessageCircle,
      description: '支持文件上传、OCR识别的智能聊天'
    },
    {
      href: '/voice-chat',
      label: '语音通话',
      icon: Phone,
      description: '实时语音对话，支持中途打断'
    }
  ]

  return (
    <Card className="mb-6">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Bot className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">TZ-LM 多模态AI助手</h1>
          </div>
          <div className="text-sm text-muted-foreground">
            基于 Qwen3-32B 模型
          </div>
        </div>
        
        <div className="flex gap-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            
            return (
              <Link key={item.href} href={item.href}>
                <Button
                  variant={isActive ? "default" : "outline"}
                  className="flex items-center gap-2 h-auto p-3"
                >
                  <Icon className="h-4 w-4" />
                  <div className="text-left">
                    <div className="font-medium">{item.label}</div>
                    <div className="text-xs opacity-70">{item.description}</div>
                  </div>
                </Button>
              </Link>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
} 