// 消息类型
export interface Message {
  id: string
  content: string
  isUser: boolean
  timestamp: Date
  fileInfo?: {
    name: string
    size: number
    type: string
    rag_enabled?: boolean
  }
  isStreaming?: boolean
}

// 语音消息类型
export interface VoiceMessage {
  id: string
  content: string
  isUser: boolean
  timestamp: Date
  duration?: number
  audioUrl?: string
  recognizedText?: string
}

// 流式事件类型
export interface StreamEvent {
  type: 'file_processing' | 'ocr_processing' | 'ocr_complete' | 'ocr_error' | 'thinking' | 'content' | 'complete' | 'error'
  message?: string
  content?: string
  file_info?: any
}

// 文件处理状态
export interface ProcessedFile {
  name: string
  size: number
  type: string
  processing?: boolean
  ocrCompleted?: boolean
  content?: string  // OCR处理后的内容，用于RAG
  doc_id?: string   // RAG文档ID
  rag_enabled?: boolean  // 是否启用RAG
}

// RAG文档块
export interface DocumentChunk {
  chunk_id: string
  content: string
  similarity: number
  metadata: Record<string, any>
}

// RAG检索请求
export interface RAGSearchRequest {
  query: string
  doc_ids?: string[]
  top_k?: number
  min_similarity?: number
}

// RAG检索响应
export interface RAGSearchResponse {
  chunks: DocumentChunk[]
  total_found: number
  search_time: number
}

// RAG文档项
export interface RAGDocument {
  doc_id: string
  filename: string
  file_type: string
  created_at: string
  chunk_count: number
  total_length: number
}

// RAG文档列表响应
export interface RAGDocumentsResponse {
  documents: RAGDocument[]
  total_count: number
  processing_time: number
}

// 通话状态
export type CallState = 'idle' | 'connecting' | 'connected' | 'speaking' | 'listening' | 'processing'

// 后端消息格式
export interface BackendMessage {
  id: string
  content: string
  message_type: string
  timestamp: string
  is_user: boolean
  file_name: string | null
  file_size: number | null
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
}

// 语音识别响应
export interface VoiceRecognitionResponse {
  success: boolean
  recognized_text: string
  response: string
  history_length?: number
  error?: string
}

// TTS请求参数
export interface TTSRequest {
  text: string
  voice?: string
  rate?: number
  pitch?: number
} 