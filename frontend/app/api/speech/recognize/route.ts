import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const audioFile = formData.get('audio') as File
    
    if (!audioFile) {
      return NextResponse.json(
        { error: '未提供音频文件' },
        { status: 400 }
      )
    }

    // 将音频文件转发到后端进行处理
    const backendFormData = new FormData()
    backendFormData.append('audio', audioFile)

    const response = await fetch('http://localhost:8000/api/speech/recognize', {
      method: 'POST',
      body: backendFormData,
    })

    if (!response.ok) {
      throw new Error(`后端语音识别失败: ${response.statusText}`)
    }

    const result = await response.json()
    return NextResponse.json(result)

  } catch (error) {
    console.error('语音识别API错误:', error)
    return NextResponse.json(
      { 
        error: '语音识别失败',
        details: error instanceof Error ? error.message : '未知错误'
      },
      { status: 500 }
    )
  }
} 