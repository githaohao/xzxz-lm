import sqlite3
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Dict, List, Any
import json
import uuid
import aiosqlite
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    """SQLite数据库管理类"""
    
    def __init__(self, db_path: str = "data/chat_history.db"):
        self.db_path = db_path
        # 确保数据目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self):
        """初始化数据库表"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 启用外键约束
                await db.execute("PRAGMA foreign_keys = ON")
                
                # 创建用户表
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER UNIQUE NOT NULL,
                        username TEXT,
                        nickname TEXT,
                        email TEXT,
                        avatar TEXT,
                        first_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建聊天会话表
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
                        tags TEXT,  -- JSON数组
                        message_count INTEGER DEFAULT 0,
                        last_message_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                    )
                """)
                
                # 创建聊天消息表
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                        content TEXT NOT NULL,
                        message_type TEXT DEFAULT 'text' CHECK (message_type IN ('text', 'voice', 'image', 'file', 'multimodal')),
                        metadata TEXT,  -- JSON对象
                        status TEXT DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'read', 'failed')),
                        parent_message_id TEXT,
                        sequence_number INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                        FOREIGN KEY (parent_message_id) REFERENCES chat_messages (id) ON DELETE SET NULL
                    )
                """)
                
                # 创建知识库表
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_bases (
                        id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        color TEXT DEFAULT '#3B82F6',
                        is_default BOOLEAN DEFAULT FALSE,
                        document_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                    )
                """)
                
                # 创建文档表
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        knowledge_base_id TEXT,
                        doc_id TEXT UNIQUE NOT NULL,  -- RAG系统中的文档ID
                        filename TEXT NOT NULL,
                        file_type TEXT NOT NULL,
                        file_size INTEGER,
                        chunk_count INTEGER DEFAULT 0,
                        ocr_completed BOOLEAN DEFAULT FALSE,
                        rag_enabled BOOLEAN DEFAULT TRUE,
                        content_preview TEXT,  -- 内容预览
                        upload_path TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                        FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases (id) ON DELETE SET NULL
                    )
                """)
                
                # 创建用户RAG文档表（专门用于用户独立的RAG服务）
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_documents (
                        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                        user_id INTEGER NOT NULL,
                        doc_id TEXT UNIQUE NOT NULL,  -- ChromaDB中的文档ID
                        title TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_type TEXT,
                        file_size INTEGER,
                        chunk_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                    )
                """)
                
                # 创建索引
                await db.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions (user_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_status ON chat_sessions (status)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions (updated_at)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages (session_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages (user_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages (created_at)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_bases_user_id ON knowledge_bases (user_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents (user_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_knowledge_base_id ON documents (knowledge_base_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_doc_id ON documents (doc_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_user_documents_user_id ON user_documents (user_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_user_documents_doc_id ON user_documents (doc_id)")
                
                await db.commit()
                logger.info("✅ 数据库初始化成功")
                
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接"""
        try:
            db = await aiosqlite.connect(self.db_path)
            await db.execute("PRAGMA foreign_keys = ON")
            yield db
        finally:
            await db.close()
    
    async def ensure_user_exists(self, user_id: int, user_info: Optional[Dict] = None) -> bool:
        """确保用户存在，如果不存在则创建"""
        try:
            async with self.get_connection() as db:
                # 检查用户是否存在
                cursor = await db.execute(
                    "SELECT id FROM users WHERE user_id = ?",
                    (user_id,)
                )
                user = await cursor.fetchone()
                
                if not user:
                    # 创建新用户
                    username = user_info.get('username', f'user_{user_id}') if user_info else f'user_{user_id}'
                    nickname = user_info.get('nickname', username) if user_info else username
                    email = user_info.get('email', '') if user_info else ''
                    avatar = user_info.get('avatar', '') if user_info else ''
                    
                    await db.execute("""
                        INSERT INTO users (user_id, username, nickname, email, avatar)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, username, nickname, email, avatar))
                    
                    # 创建默认知识库
                    kb_id = str(uuid.uuid4())
                    await db.execute("""
                        INSERT INTO knowledge_bases (id, user_id, name, description, is_default)
                        VALUES (?, ?, ?, ?, ?)
                    """, (kb_id, user_id, "默认知识库", "用户默认知识库", True))
                    
                    await db.commit()
                    logger.info(f"✅ 创建新用户: {user_id} ({username})")
                else:
                    # 更新最后登录时间
                    await db.execute(
                        "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                        (user_id,)
                    )
                    await db.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"❌ 确保用户存在失败: {e}")
            return False

# 全局数据库实例
database = Database()
