import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    
    // 转发到后端API
    const backendResponse = await fetch('http://localhost:8000/api/voice/wake-word', {
      method: 'POST',
      body: formData,
    })
    
    const result = await backendResponse.json()
    
    return NextResponse.json(result, { 
      status: backendResponse.status 
    })
  } catch (error) {
    console.error('唤醒词检测API错误:', error)
    return NextResponse.json(
      { 
        success: false, 
        wake_word_detected: false,
        error: '唤醒词检测服务异常',
        confidence: 0.0
      },
      { status: 500 }
    )
  }
} 