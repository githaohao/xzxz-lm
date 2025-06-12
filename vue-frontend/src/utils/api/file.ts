import type { ProcessedFile, RAGSearchRequest, RAGSearchResponse, RAGDocument } from '@/types'
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
 * 获取所有RAG文档列表
 */
export async function getAllDocuments(): Promise<any> {
  return api.get(API_CONFIG.ENDPOINTS.RAG_DOCUMENTS)
}

/**
 * 删除RAG文档
 */
export async function deleteDocument(docId: string): Promise<boolean> {
  try {
    await api.delete(`${API_CONFIG.ENDPOINTS.RAG_DOCUMENTS}/${docId}`)
    return true
  } catch (error) {
    console.error('删除文档失败:', error)
    return false
  }
}

/**
 * RAG文档检索
 */
export async function searchDocuments(request: RAGSearchRequest): Promise<RAGSearchResponse> {
  return api.post<RAGSearchResponse>(API_CONFIG.ENDPOINTS.RAG_SEARCH, request)
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

/**
 * 获取文档信息
 */
export async function getDocumentInfo(docId: string): Promise<any> {
  return api.get(`${API_CONFIG.ENDPOINTS.RAG_DOCUMENTS}/${docId}`)
}

/**
 * 获取文档分块内容
 */
export async function getDocumentChunks(docId: string): Promise<any> {
  return api.get(`${API_CONFIG.ENDPOINTS.RAG_DOCUMENTS}/${docId}/chunks`)
}

/**
 * 获取会话关联的文档列表
 */
export async function getSessionDocuments(sessionId: string): Promise<RAGDocument[]> {
  try {
    const response = await api.get<any>(`/api/lm/chat/sessions/${sessionId}/documents`)
    
    if (response.code === 200 && response.data) {
      return response.data.map((doc: any) => ({
        doc_id: doc.doc_id,
        filename: doc.filename,
        file_type: doc.file_type,
        chunk_count: doc.chunk_count,
        total_length: doc.file_size || 0,
        created_at: doc.upload_time
      }))
    }
    
    return []
  } catch (error) {
    console.error('获取会话文档失败:', error)
    return []
  }
} 