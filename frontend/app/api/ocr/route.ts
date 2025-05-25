import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const filePath = formData.get('file_path') as string

    if (!filePath) {
      return NextResponse.json(
        { error: '没有找到文件路径' },
        { status: 400 }
      )
    }

    // 转发到后端OCR API
    const backendFormData = new FormData()
    backendFormData.append('file_path', filePath)

    const backendResponse = await fetch('http://localhost:8000/api/ocr', {
      method: 'POST',
      body: backendFormData
    })

    if (!backendResponse.ok) {
      const errorData = await backendResponse.text()
      throw new Error(`后端OCR处理失败: ${errorData}`)
    }

    const result = await backendResponse.json()
    
    return NextResponse.json({
      success: true,
      text: result.text,
      message: 'OCR处理成功'
    })

  } catch (error) {
    console.error('OCR处理失败:', error)
    return NextResponse.json(
      { 
        error: error instanceof Error ? error.message : 'OCR处理失败',
        success: false
      },
      { status: 500 }
    )
  }
}
