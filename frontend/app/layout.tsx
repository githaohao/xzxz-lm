import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'TZ-LM 多模态聊天系统',
  description: '基于LM Studio的智能多模态聊天助手，支持PDF扫描、图片识别、语音对话',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>
        {children}
      </body>
    </html>
  )
}