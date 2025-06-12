from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union, TypeVar, Generic
from datetime import datetime
from enum import Enum

T = TypeVar('T')

class SessionStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class MessageType(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    FILE = "file"
    MULTIMODAL = "multimodal"

class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class SortOrder(str, Enum):
    ASC = "ASC"
    DESC = "DESC"

# 请求模型
class CreateSessionDto(BaseModel):
    title: Optional[str] = Field(None, max_length=200, description="会话标题")
    description: Optional[str] = Field(None, max_length=500, description="会话描述")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")

class CreateMessageDto(BaseModel):
    session_id: str = Field(..., description="会话ID")
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., min_length=1, description="消息内容")
    message_type: MessageType = Field(MessageType.TEXT, description="消息类型")
    metadata: Optional[Dict[str, Any]] = Field(None, description="消息元数据")
    parent_message_id: Optional[str] = Field(None, description="父消息ID")

class QuerySessionsDto(BaseModel):
    page: Optional[int] = Field(1, ge=1, description="页码")
    limit: Optional[int] = Field(20, ge=1, le=100, description="每页数量")
    status: Optional[SessionStatus] = Field(None, description="会话状态")
    search: Optional[str] = Field(None, max_length=100, description="搜索关键词")
    sort_by: Optional[str] = Field("updated_at", description="排序字段")
    sort_order: Optional[SortOrder] = Field(SortOrder.DESC, description="排序方向")

# 响应模型
class ChatMessage(BaseModel):
    id: str = Field(..., description="消息ID")
    session_id: str = Field(..., description="会话ID")
    user_id: int = Field(..., description="用户ID")
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    message_type: MessageType = Field(..., description="消息类型")
    metadata: Optional[Dict[str, Any]] = Field(None, description="消息元数据")
    status: MessageStatus = Field(..., description="消息状态")
    parent_message_id: Optional[str] = Field(None, description="父消息ID")
    sequence_number: int = Field(..., description="序列号")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }

class ChatSession(BaseModel):
    id: str = Field(..., description="会话ID")
    user_id: int = Field(..., description="用户ID")
    title: str = Field(..., description="会话标题")
    description: Optional[str] = Field(None, description="会话描述")
    status: SessionStatus = Field(..., description="会话状态")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    last_message_at: Optional[datetime] = Field(None, description="最后消息时间")
    message_count: int = Field(..., description="消息数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    messages: Optional[List[ChatMessage]] = Field(None, description="消息列表")

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }

class ChatStatsResponse(BaseModel):
    total_sessions: int = Field(..., description="总会话数")
    total_messages: int = Field(..., description="总消息数")
    archived_sessions: int = Field(..., description="归档会话数")

class PaginationInfo(BaseModel):
    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页数量")
    total: int = Field(..., description="总数量")
    total_pages: int = Field(..., description="总页数")

class ChatHistoryResponse(BaseModel, Generic[T]):
    code: int = Field(200, description="响应状态码")
    msg: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    pagination: Optional[PaginationInfo] = Field(None, description="分页信息")

# 知识库相关模型
class KnowledgeBase(BaseModel):
    id: str = Field(..., description="知识库ID")
    user_id: int = Field(..., description="用户ID")
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    color: str = Field("#3B82F6", description="知识库颜色")
    is_default: bool = Field(False, description="是否为默认知识库")
    document_count: int = Field(0, description="文档数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }

class CreateKnowledgeBaseDto(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="知识库名称")
    description: Optional[str] = Field(None, max_length=500, description="知识库描述")
    color: Optional[str] = Field("#3B82F6", description="知识库颜色")

class UpdateKnowledgeBaseDto(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="知识库名称")
    description: Optional[str] = Field(None, max_length=500, description="知识库描述")
    color: Optional[str] = Field(None, description="知识库颜色")

class Document(BaseModel):
    id: str = Field(..., description="文档ID")
    user_id: int = Field(..., description="用户ID")
    knowledge_base_id: Optional[str] = Field(None, description="知识库ID")
    doc_id: str = Field(..., description="RAG文档ID")
    filename: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型")
    file_size: Optional[int] = Field(None, description="文件大小")
    chunk_count: int = Field(0, description="分块数量")
    ocr_completed: bool = Field(False, description="OCR是否完成")
    rag_enabled: bool = Field(True, description="是否启用RAG")
    content_preview: Optional[str] = Field(None, description="内容预览")
    upload_path: Optional[str] = Field(None, description="上传路径")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        } 