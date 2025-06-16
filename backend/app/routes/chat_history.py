from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Optional
import logging

from app.models.chat_history import (
    ChatSession, ChatMessage, CreateSessionDto, CreateMessageDto, 
    QuerySessionsDto, ChatHistoryResponse, ChatStatsResponse,
    PaginationInfo
)
from app.services.chat_history_service import chat_history_service
from app.middleware.auth import get_current_user, get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user/chat", tags=["chat-history"])

@router.post("/sessions", response_model=ChatHistoryResponse[ChatSession])
async def create_session(
    session_data: CreateSessionDto,
    user_id: int = Depends(get_current_user_id)
):
    """创建聊天会话"""
    try:
        print(f"session_data: {user_id}")
        logger.info(f"用户 {user_id} 创建会话: {session_data.title}")
        
        session = await chat_history_service.create_session(user_id, session_data)
        
        return ChatHistoryResponse(
            code=200,
            msg="会话创建成功",
            data=session
        )
        
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions", response_model=ChatHistoryResponse[List[ChatSession]])
async def get_sessions(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="会话状态"),
    search: Optional[str] = Query(None, max_length=100, description="搜索关键词"),
    sort_by: Optional[str] = Query("updated_at", description="排序字段"),
    sort_order: Optional[str] = Query("DESC", description="排序方向"),
    user_id: int = Depends(get_current_user_id)
):
    """获取用户会话列表"""
    try:
        query_params = QuerySessionsDto(
            page=page,
            limit=limit,
            status=status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )

        print(f"query_params: {user_id}")
        
        sessions, pagination = await chat_history_service.get_sessions(user_id, query_params)
        
        return ChatHistoryResponse(
            code=200,
            msg="获取会话列表成功",
            data=sessions,
            pagination=pagination
        )
        
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}", response_model=ChatHistoryResponse[ChatSession])
async def get_session_detail(
    session_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """获取会话详情"""
    try:
        session = await chat_history_service.get_session_by_id(user_id, session_id)
        
        return ChatHistoryResponse(
            code=200,
            msg="获取会话详情成功",
            data=session
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取会话详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sessions/{session_id}", response_model=ChatHistoryResponse[ChatSession])
async def update_session(
    session_id: str,
    update_data: CreateSessionDto,
    user_id: int = Depends(get_current_user_id)
):
    """更新会话信息"""
    try:
        # 转换为字典，过滤None值
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        session = await chat_history_service.update_session(user_id, session_id, update_dict)
        
        return ChatHistoryResponse(
            code=200,
            msg="会话更新成功",
            data=session
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}", response_model=ChatHistoryResponse)
async def delete_session(
    session_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """删除会话"""
    try:
        success = await chat_history_service.delete_session(user_id, session_id)
        
        if success:
            return ChatHistoryResponse(
                code=200,
                msg="会话删除成功"
            )
        else:
            raise HTTPException(status_code=500, detail="删除会话失败")
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sessions/{session_id}/archive", response_model=ChatHistoryResponse[ChatSession])
async def archive_session(
    session_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """归档会话"""
    try:
        session = await chat_history_service.archive_session(user_id, session_id)
        
        return ChatHistoryResponse(
            code=200,
            msg="会话归档成功",
            data=session
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"归档会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sessions/{session_id}/restore", response_model=ChatHistoryResponse[ChatSession])
async def restore_session(
    session_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """恢复会话"""
    try:
        session = await chat_history_service.restore_session(user_id, session_id)
        
        return ChatHistoryResponse(
            code=200,
            msg="会话恢复成功",
            data=session
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"恢复会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/messages", response_model=ChatHistoryResponse[List[ChatMessage]])
async def get_session_messages(
    session_id: str,
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(50, ge=1, le=100, description="每页数量"),
    user_id: int = Depends(get_current_user_id)
):
    """获取会话消息列表"""
    try:
        messages, pagination = await chat_history_service.get_session_messages(
            user_id, session_id, page, limit
        )
        
        return ChatHistoryResponse(
            code=200,
            msg="获取消息列表成功",
            data=messages,
            pagination=pagination
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取消息列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/messages", response_model=ChatHistoryResponse[ChatMessage])
async def add_message(
    session_id: str,
    message_data: CreateMessageDto,
    user_id: int = Depends(get_current_user_id)
):
    """添加消息到会话"""
    try:
        # 确保session_id匹配
        message_data.session_id = session_id
        
        message = await chat_history_service.add_message(user_id, message_data)
        
        return ChatHistoryResponse(
            code=200,
            msg="消息添加成功",
            data=message
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"添加消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messages/batch", response_model=ChatHistoryResponse[List[ChatMessage]])
async def add_messages_batch(
    messages: List[CreateMessageDto],
    user_id: int = Depends(get_current_user_id)
):
    """批量添加消息"""
    try:
        result_messages = await chat_history_service.add_messages_batch(user_id, messages)
        
        return ChatHistoryResponse(
            code=200,
            msg=f"批量添加 {len(result_messages)} 条消息成功",
            data=result_messages
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"批量添加消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/messages/{message_id}", response_model=ChatHistoryResponse)
async def delete_message(
    message_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """删除消息"""
    try:
        success = await chat_history_service.delete_message(user_id, message_id)
        
        if success:
            return ChatHistoryResponse(
                code=200,
                msg="消息删除成功"
            )
        else:
            raise HTTPException(status_code=500, detail="删除消息失败")
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"删除消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=ChatHistoryResponse[ChatStatsResponse])
async def get_chat_stats(
    user_id: int = Depends(get_current_user_id)
):
    """获取用户聊天统计信息"""
    try:
        stats = await chat_history_service.get_stats(user_id)
        
        return ChatHistoryResponse(
            code=200,
            msg="获取统计信息成功",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=ChatHistoryResponse)
async def health_check():
    """聊天历史服务健康检查"""
    try:
        return ChatHistoryResponse(
            code=200,
            msg="聊天历史服务正常"
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 