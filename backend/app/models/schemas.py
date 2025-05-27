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