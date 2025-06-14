import { api } from './client'

/**
 * 知识库管理 API
 */

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
}): Promise<any> {
  const formData = new FormData()
  formData.append('file', data.file)
  formData.append('prompt', data.prompt)
  if (data.customAnalysis) {
    formData.append('custom_analysis', 'true')
  }

  return api.upload<any>(
    '/api/lm/rag/smart-archive',
    formData,
    30000 // 30秒超时
  )
}

/**
 * 分析文档内容，预览归档建议（不实际保存）
 */
export async function analyzeDocumentsForArchive(data: {
  files: File[]
  prompt: string
  customAnalysis?: boolean
}): Promise<any> {
  const formData = new FormData()

  data.files.forEach((file) => {
    formData.append(`files`, file)
  })
  formData.append('prompt', data.prompt)
  if (data.customAnalysis) {
    formData.append('custom_analysis', 'true')
  }

  return api.upload<any>(
    '/api/lm/rag/analyze-documents',
    formData,
    30000 // 30秒超时
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
}): Promise<any> {
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
}): Promise<any> {
  const formData = new FormData()

  data.files.forEach((file) => {
    formData.append(`files`, file)
  })
  formData.append('prompt', data.prompt)
  if (data.customAnalysis) {
    formData.append('custom_analysis', 'true')
  }

  return api.upload<any>(
    '/api/lm/rag/batch-smart-archive',
    formData,
    60000 // 批量处理需要更长时间
  )
}

/**
 * 分析已有文档进行智能归档
 */
export async function analyzeExistingDocumentsForArchive(data: {
  docIds: string[]
  prompt: string
  customAnalysis?: boolean
}): Promise<any> {
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
}): Promise<any> {
  return api.post('/api/lm/rag/confirm-existing-archive', data)
} 