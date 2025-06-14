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

// 知识库管理 API
/**
 * 创建知识库
 */
export async function createKnowledgeBase(data: {
  name: string
  description?: string
  color?: string
}): Promise<any> {
  return api.post('/api/lm/rag/knowledge-bases', data)
}

/**
 * 获取所有知识库
 */
export async function getAllKnowledgeBases(): Promise<any> {
  return api.get('/api/lm/rag/knowledge-bases')
}

/**
 * 获取单个知识库详情
 */
export async function getKnowledgeBase(kbId: string): Promise<any> {
  return api.get(`/api/lm/rag/knowledge-bases/${kbId}`)
}

/**
 * 更新知识库
 */
export async function updateKnowledgeBase(kbId: string, data: {
  name: string
  description?: string
  color?: string
}): Promise<any> {
  return api.put(`/api/lm/rag/knowledge-bases/${kbId}`, data)
}

/**
 * 删除知识库
 */
export async function deleteKnowledgeBase(kbId: string): Promise<boolean> {
  try {
    await api.delete(`/api/lm/rag/knowledge-bases/${kbId}`)
    return true
  } catch (error) {
    console.error('删除知识库失败:', error)
    return false
  }
}

/**
 * 向知识库添加文档
 */
export async function addDocumentsToKnowledgeBase(kbId: string, documentIds: string[]): Promise<any> {
  return api.post(`/api/lm/rag/knowledge-bases/${kbId}/documents`, {
    document_ids: documentIds
  })
}

/**
 * 从知识库移除文档
 */
export async function removeDocumentsFromKnowledgeBase(kbId: string, documentIds: string[]): Promise<any> {
  const response = await api.get(`/api/lm/rag/knowledge-bases/${kbId}/documents`)
  // 使用POST请求模拟DELETE带body
  return api.post(`/api/lm/rag/knowledge-bases/${kbId}/documents/remove`, {
    document_ids: documentIds
  })
}

/**
 * 获取知识库的所有文档
 */
export async function getKnowledgeBaseDocuments(kbId: string): Promise<any> {
  return api.get(`/api/lm/rag/knowledge-bases/${kbId}/documents`)
}

/**
 * 智能文档分类和归档
 */
export async function smartArchiveDocument(data: {
  file: File
  prompt: string
  customAnalysis?: boolean
}): Promise<{
  fileName: string
  knowledgeBaseName: string
  isNewKnowledgeBase: boolean
  reason?: string
  docId: string
  knowledgeBaseId: string
}> {
  const formData = new FormData()
  formData.append('file', data.file)
  formData.append('prompt', data.prompt)
  if (data.customAnalysis) {
    formData.append('custom_analysis', 'true')
  }

  return api.upload<any>(
    '/api/lm/rag/smart-archive', 
    formData, 
    API_CONFIG.TIMEOUT.RAG
  )
}

/**
 * 分析文档内容，预览归档建议（不实际保存）
 */
export async function analyzeDocumentsForArchive(data: {
  files: File[]
  prompt: string
  customAnalysis?: boolean
}): Promise<{
  code: number
  msg: string
  data: {
    results: Array<{
      fileName: string
      knowledgeBaseName: string
      isNewKnowledgeBase: boolean
      reason?: string
      knowledgeBaseId?: string
      documentType: string
      textContent: string
      docId?: string  // ✨ 新增：文档ID（分析阶段已生成）
      success: boolean
      error?: string
    }>
    totalFiles: number
    successCount: number
    failureCount: number
  }
}> {
  const formData = new FormData()
  
  data.files.forEach((file, index) => {
    formData.append(`files`, file)
  })
  formData.append('prompt', data.prompt)
  if (data.customAnalysis) {
    formData.append('custom_analysis', 'true')
  }

  return api.upload<any>(
    '/api/lm/rag/analyze-documents', 
    formData, 
    API_CONFIG.TIMEOUT.RAG
  )
}

/**
 * 确认归档分析结果，执行文档与知识库的关联操作
 * （文档在分析阶段已保存，这里只做关联）
 */
export async function confirmSmartArchive(data: {
  files: Array<{
    fileName: string
    fileType: string
    content?: string // ⚠️ 已弃用，保留兼容性
  }>
  analysisResults: Array<{
    fileName: string
    knowledgeBaseName: string
    isNewKnowledgeBase: boolean
    reason?: string
    knowledgeBaseId?: string
    documentType: string
    docId?: string  // ✨ 新增：文档ID（分析阶段生成）
    success: boolean
    error?: string
  }>
}): Promise<{
  code: number
  msg: string
  data: {
    results: Array<{
      fileName: string
      knowledgeBaseName: string
      isNewKnowledgeBase: boolean
      reason?: string
      docId: string
      knowledgeBaseId: string
      success: boolean
      error?: string
    }>
    totalFiles: number
    successCount: number
    failureCount: number
  }
}> {
  return api.post<any>(
    '/api/lm/rag/confirm-smart-archive',
    data
  )
}

/**
 * 批量智能文档归档（一步到位，保留兼容性）
 */
export async function batchSmartArchive(data: {
  files: File[]
  prompt: string
  customAnalysis?: boolean
}): Promise<{
  results: Array<{
    fileName: string
    knowledgeBaseName: string
    isNewKnowledgeBase: boolean
    reason?: string
    docId: string
    knowledgeBaseId: string
    success: boolean
    error?: string
  }>
  totalFiles: number
  successCount: number
  failureCount: number
}> {
  const formData = new FormData()
  
  data.files.forEach((file, index) => {
    formData.append(`files`, file)
  })
  formData.append('prompt', data.prompt)
  if (data.customAnalysis) {
    formData.append('custom_analysis', 'true')
  }

  return api.upload<any>(
    '/api/lm/rag/batch-smart-archive', 
    formData, 
    API_CONFIG.TIMEOUT.RAG * 2 // 批量处理需要更长时间
  )
}

/**
 * 分析已有文档进行智能归档
 */
export async function analyzeExistingDocumentsForArchive(data: {
  docIds: string[]
  prompt: string
  customAnalysis?: boolean
}): Promise<{
  code: number
  msg: string
  data: {
    results: Array<{
      docId: string
      filename: string
      knowledgeBaseName: string
      isNewKnowledgeBase: boolean
      reason?: string
      knowledgeBaseId?: string
      documentType: string
      textContent: string
      success: boolean
      error?: string
    }>
    totalDocuments: number
    successCount: number
    failureCount: number
  }
}> {
  return api.post('/api/lm/rag/analyze-existing-documents', data)
}

/**
 * 确认已有文档的智能归档
 */
export async function confirmExistingArchive(data: {
  analysisResults: Array<{
    docId: string
    filename: string
    knowledgeBaseName: string
    isNewKnowledgeBase: boolean
    reason?: string
    knowledgeBaseId?: string
    documentType: string
    success: boolean
    error?: string
  }>
}): Promise<{
  code: number
  msg: string
  data: {
    results: Array<{
      docId: string
      filename: string
      knowledgeBaseName: string
      isNewKnowledgeBase: boolean
      reason?: string
      knowledgeBaseId: string
      success: boolean
      error?: string
    }>
    totalDocuments: number
    successCount: number
    failureCount: number
  }
}> {
  return api.post('/api/lm/rag/confirm-existing-archive', data)
}