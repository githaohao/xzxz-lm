import type { RAGSearchRequest, RAGSearchResponse, RAGDocument } from '@/types'
import { API_CONFIG } from '../api-config'
import { api } from './client'

/**
 * RAG文档管理和检索 API
 */

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
