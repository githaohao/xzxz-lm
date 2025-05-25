import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const { text, voice = 'zh-CN-XiaoxiaoNeural', rate = 1.0, pitch = 1.0 } = await request.json()
    
    if (!text) {
      return NextResponse.json(
        { error: '未提供文本内容' },
        { status: 400 }
      )
    }

    // 将文本发送到后端进行语音合成
    const response = await fetch('http://localhost:8000/api/voice/speech/synthesize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        voice,
        rate,
        pitch
      }),
    })

    if (!response.ok) {
      throw new Error(`后端语音合成失败: ${response.statusText}`)
    }

    // 返回音频流
    const audioBuffer = await response.arrayBuffer()
    
    return new NextResponse(audioBuffer, {
      headers: {
        'Content-Type': 'audio/wav',
        'Content-Length': audioBuffer.byteLength.toString(),
      },
    })

  } catch (error) {
    console.error('语音合成API错误:', error)
    return NextResponse.json(
      { 
        error: '语音合成失败',
        details: error instanceof Error ? error.message : '未知错误'
      },
      { status: 500 }
    )
  }
} 