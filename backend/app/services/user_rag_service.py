"""
用户绑定的RAG服务
为每个用户创建独立的ChromaDB集合，实现数据隔离
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import PyPDF2
from docx import Document
import aiofiles

from app.database import Database
from app.config import settings

logger = logging.getLogger(__name__)

class UserRAGService:
    """用户绑定的RAG服务"""
    
    def __init__(self):
        self.db = Database()
        self.chroma_client = None
        self.embedding_model = None
        self._initialized = False

    def _get_user_collection_name(self, user_id: int) -> str:
        """获取用户专属的集合名称"""
        return f"user_{user_id}_docs"
    
    async def get_user_collection(self, user_id: int):
        """获取或创建用户专属的ChromaDB集合"""
        if not self._initialized:
            await self.initialize()
        
        collection_name = self._get_user_collection_name(user_id)
        
        try:
            # 尝试获取现有集合
            collection = self.chroma_client.get_collection(collection_name)
        except ValueError:
            # 集合不存在，创建新集合
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"为用户 {user_id} 创建新的文档集合: {collection_name}")
        
        return collection
    
    async def add_document(self, user_id: int, file_path: str, title: str = None) -> str:
        """为用户添加文档到知识库"""
        try:
            # 生成文档ID
            doc_id = str(uuid.uuid4())
            
            # 提取文档内容
            content = await self._extract_text_from_file(file_path)
            if not content.strip():
                raise ValueError("无法从文档中提取有效内容")
            
            # 分块处理文档
            chunks = self._split_text(content)
            
            # 获取用户集合
            collection = await self.get_user_collection(user_id)
            
            # 生成嵌入
            embeddings = self.embedding_model.encode(chunks).tolist()
            
            # 准备元数据
            metadatas = []
            ids = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                ids.append(chunk_id)
                metadatas.append({
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "file_path": file_path,
                    "title": title or os.path.basename(file_path),
                    "created_at": datetime.now().isoformat()
                })
            
            # 添加到ChromaDB
            collection.add(
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            
            # 保存文档信息到数据库
            await self._save_document_to_db(user_id, doc_id, file_path, title, len(chunks))
            
            logger.info(f"用户 {user_id} 添加文档成功: {title}, 分块数: {len(chunks)}")
            return doc_id
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise e
    
    async def search_documents(self, user_id: int, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """在用户的知识库中搜索相关文档"""
        try:
            collection = await self.get_user_collection(user_id)
            
            # 生成查询嵌入
            query_embedding = self.embedding_model.encode([query]).tolist()[0]
            
            # 在ChromaDB中搜索
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # 格式化结果
            search_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    search_results.append({
                        "id": results['ids'][0][i],
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "similarity": 1 - results['distances'][0][i]  # 转换距离为相似度
                    })
            
            return search_results
            
        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            return []
    
    async def get_user_documents(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的文档列表"""
        try:
            query = """
                SELECT doc_id, title, file_path, chunk_count, created_at, updated_at
                FROM user_documents 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            """
            
            async with self.db.get_connection() as conn:
                cursor = await conn.execute(query, (user_id,))
                rows = await cursor.fetchall()
                
                documents = []
                for row in rows:
                    documents.append({
                        "doc_id": row[0],
                        "title": row[1],
                        "file_path": row[2],
                        "chunk_count": row[3],
                        "created_at": row[4],
                        "updated_at": row[5]
                    })
                
                return documents
                
        except Exception as e:
            logger.error(f"获取用户文档列表失败: {e}")
            return []
    
    async def delete_document(self, user_id: int, doc_id: str) -> bool:
        """删除用户的文档"""
        try:
            collection = await self.get_user_collection(user_id)
            
            # 获取文档的所有分块ID
            chunk_ids = []
            result = collection.get(where={"doc_id": doc_id})
            if result['ids']:
                chunk_ids = result['ids']
            
            # 从ChromaDB删除
            if chunk_ids:
                collection.delete(ids=chunk_ids)
            
            # 从数据库删除记录
            await self._delete_document_from_db(user_id, doc_id)
            
            logger.info(f"用户 {user_id} 删除文档成功: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    async def _extract_text_from_file(self, file_path: str) -> str:
        """从文件中提取文本内容"""
        _, ext = os.path.splitext(file_path.lower())
        
        try:
            if ext == '.pdf':
                return await self._extract_from_pdf(file_path)
            elif ext in ['.docx', '.doc']:
                return await self._extract_from_docx(file_path)
            elif ext == '.txt':
                return await self._extract_from_txt(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {ext}")
        except Exception as e:
            logger.error(f"提取文件内容失败: {e}")
            raise e
    
    async def _extract_from_pdf(self, file_path: str) -> str:
        """从PDF文件提取文本"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"PDF文本提取失败: {e}")
            raise e
        
        return text.strip()
    
    async def _extract_from_docx(self, file_path: str) -> str:
        """从DOCX文件提取文本"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"DOCX文本提取失败: {e}")
            raise e
    
    async def _extract_from_txt(self, file_path: str) -> str:
        """从TXT文件提取文本"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                content = await file.read()
            return content.strip()
        except Exception as e:
            logger.error(f"TXT文本提取失败: {e}")
            raise e
    
    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """将文本分割成较小的块"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # 如果不是最后一块，尝试在句号处分割
            if end < len(text):
                # 寻找最近的句号
                last_period = text.rfind('.', start, end)
                if last_period > start:
                    end = last_period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 设置下一块的开始位置，考虑重叠
            start = max(start + 1, end - overlap)
            
            if start >= len(text):
                break
        
        return chunks
    
    async def _save_document_to_db(self, user_id: int, doc_id: str, file_path: str, title: str, chunk_count: int):
        """保存文档信息到数据库"""
        query = """
            INSERT INTO user_documents (user_id, doc_id, title, file_path, chunk_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """
        
        async with self.db.get_connection() as conn:
            await conn.execute(query, (user_id, doc_id, title, file_path, chunk_count))
            await conn.commit()
    
    async def _delete_document_from_db(self, user_id: int, doc_id: str):
        """从数据库删除文档记录"""
        query = "DELETE FROM user_documents WHERE user_id = ? AND doc_id = ?"
        
        async with self.db.get_connection() as conn:
            await conn.execute(query, (user_id, doc_id))
            await conn.commit()

# 创建全局实例
user_rag_service = UserRAGService() 