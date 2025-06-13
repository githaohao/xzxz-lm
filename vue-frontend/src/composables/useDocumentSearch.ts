import { ref, computed, type Ref } from 'vue'
import type { RAGDocument, RAGSearchRequest, RAGSearchResponse } from '@/types'
import { searchDocuments } from '@/utils/api'

export interface DocumentSearchOptions {
  query: string
  searchType: 'filename' | 'content' | 'semantic' | 'all'
  fileTypes?: string[]
  dateRange?: {
    start?: Date
    end?: Date
  }
  chunkCountRange?: {
    min?: number
    max?: number
  }
  sizeRange?: {
    min?: number
    max?: number
  }
}

export function useDocumentSearch(documents: Ref<RAGDocument[]>) {
  const searchQuery = ref('')
  const searchOptions = ref<DocumentSearchOptions>({
    query: '',
    searchType: 'all'
  })
  const isSearching = ref(false)
  const searchResults = ref<RAGDocument[]>([])
  const semanticResults = ref<RAGSearchResponse | null>(null)

  // 基础文件名搜索
  const filenameFilteredDocuments = computed(() => {
    if (!searchQuery.value) return documents.value
    
    const query = searchQuery.value.toLowerCase()
    return documents.value.filter((doc: RAGDocument) => 
      doc.filename.toLowerCase().includes(query)
    )
  })

  // 高级搜索过滤
  const advancedFilteredDocuments = computed(() => {
    let filtered = documents.value

    if (searchOptions.value.query) {
      const query = searchOptions.value.query.toLowerCase()
      
      filtered = filtered.filter((doc: RAGDocument) => {
        switch (searchOptions.value.searchType) {
          case 'filename':
            return doc.filename.toLowerCase().includes(query)
          case 'content':
            // 这里需要有文档内容才能搜索，暂时用文件名代替
            return doc.filename.toLowerCase().includes(query)
          case 'all':
            return doc.filename.toLowerCase().includes(query) ||
                   getFileTypeDisplay(doc.file_type).toLowerCase().includes(query)
          default:
            return true
        }
      })
    }

    // 文件类型过滤
    if (searchOptions.value.fileTypes?.length) {
      filtered = filtered.filter((doc: RAGDocument) => 
        searchOptions.value.fileTypes!.includes(doc.file_type)
      )
    }

    // 日期范围过滤
    if (searchOptions.value.dateRange?.start || searchOptions.value.dateRange?.end) {
      filtered = filtered.filter((doc: RAGDocument) => {
        const docDate = new Date(doc.created_at)
        const start = searchOptions.value.dateRange?.start
        const end = searchOptions.value.dateRange?.end
        
        if (start && docDate < start) return false
        if (end && docDate > end) return false
        return true
      })
    }

    // 分片数量范围过滤
    if (searchOptions.value.chunkCountRange?.min !== undefined || 
        searchOptions.value.chunkCountRange?.max !== undefined) {
      filtered = filtered.filter((doc: RAGDocument) => {
        const min = searchOptions.value.chunkCountRange?.min
        const max = searchOptions.value.chunkCountRange?.max
        
        if (min !== undefined && doc.chunk_count < min) return false
        if (max !== undefined && doc.chunk_count > max) return false
        return true
      })
    }

    // 文档大小范围过滤
    if (searchOptions.value.sizeRange?.min !== undefined || 
        searchOptions.value.sizeRange?.max !== undefined) {
      filtered = filtered.filter((doc: RAGDocument) => {
        const min = searchOptions.value.sizeRange?.min
        const max = searchOptions.value.sizeRange?.max
        
        if (min !== undefined && doc.total_length < min) return false
        if (max !== undefined && doc.total_length > max) return false
        return true
      })
    }

    return filtered
  })

  // 执行语义搜索
  async function performSemanticSearch(query: string, docIds?: string[]) {
    if (!query.trim()) return

    isSearching.value = true
    try {
      const request: RAGSearchRequest = {
        query,
        doc_ids: docIds      }
      
      const response = await searchDocuments(request)
      semanticResults.value = response
      
      // 根据语义搜索结果排序文档
      if (response.chunks.length > 0) {
        const docIdScores = new Map<string, number>()
        
        response.chunks.forEach(chunk => {
          const docId = chunk.metadata.doc_id
          const currentScore = docIdScores.get(docId) || 0
          docIdScores.set(docId, Math.max(currentScore, chunk.similarity))
        })
        
        const sortedDocs = documents.value
          .filter((doc: RAGDocument) => docIdScores.has(doc.doc_id))
          .sort((a: RAGDocument, b: RAGDocument) => (docIdScores.get(b.doc_id) || 0) - (docIdScores.get(a.doc_id) || 0))
        
        searchResults.value = sortedDocs
      } else {
        searchResults.value = []
      }
    } catch (error) {
      console.error('语义搜索失败:', error)
      searchResults.value = []
    } finally {
      isSearching.value = false
    }
  }

  // 组合搜索结果
  const combinedSearchResults = computed(() => {
    if (searchOptions.value.searchType === 'semantic' && semanticResults.value) {
      return searchResults.value
    }
    return advancedFilteredDocuments.value
  })

  // 搜索统计
  const searchStats = computed(() => {
    const total = documents.value.length
    const filtered = combinedSearchResults.value.length
    const semanticChunks = semanticResults.value?.chunks.length || 0
    
    return {
      total,
      filtered,
      semanticChunks,
      hasFilters: searchOptions.value.query || 
                  searchOptions.value.fileTypes?.length ||
                  searchOptions.value.dateRange?.start ||
                  searchOptions.value.dateRange?.end ||
                  searchOptions.value.chunkCountRange?.min !== undefined ||
                  searchOptions.value.chunkCountRange?.max !== undefined ||
                  searchOptions.value.sizeRange?.min !== undefined ||
                  searchOptions.value.sizeRange?.max !== undefined
    }
  })

  // 重置搜索
  function resetSearch() {
    searchQuery.value = ''
    searchOptions.value = {
      query: '',
      searchType: 'all'
    }
    searchResults.value = []
    semanticResults.value = null
  }

  // 清除语义搜索结果
  function clearSemanticResults() {
    semanticResults.value = null
    searchResults.value = []
  }

  // 获取搜索建议
  function getSearchSuggestions(query: string): string[] {
    if (!query) return []
    
    const suggestions = new Set<string>()
    const queryLower = query.toLowerCase()
    
    documents.value.forEach((doc: RAGDocument) => {
      // 文件名建议
      if (doc.filename.toLowerCase().includes(queryLower)) {
        const words = doc.filename.split(/[.\-_\s]+/)
        words.forEach((word: string) => {
          if (word.toLowerCase().startsWith(queryLower) && word.length > query.length) {
            suggestions.add(word)
          }
        })
      }
      
      // 文件类型建议
      const displayType = getFileTypeDisplay(doc.file_type)
      if (displayType.toLowerCase().includes(queryLower)) {
        suggestions.add(displayType)
      }
    })
    
    return Array.from(suggestions).slice(0, 5)
  }

  // 高亮搜索词
  function highlightSearchTerm(text: string, searchTerm: string): string {
    if (!searchTerm) return text
    
    const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
    return text.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-800 rounded px-0.5">$1</mark>')
  }

  return {
    // 响应式状态
    searchQuery,
    searchOptions,
    isSearching,
    searchResults,
    semanticResults,
    
    // 计算属性
    filenameFilteredDocuments,
    advancedFilteredDocuments,
    combinedSearchResults,
    searchStats,
    
    // 方法
    performSemanticSearch,
    resetSearch,
    clearSemanticResults,
    getSearchSuggestions,
    highlightSearchTerm
  }
}

// 工具函数
function getFileTypeDisplay(fileType: string): string {
  const typeMap: Record<string, string> = {
    'application/pdf': 'PDF',
    'image/png': 'PNG',
    'image/jpg': 'JPG', 
    'image/jpeg': 'JPEG',
  }
  return typeMap[fileType] || 'File'
}
