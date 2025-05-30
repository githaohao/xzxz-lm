import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  KnowledgeBase, 
  CreateKnowledgeBaseRequest, 
  UpdateKnowledgeBaseRequest,
  RAGDocument,
  DocumentSearchOptions,
  KnowledgeBaseStats
} from '@/types'
import { generateId } from '@/utils/voice-utils'
import { getAllDocuments } from '@/utils/api'

export const useKnowledgeBaseStore = defineStore('knowledgeBase', () => {
  // 状态
  const knowledgeBases = ref<KnowledgeBase[]>([])
  const allDocuments = ref<RAGDocument[]>([])
  const selectedKnowledgeBase = ref<KnowledgeBase | null>(null)
  const selectedDocuments = ref<Set<string>>(new Set())
  const isLoading = ref(false)
  const searchOptions = ref<DocumentSearchOptions>({})

  // 计算属性
  const hasKnowledgeBases = computed(() => knowledgeBases.value.length > 0)
  const defaultKnowledgeBase = computed(() => 
    knowledgeBases.value.find(kb => kb.isDefault) || null
  )
  
  // 当前知识库的文档
  const currentKnowledgeBaseDocuments = computed(() => {
    if (!selectedKnowledgeBase.value) return allDocuments.value
    
    return allDocuments.value.filter(doc => 
      selectedKnowledgeBase.value!.documentIds.includes(doc.doc_id)
    )
  })

  // 未分类的文档（不属于任何知识库）
  const uncategorizedDocuments = computed(() => {
    const allKnowledgeBaseDocIds = new Set(
      knowledgeBases.value.flatMap(kb => kb.documentIds)
    )
    return allDocuments.value.filter(doc => !allKnowledgeBaseDocIds.has(doc.doc_id))
  })

  // 知识库统计
  const knowledgeBaseStats = computed((): Record<string, KnowledgeBaseStats> => {
    const stats: Record<string, KnowledgeBaseStats> = {}
    
    knowledgeBases.value.forEach(kb => {
      const docs = allDocuments.value.filter(doc => kb.documentIds.includes(doc.doc_id))
      const weekAgo = new Date()
      weekAgo.setDate(weekAgo.getDate() - 7)
      
      stats[kb.id] = {
        totalDocuments: docs.length,
        totalChunks: docs.reduce((sum, doc) => sum + doc.chunk_count, 0),
        totalSize: docs.reduce((sum, doc) => sum + doc.total_length, 0),
        recentlyAdded: docs.filter(doc => new Date(doc.created_at) > weekAgo).length
      }
    })
    
    return stats
  })

  // 过滤后的文档
  const filteredDocuments = computed(() => {
    let docs = selectedKnowledgeBase.value 
      ? currentKnowledgeBaseDocuments.value 
      : allDocuments.value

    // 文本搜索
    if (searchOptions.value.query) {
      const query = searchOptions.value.query.toLowerCase()
      docs = docs.filter(doc => 
        doc.filename.toLowerCase().includes(query) ||
        doc.file_type.toLowerCase().includes(query)
      )
    }

    // 文件类型过滤
    if (searchOptions.value.fileTypes?.length) {
      docs = docs.filter(doc => 
        searchOptions.value.fileTypes!.includes(doc.file_type)
      )
    }

    // 日期范围过滤
    if (searchOptions.value.dateRange) {
      const { start, end } = searchOptions.value.dateRange
      docs = docs.filter(doc => {
        const docDate = new Date(doc.created_at)
        return docDate >= start && docDate <= end
      })
    }

    // 排序
    if (searchOptions.value.sortBy) {
      const { sortBy, sortOrder = 'asc' } = searchOptions.value
      docs = [...docs].sort((a, b) => {
        let comparison = 0
        
        switch (sortBy) {
          case 'name':
            comparison = a.filename.localeCompare(b.filename)
            break
          case 'date':
            comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
            break
          case 'size':
            comparison = a.total_length - b.total_length
            break
        }
        
        return sortOrder === 'desc' ? -comparison : comparison
      })
    }

    return docs
  })

  // 预定义颜色
  const availableColors = [
    '#3B82F6', // blue
    '#10B981', // emerald
    '#F59E0B', // amber
    '#EF4444', // red
    '#8B5CF6', // violet
    '#06B6D4', // cyan
    '#84CC16', // lime
    '#F97316', // orange
    '#EC4899', // pink
    '#6B7280'  // gray
  ]

  // 初始化
  async function initialize() {
    await Promise.all([
      loadKnowledgeBases(),
      fetchAllDocuments()
    ])
    
    // 如果没有默认知识库，创建一个
    if (!defaultKnowledgeBase.value) {
      await createKnowledgeBase({
        name: '默认知识库',
        description: '系统默认知识库，用于存放未分类的文档',
        color: availableColors[0]
      }, true)
    }
  }

  // 获取所有文档
  async function fetchAllDocuments() {
    try {
      isLoading.value = true
      const response = await getAllDocuments()
      allDocuments.value = response.documents
      console.log('📚 已获取所有文档:', response.documents.length)
    } catch (error) {
      console.error('获取文档失败:', error)
    } finally {
      isLoading.value = false
    }
  }

  // 创建知识库
  async function createKnowledgeBase(
    request: CreateKnowledgeBaseRequest, 
    isDefault = false
  ): Promise<KnowledgeBase> {
    const knowledgeBase: KnowledgeBase = {
      id: generateId(),
      name: request.name,
      description: request.description,
      documentIds: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      color: request.color || availableColors[knowledgeBases.value.length % availableColors.length],
      isDefault
    }

    knowledgeBases.value.push(knowledgeBase)
    saveKnowledgeBases()
    
    console.log('✨ 创建知识库:', knowledgeBase.name)
    return knowledgeBase
  }

  // 更新知识库
  async function updateKnowledgeBase(
    id: string, 
    request: UpdateKnowledgeBaseRequest
  ): Promise<boolean> {
    const index = knowledgeBases.value.findIndex(kb => kb.id === id)
    if (index === -1) return false

    const knowledgeBase = knowledgeBases.value[index]
    Object.assign(knowledgeBase, {
      ...request,
      updatedAt: new Date()
    })

    saveKnowledgeBases()
    console.log('📝 更新知识库:', knowledgeBase.name)
    return true
  }

  // 删除知识库
  async function deleteKnowledgeBase(id: string): Promise<boolean> {
    const index = knowledgeBases.value.findIndex(kb => kb.id === id)
    if (index === -1) return false

    const knowledgeBase = knowledgeBases.value[index]
    
    // 不能删除默认知识库
    if (knowledgeBase.isDefault) {
      console.warn('⚠️ 不能删除默认知识库')
      return false
    }

    knowledgeBases.value.splice(index, 1)
    
    // 如果删除的是当前选中的知识库，切换到默认知识库
    if (selectedKnowledgeBase.value?.id === id) {
      selectedKnowledgeBase.value = defaultKnowledgeBase.value
    }

    saveKnowledgeBases()
    console.log('🗑️ 删除知识库:', knowledgeBase.name)
    return true
  }

  // 设置当前知识库
  function setSelectedKnowledgeBase(knowledgeBase: KnowledgeBase | null) {
    selectedKnowledgeBase.value = knowledgeBase
    selectedDocuments.value.clear()
  }

  // 将文档添加到知识库
  async function addDocumentsToKnowledgeBase(
    knowledgeBaseId: string, 
    documentIds: string[]
  ): Promise<boolean> {
    const knowledgeBase = knowledgeBases.value.find(kb => kb.id === knowledgeBaseId)
    if (!knowledgeBase) return false

    // 添加文档ID（去重）
    const newDocumentIds = documentIds.filter(id => 
      !knowledgeBase.documentIds.includes(id)
    )
    
    knowledgeBase.documentIds.push(...newDocumentIds)
    knowledgeBase.updatedAt = new Date()
    
    saveKnowledgeBases()
    console.log(`📁 向知识库 "${knowledgeBase.name}" 添加了 ${newDocumentIds.length} 个文档`)
    return true
  }

  // 从知识库移除文档
  async function removeDocumentsFromKnowledgeBase(
    knowledgeBaseId: string, 
    documentIds: string[]
  ): Promise<boolean> {
    const knowledgeBase = knowledgeBases.value.find(kb => kb.id === knowledgeBaseId)
    if (!knowledgeBase) return false

    // 移除文档ID
    knowledgeBase.documentIds = knowledgeBase.documentIds.filter(id => 
      !documentIds.includes(id)
    )
    knowledgeBase.updatedAt = new Date()
    
    saveKnowledgeBases()
    console.log(`📁 从知识库 "${knowledgeBase.name}" 移除了 ${documentIds.length} 个文档`)
    return true
  }

  // 移动文档到另一个知识库
  async function moveDocuments(
    documentIds: string[],
    targetKnowledgeBaseId: string,
    sourceKnowledgeBaseId?: string
  ): Promise<boolean> {
    // 从源知识库移除（如果指定）
    if (sourceKnowledgeBaseId) {
      await removeDocumentsFromKnowledgeBase(sourceKnowledgeBaseId, documentIds)
    } else {
      // 从所有知识库中移除
      for (const kb of knowledgeBases.value) {
        await removeDocumentsFromKnowledgeBase(kb.id, documentIds)
      }
    }

    // 添加到目标知识库
    return await addDocumentsToKnowledgeBase(targetKnowledgeBaseId, documentIds)
  }

  // 文档选择操作
  function selectDocument(docId: string) {
    selectedDocuments.value.add(docId)
  }

  function unselectDocument(docId: string) {
    selectedDocuments.value.delete(docId)
  }

  function toggleDocument(docId: string) {
    if (selectedDocuments.value.has(docId)) {
      unselectDocument(docId)
    } else {
      selectDocument(docId)
    }
  }

  function clearSelection() {
    selectedDocuments.value.clear()
  }

  function selectAll() {
    filteredDocuments.value.forEach(doc => {
      selectedDocuments.value.add(doc.doc_id)
    })
  }

  // 搜索和过滤
  function updateSearchOptions(options: Partial<DocumentSearchOptions>) {
    searchOptions.value = { ...searchOptions.value, ...options }
  }

  function clearSearch() {
    searchOptions.value = {}
  }

  // 本地存储管理
  function saveKnowledgeBases() {
    try {
      const data = knowledgeBases.value.map(kb => ({
        ...kb,
        createdAt: kb.createdAt.toISOString(),
        updatedAt: kb.updatedAt.toISOString()
      }))
      localStorage.setItem('knowledgeBases', JSON.stringify(data))
    } catch (error) {
      console.error('保存知识库失败:', error)
    }
  }

  function loadKnowledgeBases() {
    try {
      const data = localStorage.getItem('knowledgeBases')
      if (data) {
        const parsed = JSON.parse(data)
        knowledgeBases.value = parsed.map((kb: any) => ({
          ...kb,
          createdAt: new Date(kb.createdAt),
          updatedAt: new Date(kb.updatedAt)
        }))
        console.log(`✅ 从缓存加载了 ${knowledgeBases.value.length} 个知识库`)
      }
    } catch (error) {
      console.error('加载知识库失败:', error)
    }
  }

  // 获取文档所属的知识库
  function getDocumentKnowledgeBases(docId: string): KnowledgeBase[] {
    return knowledgeBases.value.filter(kb => kb.documentIds.includes(docId))
  }

  // 格式化工具函数
  function formatFileSize(size: number): string {
    if (size < 1000) return `${size} 字符`
    if (size < 1000000) return `${(size / 1000).toFixed(1)}K 字符`
    return `${(size / 1000000).toFixed(1)}M 字符`
  }

  function formatDate(date: Date | string): string {
    const d = typeof date === 'string' ? new Date(date) : date
    return d.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return {
    // 状态
    knowledgeBases,
    allDocuments,
    selectedKnowledgeBase,
    selectedDocuments,
    isLoading,
    searchOptions,

    // 计算属性
    hasKnowledgeBases,
    defaultKnowledgeBase,
    currentKnowledgeBaseDocuments,
    uncategorizedDocuments,
    knowledgeBaseStats,
    filteredDocuments,

    // 方法
    initialize,
    fetchAllDocuments,
    createKnowledgeBase,
    updateKnowledgeBase,
    deleteKnowledgeBase,
    setSelectedKnowledgeBase,
    addDocumentsToKnowledgeBase,
    removeDocumentsFromKnowledgeBase,
    moveDocuments,
    selectDocument,
    unselectDocument,
    toggleDocument,
    clearSelection,
    selectAll,
    updateSearchOptions,
    clearSearch,
    getDocumentKnowledgeBases,
    formatFileSize,
    formatDate,
    
    // 常量
    availableColors
  }
}) 