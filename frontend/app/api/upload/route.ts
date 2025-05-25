import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File

    if (!file) {
      return NextResponse.json(
        { error: '没有找到文件' },
        { status: 400 }
      )
    }

    // 转发到后端上传API
    const backendFormData = new FormData()
    backendFormData.append('file', file)

    const backendResponse = await fetch('http://localhost:8000/api/upload', {
      method: 'POST',
      body: backendFormData
    })

    if (!backendResponse.ok) {
      const errorData = await backendResponse.text()
      throw new Error(`后端上传失败: ${errorData}`)
    }

    const result = await backendResponse.json()
    
    return NextResponse.json({
      success: true,
      file_path: result.file_path,
      message: '文件上传成功'
    })

  } catch (error) {
    console.error('文件上传失败:', error)
    return NextResponse.json(
      { 
        error: error instanceof Error ? error.message : '文件上传失败',
        success: false
      },
      { status: 500 }
    )
  }
}
