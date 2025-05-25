import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/voice/engine`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('FunAudioLLM引擎状态检查失败:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'FunAudioLLM引擎状态检查失败',
        engine: {
          status: {
            available: false
          }
        }
      },
      { status: 500 }
    )
  }
} 