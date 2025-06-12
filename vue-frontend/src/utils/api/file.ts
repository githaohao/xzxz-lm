import type { ProcessedFile, RAGSearchRequest, RAGSearchResponse } from '@/types'
import { API_CONFIG } from '../api-config'
import { api } from './client'

/**
 * 文件上传和处理
 */
export async function uploadFile(file: File): Promise<ProcessedFile> {
  const formData = new FormData()
  formData.append('file', file)

  // 1. 先上传文件
  const uploadResult = await api.upload<any>(
    API_CONFIG.ENDPOINTS.UPLOAD, 
    formData, 
    API_CONFIG.TIMEOUT.UPLOAD
  )

  let ocrCompleted = false
  let content: string | undefined = undefined
  let docId: string | undefined = undefined
  let ragEnabled = false

  // 2. 如果是支持OCR的文件类型，进行OCR处理
  const fileExt = file.name.toLowerCase().split('.').pop()
  if (fileExt && ['pdf', 'png', 'jpg', 'jpeg'].includes(fileExt)) {
    try {
      const ocrFormData = new FormData()
      ocrFormData.append('file_path', uploadResult.file_path)

      const ocrResponse = await api.upload<any>(
        API_CONFIG.ENDPOINTS.OCR, 
        ocrFormData, 
        API_CONFIG.TIMEOUT.OCR
      )
      content = ocrResponse.text // 保存OCR文本用于RAG
      ocrCompleted = true // OCR处理完成

      // 3. 如果OCR成功且有内容，进行RAG文档处理
      if (content && content.trim().length > 50) {
        try {
          docId = await processDocumentForRAG(content, file.name, file.type)
          ragEnabled = true
          console.log('✅ RAG文档处理完成，doc_id:', docId)
        } catch (ragError) {
          console.warn('⚠️ RAG文档处理失败:', ragError)
          // RAG处理失败不影响文件使用
        }
      }
    } catch (ocrError) {
      console.warn('OCR处理失败:', ocrError)
      // OCR失败不影响文件上传，继续处理
      ocrCompleted = false
    }
  } else {
    // 非OCR文件类型，直接标记为完成
    ocrCompleted = true
  }

  return {
    name: file.name,
    size: file.size,
    type: file.type,
    content,
    ocrCompleted,
    processing: !ocrCompleted, // 如果OCR未完成，则仍处于处理中状态
    doc_id: docId,
    rag_enabled: ragEnabled
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