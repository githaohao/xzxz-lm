import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { RAGDocument, RAGDocumentsResponse } from '@/types'
import { getAllDocuments, deleteDocument } from '@/utils/api'

export const useRAGStore = defineStore('rag', () => {
  // 状态
  const documents = ref<RAGDocument[]>([])
  const selectedDocuments = ref<Set<string>>(new Set())
  const isLoading = ref(false)
  const lastUpdateTime = ref<Date | null>(null)

  // 计算属性
  const hasDocuments = computed(() => documents.value.length > 0)
  const selectedDocumentsList = computed(() => 
    documents.value.filter(doc => selectedDocuments.value.has(doc.doc_id))
  )
  const selectedCount = computed(() => selectedDocuments.value.size)

  // 获取所有文档
  async function fetchDocuments() {
    try {
      isLoading.value = true
      const response: RAGDocumentsResponse = await getAllDocuments()
      documents.value = response.documents
      lastUpdateTime.value = new Date()
      console.log(`📚 获取到 ${response.total_count} 个RAG文档`)
    } catch (error) {
      console.error('获取文档列表失败:', error)
      documents.value = []
    } finally {
      isLoading.value = false
    }
  }

  // 选择文档
  function selectDocument(docId: string) {
    selectedDocuments.value.add(docId)
  }

  // 取消选择文档
  function unselectDocument(docId: string) {
    selectedDocuments.value.delete(docId)
  }

  // 切换文档选择状态
  function toggleDocument(docId: string) {
    if (selectedDocuments.value.has(docId)) {
      unselectDocument(docId)
    } else {
      selectDocument(docId)
    }
  }

  // 清除所有选择
  function clearSelection() {
    selectedDocuments.value.clear()
  }

  // 选择所有文档
  function selectAll() {
    documents.value.forEach(doc => {
      selectedDocuments.value.add(doc.doc_id)
    })
  }

  // 删除文档
  async function removeDocument(docId: string) {
    try {
      const success = await deleteDocument(docId)
      if (success) {
        // 从列表中移除
        documents.value = documents.value.filter(doc => doc.doc_id !== docId)
        // 从选择中移除
        selectedDocuments.value.delete(docId)
        console.log(`🗑️ 文档删除成功: ${docId}`)
        return true
      }
      return false
    } catch (error) {
      console.error('删除文档失败:', error)
      return false
    }
  }

  // 批量删除选中的文档
  async function removeSelectedDocuments() {
    const docIds = Array.from(selectedDocuments.value)
    const results = await Promise.allSettled(
      docIds.map(docId => removeDocument(docId))
    )
    
    const successCount = results.filter(result => 
      result.status === 'fulfilled' && result.value === true
    ).length
    
    console.log(`🗑️ 批量删除完成: ${successCount}/${docIds.length}`)
    return successCount
  }

  // 根据文件名查找文档
  function findDocumentByFilename(filename: string): RAGDocument | undefined {
    return documents.value.find(doc => doc.filename === filename)
  }

  // 获取文档统计信息
  const documentStats = computed(() => ({
    totalDocuments: documents.value.length,
    totalChunks: documents.value.reduce((sum, doc) => sum + doc.chunk_count, 0),
    totalLength: documents.value.reduce((sum, doc) => sum + doc.total_length, 0),
    selectedDocuments: selectedCount.value
  }))

  // 格式化文档大小
  function formatDocumentSize(totalLength: number): string {
    if (totalLength < 1000) return `${totalLength} 字符`
    if (totalLength < 1000000) return `${(totalLength / 1000).toFixed(1)}K 字符`
    return `${(totalLength / 1000000).toFixed(1)}M 字符`
  }

  // 格式化创建时间
  function formatCreateTime(isoString: string): string {
    try {
      const date = new Date(isoString)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 1) return '刚刚'
      if (diffMins < 60) return `${diffMins}分钟前`
      if (diffHours < 24) return `${diffHours}小时前`
      if (diffDays < 7) return `${diffDays}天前`
      
      return date.toLocaleDateString('zh-CN')
    } catch {
      return '未知时间'
    }
  }

  return {
    // 状态
    documents,
    selectedDocuments,
    isLoading,
    lastUpdateTime,

    // 计算属性
    hasDocuments,
    selectedDocumentsList,
    selectedCount,
    documentStats,

    // 方法
    fetchDocuments,
    selectDocument,
    unselectDocument,
    toggleDocument,
    clearSelection,
    selectAll,
    removeDocument,
    removeSelectedDocuments,
    findDocumentByFilename,
    formatDocumentSize,
    formatCreateTime
  }
}) 