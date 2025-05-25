import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    // 获取FormData
    const formData = await request.formData()
    
    console.log('🔄 代理多模态流式请求到后端')
    
    // 代理到后端API
    const response = await fetch('http://localhost:8000/api/chat/multimodal/stream/response', {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }

    // 创建流式响应
    const stream = new ReadableStream({
      start(controller) {
        const reader = response.body?.getReader()
        if (!reader) {
          controller.close()
          return
        }

        const decoder = new TextDecoder()

        function pump(): Promise<void> {
          return reader.read().then(({ done, value }) => {
            if (done) {
              controller.close()
              return
            }

            const chunk = decoder.decode(value, { stream: true })
            controller.enqueue(new TextEncoder().encode(chunk))
            return pump()
          })
        }

        return pump()
      },
    })

    return new NextResponse(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    })
  } catch (error) {
    console.error('❌ API Route Error:', error)
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    )
  }
}
