import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    
    // 转发到后端FunAudioLLM服务
    const response = await fetch(`${BACKEND_URL}/api/voice/chat`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('FunAudioLLM语音聊天失败:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'FunAudioLLM语音聊天失败',
        recognized_text: '',
        response: '抱歉，语音处理出现问题。请稍后重试。'
      },
      { status: 500 }
    )
  }
} 