import type { ProcessedFile } from '@/types'
import { API_CONFIG } from '../api-config'
import { api } from './client'

/**
 * 文件上传和处理 - 支持PDF智能检测
 */
export async function uploadFile(file: File, sessionId?: string): Promise<ProcessedFile> {
  const formData = new FormData()
  formData.append('file', file)
  if (sessionId) {
    formData.append('session_id', sessionId)
  }

  try {
    // 使用新的智能上传接口，支持PDF自动检测和处理
    const uploadResult = await api.upload<any>(
      API_CONFIG.ENDPOINTS.UPLOAD,
      formData,
      API_CONFIG.TIMEOUT.UPLOAD
    )

    console.log('📁 文件上传结果:', uploadResult)

    // 转换后端响应为前端ProcessedFile格式
    const processedFile: ProcessedFile = {
      name: uploadResult.file_name || file.name,
      size: uploadResult.file_size || file.size,
      type: uploadResult.file_type || file.type,
      content: uploadResult.text_content,
      doc_id: uploadResult.doc_id,
      rag_enabled: uploadResult.rag_processed || false,
      ocrCompleted: true, // 后端已完成所有处理
      processing: false,  // 处理已完成
      // PDF智能处理字段
      is_pdf: uploadResult.is_pdf || false,
      is_text_pdf: uploadResult.is_text_pdf,
      char_count: uploadResult.char_count,
      processing_status: uploadResult.processing_status,
      rag_processed: uploadResult.rag_processed || false
    }

    // 如果是PDF文件，记录处理状态
    if (uploadResult.is_pdf) {
      if (uploadResult.is_text_pdf === true) {
        console.log('✅ 文本PDF处理完成:', {
          fileName: file.name,
          charCount: uploadResult.char_count,
          docId: uploadResult.doc_id,
          ragProcessed: uploadResult.rag_processed
        })
      } else if (uploadResult.is_text_pdf === false) {
        console.log('🔍 扫描PDF OCR处理完成:', {
          fileName: file.name,
          charCount: uploadResult.char_count,
          docId: uploadResult.doc_id,
          ragProcessed: uploadResult.rag_processed,
          status: uploadResult.processing_status
        })
      }
    }

    return processedFile

  } catch (error) {
    console.error('❌ 文件上传失败:', error)

    // 如果是网络错误或服务器错误，返回基础文件信息
    return {
      name: file.name,
      size: file.size,
      type: file.type,
      processing: false,
      ocrCompleted: false,
      rag_enabled: false,
      is_pdf: file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf'),
      processing_status: '上传失败: ' + (error instanceof Error ? error.message : '未知错误')
    }
  }
}

/**
 * 处理文档进行RAG索引
 */
export async function processDocumentForRAG(
  content: string,
  filename: string,
  fileType: string
): Promise<string> {
  const formData = new FormData()
  formData.append('content', content)
  formData.append('filename', filename)
  formData.append('file_type', fileType)

  const response = await api.upload<any>(
    API_CONFIG.ENDPOINTS.RAG_PROCESS,
    formData,
    API_CONFIG.TIMEOUT.RAG
  )
  return response.doc_id
}