from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    FILE = "file"

class ChatMessage(BaseModel):
    id: Optional[str] = None
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = Field(default_factory=datetime.now)
    is_user: bool = True
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=4096)
    stream: bool = False

class FileData(BaseModel):
    name: str
    type: str
    size: int
    content: Optional[str] = None
    doc_id: Optional[str] = None  # RAG文档ID
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
    min_similarity: float = Field(default=0.6, ge=0.0, le=1.0)

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

class ChatResponse(BaseModel):
    response: str
    message_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None

class FileUploadResponse(BaseModel):
    file_id: str
    file_name: str
    file_path: str
    file_size: int
    file_type: str
    upload_time: datetime = Field(default_factory=datetime.now)

class OCRRequest(BaseModel):
    file_path: str
    language: str = "chi_sim+eng"
    use_paddleocr: bool = True

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
    timestamp: datetime = Field(default_factory=datetime.now)
    lm_studio_status: bool
    services: dict = Field(default_factory=dict) 