import uuid
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import math

from app.database import database
from app.models.chat_history import (
    ChatSession, ChatMessage, CreateSessionDto, CreateMessageDto, 
    QuerySessionsDto, ChatStatsResponse, PaginationInfo,
    SessionStatus, MessageRole, MessageType, MessageStatus, SortOrder
)

logger = logging.getLogger(__name__)

class ChatHistoryService:
    """聊天历史服务"""
    
    async def create_session(
        self, 
        user_id: int, 
        session_data: CreateSessionDto
    ) -> ChatSession:
        """创建聊天会话"""
        try:
            session_id = str(uuid.uuid4())
            title = session_data.title or f"对话 {datetime.now().strftime('%m-%d %H:%M')}"
            tags_json = json.dumps(session_data.tags) if session_data.tags else None
            
            async with database.get_connection() as db:
                await db.execute("""
                    INSERT INTO chat_sessions (
                        id, user_id, title, description, tags, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (session_id, user_id, title, session_data.description, tags_json))
                
                await db.commit()
                
                # 获取创建的会话
                return await self.get_session_by_id(user_id, session_id)
                
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            raise
    
    async def get_sessions(
        self, 
        user_id: int, 
        query_params: QuerySessionsDto
    ) -> Tuple[List[ChatSession], PaginationInfo]:
        """获取用户会话列表"""
        try:
            # 构建查询条件
            where_conditions = ["user_id = ?"]
            params = [user_id]
            
            if query_params.status:
                where_conditions.append("status = ?")
                params.append(query_params.status.value)
            else:
                # 默认不返回已删除的会话
                where_conditions.append("status != ?")
                params.append(SessionStatus.DELETED.value)
            
            if query_params.search:
                where_conditions.append("(title LIKE ? OR description LIKE ?)")
                search_term = f"%{query_params.search}%"
                params.extend([search_term, search_term])
            
            where_clause = " AND ".join(where_conditions)
            
            # 构建排序
            valid_sort_fields = ["created_at", "updated_at", "last_message_at", "message_count", "title"]
            sort_field = query_params.sort_by if query_params.sort_by in valid_sort_fields else "updated_at"
            sort_order = query_params.sort_order.value
            
            async with database.get_connection() as db:
                # 获取总数
                count_sql = f"SELECT COUNT(*) FROM chat_sessions WHERE {where_clause}"
                cursor = await db.execute(count_sql, params)
                total = (await cursor.fetchone())[0]
                
                # 计算分页
                page = query_params.page
                limit = query_params.limit
                offset = (page - 1) * limit
                total_pages = math.ceil(total / limit)
                
                # 获取会话列表
                list_sql = f"""
                    SELECT id, user_id, title, description, status, tags, 
                           message_count, last_message_at, created_at, updated_at
                    FROM chat_sessions 
                    WHERE {where_clause}
                    ORDER BY {sort_field} {sort_order}
                    LIMIT ? OFFSET ?
                """
                cursor = await db.execute(list_sql, params + [limit, offset])
                rows = await cursor.fetchall()
                
                sessions = []
                for row in rows:
                    tags = json.loads(row[5]) if row[5] else []
                    session = ChatSession(
                        id=row[0],
                        user_id=row[1],
                        title=row[2],
                        description=row[3],
                        status=SessionStatus(row[4]),
                        tags=tags,
                        message_count=row[6],
                        last_message_at=datetime.fromisoformat(row[7]) if row[7] else None,
                        created_at=datetime.fromisoformat(row[8]),
                        updated_at=datetime.fromisoformat(row[9])
                    )
                    sessions.append(session)
                
                pagination = PaginationInfo(
                    page=page,
                    limit=limit,
                    total=total,
                    total_pages=total_pages
                )
                
                return sessions, pagination
                
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            raise
    
    async def get_session_by_id(self, user_id: int, session_id: str) -> ChatSession:
        """获取单个会话详情"""
        try:
            async with database.get_connection() as db:
                cursor = await db.execute("""
                    SELECT id, user_id, title, description, status, tags,
                           message_count, last_message_at, created_at, updated_at
                    FROM chat_sessions 
                    WHERE id = ? AND user_id = ?
                """, (session_id, user_id))
                
                row = await cursor.fetchone()
                if not row:
                    raise ValueError(f"会话不存在: {session_id}")
                
                tags = json.loads(row[5]) if row[5] else []
                return ChatSession(
                    id=row[0],
                    user_id=row[1],
                    title=row[2],
                    description=row[3],
                    status=SessionStatus(row[4]),
                    tags=tags,
                    message_count=row[6],
                    last_message_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    created_at=datetime.fromisoformat(row[8]),
                    updated_at=datetime.fromisoformat(row[9])
                )
                
        except Exception as e:
            logger.error(f"获取会话详情失败: {e}")
            raise
    
    async def update_session(
        self, 
        user_id: int, 
        session_id: str, 
        update_data: Dict[str, Any]
    ) -> ChatSession:
        """更新会话信息"""
        try:
            # 验证会话所有权
            await self.get_session_by_id(user_id, session_id)
            
            # 构建更新字段
            update_fields = []
            params = []
            
            if "title" in update_data:
                update_fields.append("title = ?")
                params.append(update_data["title"])
            
            if "description" in update_data:
                update_fields.append("description = ?")
                params.append(update_data["description"])
            
            if "tags" in update_data:
                update_fields.append("tags = ?")
                params.append(json.dumps(update_data["tags"]))
            
            if not update_fields:
                # 没有更新字段，直接返回原会话
                return await self.get_session_by_id(user_id, session_id)
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.extend([session_id, user_id])
            
            async with database.get_connection() as db:
                update_sql = f"""
                    UPDATE chat_sessions 
                    SET {', '.join(update_fields)}
                    WHERE id = ? AND user_id = ?
                """
                await db.execute(update_sql, params)
                await db.commit()
                
                return await self.get_session_by_id(user_id, session_id)
                
        except Exception as e:
            logger.error(f"更新会话失败: {e}")
            raise
    
    async def delete_session(self, user_id: int, session_id: str) -> bool:
        """删除会话（软删除）"""
        try:
            # 验证会话所有权
            await self.get_session_by_id(user_id, session_id)
            
            async with database.get_connection() as db:
                await db.execute("""
                    UPDATE chat_sessions 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                """, (SessionStatus.DELETED.value, session_id, user_id))
                
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            raise
    
    async def archive_session(self, user_id: int, session_id: str) -> ChatSession:
        """归档会话"""
        try:
            # 验证会话所有权
            await self.get_session_by_id(user_id, session_id)
            
            async with database.get_connection() as db:
                await db.execute("""
                    UPDATE chat_sessions 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                """, (SessionStatus.ARCHIVED.value, session_id, user_id))
                
                await db.commit()
                return await self.get_session_by_id(user_id, session_id)
                
        except Exception as e:
            logger.error(f"归档会话失败: {e}")
            raise
    
    async def restore_session(self, user_id: int, session_id: str) -> ChatSession:
        """恢复会话"""
        try:
            # 验证会话所有权
            await self.get_session_by_id(user_id, session_id)
            
            async with database.get_connection() as db:
                await db.execute("""
                    UPDATE chat_sessions 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                """, (SessionStatus.ACTIVE.value, session_id, user_id))
                
                await db.commit()
                return await self.get_session_by_id(user_id, session_id)
                
        except Exception as e:
            logger.error(f"恢复会话失败: {e}")
            raise
    
    async def get_session_messages(
        self, 
        user_id: int, 
        session_id: str, 
        page: int = 1, 
        limit: int = 50
    ) -> Tuple[List[ChatMessage], PaginationInfo]:
        """获取会话消息列表"""
        try:
            # 验证会话所有权
            await self.get_session_by_id(user_id, session_id)
            
            async with database.get_connection() as db:
                # 获取总消息数
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM chat_messages WHERE session_id = ? AND user_id = ?",
                    (session_id, user_id)
                )
                total = (await cursor.fetchone())[0]
                
                # 计算分页
                offset = (page - 1) * limit
                total_pages = math.ceil(total / limit)
                
                # 获取消息列表
                cursor = await db.execute("""
                    SELECT id, session_id, user_id, role, content, message_type,
                           metadata, status, parent_message_id, sequence_number, created_at
                    FROM chat_messages 
                    WHERE session_id = ? AND user_id = ?
                    ORDER BY sequence_number ASC
                    LIMIT ? OFFSET ?
                """, (session_id, user_id, limit, offset))
                
                rows = await cursor.fetchall()
                messages = []
                
                for row in rows:
                    metadata = json.loads(row[6]) if row[6] else None
                    message = ChatMessage(
                        id=row[0],
                        session_id=row[1],
                        user_id=row[2],
                        role=MessageRole(row[3]),
                        content=row[4],
                        message_type=MessageType(row[5]),
                        metadata=metadata,
                        status=MessageStatus(row[7]),
                        parent_message_id=row[8],
                        sequence_number=row[9],
                        created_at=datetime.fromisoformat(row[10])
                    )
                    messages.append(message)
                
                pagination = PaginationInfo(
                    page=page,
                    limit=limit,
                    total=total,
                    total_pages=total_pages
                )
                
                return messages, pagination
                
        except Exception as e:
            logger.error(f"获取会话消息失败: {e}")
            raise
    
    async def add_message(
        self, 
        user_id: int, 
        message_data: CreateMessageDto
    ) -> ChatMessage:
        """添加消息到会话"""
        try:
            # 验证会话所有权
            await self.get_session_by_id(user_id, message_data.session_id)
            
            message_id = str(uuid.uuid4())
            metadata_json = json.dumps(message_data.metadata) if message_data.metadata else None
            
            async with database.get_connection() as db:
                # 获取下一个序列号
                cursor = await db.execute(
                    "SELECT COALESCE(MAX(sequence_number), 0) + 1 FROM chat_messages WHERE session_id = ?",
                    (message_data.session_id,)
                )
                sequence_number = (await cursor.fetchone())[0]
                
                # 插入消息
                await db.execute("""
                    INSERT INTO chat_messages (
                        id, session_id, user_id, role, content, message_type,
                        metadata, status, parent_message_id, sequence_number, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    message_id, message_data.session_id, user_id, message_data.role.value,
                    message_data.content, message_data.message_type.value, metadata_json,
                    MessageStatus.SENT.value, message_data.parent_message_id, sequence_number
                ))
                
                # 更新会话统计
                await db.execute("""
                    UPDATE chat_sessions 
                    SET message_count = message_count + 1,
                        last_message_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                """, (message_data.session_id, user_id))
                
                await db.commit()
                
                # 返回创建的消息
                cursor = await db.execute("""
                    SELECT id, session_id, user_id, role, content, message_type,
                           metadata, status, parent_message_id, sequence_number, created_at
                    FROM chat_messages 
                    WHERE id = ?
                """, (message_id,))
                
                row = await cursor.fetchone()
                metadata = json.loads(row[6]) if row[6] else None
                
                return ChatMessage(
                    id=row[0],
                    session_id=row[1],
                    user_id=row[2],
                    role=MessageRole(row[3]),
                    content=row[4],
                    message_type=MessageType(row[5]),
                    metadata=metadata,
                    status=MessageStatus(row[7]),
                    parent_message_id=row[8],
                    sequence_number=row[9],
                    created_at=datetime.fromisoformat(row[10])
                )
                
        except Exception as e:
            logger.error(f"添加消息失败: {e}")
            raise
    
    async def add_messages_batch(
        self, 
        user_id: int, 
        messages: List[CreateMessageDto]
    ) -> List[ChatMessage]:
        """批量添加消息"""
        try:
            result_messages = []
            
            # 按会话分组
            session_groups = {}
            for msg in messages:
                if msg.session_id not in session_groups:
                    session_groups[msg.session_id] = []
                session_groups[msg.session_id].append(msg)
            
            async with database.get_connection() as db:
                for session_id, session_messages in session_groups.items():
                    # 验证会话所有权
                    await self.get_session_by_id(user_id, session_id)
                    
                    # 获取起始序列号
                    cursor = await db.execute(
                        "SELECT COALESCE(MAX(sequence_number), 0) FROM chat_messages WHERE session_id = ?",
                        (session_id,)
                    )
                    base_sequence = (await cursor.fetchone())[0]
                    
                    # 批量插入消息
                    for i, msg_data in enumerate(session_messages):
                        message_id = str(uuid.uuid4())
                        metadata_json = json.dumps(msg_data.metadata) if msg_data.metadata else None
                        sequence_number = base_sequence + i + 1
                        
                        await db.execute("""
                            INSERT INTO chat_messages (
                                id, session_id, user_id, role, content, message_type,
                                metadata, status, parent_message_id, sequence_number, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, (
                            message_id, session_id, user_id, msg_data.role.value,
                            msg_data.content, msg_data.message_type.value, metadata_json,
                            MessageStatus.SENT.value, msg_data.parent_message_id, sequence_number
                        ))
                        
                        # 构建返回的消息对象
                        message = ChatMessage(
                            id=message_id,
                            session_id=session_id,
                            user_id=user_id,
                            role=msg_data.role,
                            content=msg_data.content,
                            message_type=msg_data.message_type,
                            metadata=msg_data.metadata,
                            status=MessageStatus.SENT,
                            parent_message_id=msg_data.parent_message_id,
                            sequence_number=sequence_number,
                            created_at=datetime.now()
                        )
                        result_messages.append(message)
                    
                    # 更新会话统计
                    await db.execute("""
                        UPDATE chat_sessions 
                        SET message_count = message_count + ?,
                            last_message_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ?
                    """, (len(session_messages), session_id, user_id))
                
                await db.commit()
                return result_messages
                
        except Exception as e:
            logger.error(f"批量添加消息失败: {e}")
            raise
    
    async def delete_message(self, user_id: int, message_id: str) -> bool:
        """删除消息"""
        try:
            async with database.get_connection() as db:
                # 验证消息所有权
                cursor = await db.execute(
                    "SELECT session_id FROM chat_messages WHERE id = ? AND user_id = ?",
                    (message_id, user_id)
                )
                row = await cursor.fetchone()
                if not row:
                    raise ValueError(f"消息不存在: {message_id}")
                
                session_id = row[0]
                
                # 删除消息
                await db.execute(
                    "DELETE FROM chat_messages WHERE id = ? AND user_id = ?",
                    (message_id, user_id)
                )
                
                # 更新会话统计
                await db.execute("""
                    UPDATE chat_sessions 
                    SET message_count = message_count - 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                """, (session_id, user_id))
                
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"删除消息失败: {e}")
            raise
    
    async def get_stats(self, user_id: int) -> ChatStatsResponse:
        """获取用户聊天统计信息"""
        try:
            async with database.get_connection() as db:
                # 获取会话统计
                cursor = await db.execute("""
                    SELECT 
                        COUNT(*) as total_sessions,
                        SUM(CASE WHEN status = 'archived' THEN 1 ELSE 0 END) as archived_sessions
                    FROM chat_sessions 
                    WHERE user_id = ? AND status != 'deleted'
                """, (user_id,))
                
                session_stats = await cursor.fetchone()
                
                # 获取消息统计
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM chat_messages WHERE user_id = ?",
                    (user_id,)
                )
                total_messages = (await cursor.fetchone())[0]
                
                return ChatStatsResponse(
                    total_sessions=session_stats[0],
                    total_messages=total_messages,
                    archived_sessions=session_stats[1]
                )
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise

# 创建服务实例
chat_history_service = ChatHistoryService() 