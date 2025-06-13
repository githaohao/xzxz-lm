from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum
from app.utils import now_china_naive

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    FILE = "file"

class ChatMessage(BaseModel):
    id: Optional[str] = None
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = Field(default_factory=now_china_naive)
    is_user: bool = True
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=4096)
    stream: bool = False
    session_id: Optional[str] = None  # 可选的会话ID，用于保存聊天历史

class FileData(BaseModel):
    name: str
    type: str
    size: int
    content: Optional[str] = None
    doc_id: Optional[str] = None  # RAG文档ID
    knowledge_base_id: Optional[str] = None  # 知识库ID，用于知识库RAG检索
    ocr_completed: Optional[bool] = False
    rag_enabled: Optional[bool] = False  # 是否启用RAG功能

class DocumentChunk(BaseModel):
    """文档分块"""
    chunk_id: str
    content: str
    similarity: float
    metadata: dict

class RAGSearchRequest(BaseModel):
    """RAG检索请求"""
    query: str
    doc_ids: Optional[List[str]] = None
    top_k: int = Field(default=5, ge=1, le=20)
    min_similarity: float = Field(default=0.355, ge=0.0, le=1.0)

class RAGSearchResponse(BaseModel):
    """RAG检索响应"""
    chunks: List[DocumentChunk]
    total_found: int
    search_time: float

class DocumentInfo(BaseModel):
    """文档信息"""
    doc_id: str
    filename: str
    file_type: str
    chunk_count: int
    created_at: str

class MultimodalStreamRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    file_data: Optional[FileData] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=4096)
    session_id: Optional[str] = None  # 可选的会话ID，用于保存聊天历史

class ChatResponse(BaseModel):
    response: str
    message_id: str
    timestamp: datetime = Field(default_factory=now_china_naive)
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }

class FileUploadResponse(BaseModel):
    file_id: str
    file_name: str
    file_path: str
    file_size: int
    file_type: str
    upload_time: datetime = Field(default_factory=now_china_naive)
    # PDF处理状态信息
    is_pdf: bool = False
    is_text_pdf: Optional[bool] = None  # None: 未检测, True: 文本PDF, False: 扫描PDF
    text_content: Optional[str] = None  # 提取的文本内容（仅文本PDF）
    char_count: Optional[int] = None  # 字符数量
    processing_status: Optional[str] = None  # 处理状态信息
    doc_id: Optional[str] = None  # RAG文档ID
    rag_processed: bool = False  # 是否已进行RAG处理

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }

class OCRRequest(BaseModel):
    file_path: str
    language: str = "chi_sim+eng"

class OCRResponse(BaseModel):
    text: str
    confidence: Optional[float] = None
    processing_time: float
    detected_language: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "+0%"
    volume: str = "+0%"

class TTSResponse(BaseModel):
    audio_file: str
    duration: Optional[float] = None
    file_size: int

class STTRequest(BaseModel):
    audio_file: str
    language: str = "zh"

class STTResponse(BaseModel):
    text: str
    confidence: Optional[float] = None
    language: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime = Field(default_factory=now_china_naive)
    lm_studio_status: bool
    services: dict = Field(default_factory=dict)
    nacos_info: Optional[dict] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }

# 知识库管理相关模型
class KnowledgeBaseRequest(BaseModel):
    """创建/更新知识库请求"""
    name: str = Field(..., min_length=1, max_length=100, description="知识库名称")
    description: Optional[str] = Field(None, max_length=500, description="知识库描述")
    color: str = Field("#3B82F6", description="知识库颜色")

class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: str
    name: str
    description: Optional[str] = None
    color: str
    document_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }

class KnowledgeBaseDocumentRequest(BaseModel):
    """知识库文档关联请求"""
    document_ids: List[str] = Field(..., description="文档ID列表")

class DocumentWithKnowledgeBases(BaseModel):
    """带知识库信息的文档"""
    doc_id: str
    filename: str
    file_type: str
    chunk_count: int
    total_length: int
    created_at: str
    knowledge_bases: List[str] = Field(default_factory=list, description="关联的知识库ID列表")

class KnowledgeBaseListResponse(BaseModel):
    """知识库列表响应"""
    knowledge_bases: List[KnowledgeBaseResponse]
    total_count: int
    processing_time: float