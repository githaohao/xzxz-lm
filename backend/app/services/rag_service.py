"""
RAG (Retrieval-Augmented Generation) 服务
用于智能文档检索和增强生成
"""

import os
import uuid
import hashlib
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import numpy as np

from app.config import settings
from app.database import Database

logger = logging.getLogger(__name__)

class DocumentChunk:
    """文档块数据结构"""
    def __init__(self, content: str, metadata: Dict):
        self.content = content
        self.metadata = metadata
        self.chunk_id = str(uuid.uuid4())

class RAGService:
    """RAG服务类"""
    
    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.embedding_model = None
        self.text_splitter = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.db = Database()  # 数据库连接
        # 移除内存存储，改用数据库
        self.document_kb_mapping = {}  # doc_id -> [kb_id1, kb_id2, ...]  
        self._initialize()
    
    def _initialize(self):
        """初始化RAG服务"""
        try:
            # 设置 tokenizers 环境变量，避免并行处理警告
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            
            # 初始化ChromaDB
            chroma_path = os.path.join(settings.upload_dir, "chroma_db")
            os.makedirs(chroma_path, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=chroma_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 获取或创建集合
            self.collection = self.chroma_client.get_or_create_collection(
                name="document_chunks",
                metadata={"description": "存储文档分块的向量集合"}
            )
            
            # 初始化嵌入模型 (支持中文)
            model_name = settings.embedding_model
            logger.info(f"正在加载嵌入模型: {model_name}")
            
            try:
                self.embedding_model = SentenceTransformer(model_name)
                logger.info(f"嵌入模型加载成功: {model_name}")
            except Exception as e:
                logger.warning(f"加载 {model_name} 失败，回退到备用模型: {e}")
                # 保持与用户RAG服务一致的回退模型
                fallback_model = 'sentence-transformers/all-MiniLM-L6-v2'
                self.embedding_model = SentenceTransformer(fallback_model)
                logger.info(f"备用嵌入模型加载成功: {fallback_model}")
            
            # 初始化文本分割器
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.rag_chunk_size,
                chunk_overlap=settings.rag_chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
            )
            
            logger.info("RAG服务初始化成功")
            
        except Exception as e:
            logger.error(f"RAG服务初始化失败: {e}")
            raise
    
    async def process_document(self, content: str, filename: str, file_type: str) -> str:
        """
        处理文档：分块、向量化、存储
        
        Args:
            content: 文档内容
            filename: 文件名
            file_type: 文件类型
            
        Returns:
            document_id: 文档唯一标识
        """
        try:
            # 生成文档ID
            doc_id = self._generate_doc_id(content, filename)
            
            # 检查文档是否已存在
            existing_docs = self.collection.get(
                where={"doc_id": doc_id}
            )
            
            if existing_docs['ids']:
                logger.info(f"文档已存在，跳过处理: {filename}")
                return doc_id
            
            # 文档分块
            chunks = await self._split_document(content, filename, file_type)
            
            if not chunks:
                logger.warning(f"文档分块为空: {filename}")
                return doc_id
            
            # 向量化和存储
            await self._vectorize_and_store(chunks, doc_id)
            
            logger.info(f"文档处理完成: {filename}, 分块数: {len(chunks)}")
            return doc_id
            
        except Exception as e:
            logger.error(f"文档处理失败 {filename}: {e}")
            raise
    
    async def search_relevant_chunks(
        self, 
        query: str, 
        doc_ids: Optional[List[str]] = None,
        top_k: int = 5,
        min_similarity: float = 0.6
    ) -> List[Dict]:
        """
        检索相关文档块
        
        Args:
            query: 查询文本
            doc_ids: 限定搜索的文档ID列表
            top_k: 返回top-k个结果
            min_similarity: 最小相似度阈值
            
        Returns:
            相关文档块列表
        """
        try:
            if not query.strip():
                logger.warning("查询字符串为空")
                return []
            
            logger.info(f"开始RAG检索: query='{query}', doc_ids={doc_ids}, top_k={top_k}, min_similarity={min_similarity}")
            
            # 生成查询向量
            query_embedding = await self._generate_embedding(query)
            logger.info(f"查询向量生成成功，维度: {query_embedding.shape}")
            
            # 构建查询条件
            where_clause = None
            if doc_ids:
                where_clause = {"doc_id": {"$in": doc_ids}}
                logger.info(f"限定搜索文档: {doc_ids}")
            
            # 检查数据库中的文档数量
            total_docs = len(self.collection.get()['ids'])
            logger.info(f"数据库中共有 {total_docs} 个文档块")
            
            if total_docs == 0:
                logger.warning("数据库中没有文档块，请先上传并处理文档")
                return []
            
            # 向量检索
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=where_clause
            )
            
            logger.info(f"ChromaDB返回 {len(results['ids'][0]) if results['ids'][0] else 0} 个候选结果")
            
            # 处理结果
            relevant_chunks = []
            
            if results['ids'][0]:  # 如果有结果
                logger.info("处理检索结果...")
                for i, chunk_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i]
                    
                    # 改进的相似度计算
                    # ChromaDB使用L2距离，需要根据实际距离范围调整计算方式
                    if distance <= 2.0:  # 对于归一化向量，L2距离通常在0-2之间
                        similarity = max(0, 1 - distance / 2)
                    else:  # 对于未归一化向量，使用指数衰减
                        similarity = max(0, 1.0 / (1 + distance / 100))  # 调整衰减因子2
                    
                    logger.debug(f"候选结果 {i+1}: 距离={distance:.4f}, 相似度={similarity:.4f}")
                    
                    if similarity >= min_similarity:
                        relevant_chunks.append({
                            'chunk_id': chunk_id,
                            'content': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'similarity': similarity
                        })
                        logger.debug(f"结果 {i+1} 通过相似度阈值")
                    else:
                        logger.debug(f"结果 {i+1} 未通过相似度阈值 ({similarity:.4f} < {min_similarity})")
            else:
                logger.warning("ChromaDB没有返回任何结果")
            
            logger.info(f"最终检索到 {len(relevant_chunks)} 个相关文档块")
            
            # 如果没有结果，降低阈值重试一次
            if not relevant_chunks and min_similarity > 0.3:
                logger.info(f"没有找到结果，尝试降低相似度阈值从 {min_similarity} 到 0.3")
                return await self.search_relevant_chunks(
                    query=query,
                    doc_ids=doc_ids,
                    top_k=top_k,
                    min_similarity=0.3
                )
            
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"文档检索失败: {e}")
            return []
    
    async def get_document_info(self, doc_id: str) -> Optional[Dict]:
        """获取文档信息"""
        try:
            results = self.collection.get(
                where={"doc_id": doc_id},
                limit=1
            )
            
            if results['ids']:
                metadata = results['metadatas'][0]
                return {
                    'doc_id': doc_id,
                    'filename': metadata.get('filename'),
                    'file_type': metadata.get('file_type'),
                    'chunk_count': len(results['ids']),
                    'created_at': metadata.get('created_at')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取文档信息失败 {doc_id}: {e}")
            return None
    
    async def get_all_documents(self) -> List[Dict]:
        """获取所有文档列表"""
        try:
            # 获取所有文档块
            results = self.collection.get()
            
            # 按doc_id分组统计
            doc_stats = {}
            
            if results['ids']:
                for i, chunk_id in enumerate(results['ids']):
                    metadata = results['metadatas'][i]
                    doc_id = metadata.get('doc_id')
                    
                    if doc_id not in doc_stats:
                        doc_stats[doc_id] = {
                            'doc_id': doc_id,
                            'filename': metadata.get('filename', 'Unknown'),
                            'file_type': metadata.get('file_type', 'Unknown'),
                            'created_at': metadata.get('created_at', ''),
                            'chunk_count': 0,
                            'total_length': 0
                        }
                    
                    doc_stats[doc_id]['chunk_count'] += 1
                    doc_stats[doc_id]['total_length'] += metadata.get('chunk_length', 0)
            
            # 转换为列表并按创建时间排序
            documents = list(doc_stats.values())
            documents.sort(key=lambda x: x['created_at'], reverse=True)
            
            logger.info(f"获取到 {len(documents)} 个文档")
            return documents
            
        except Exception as e:
            logger.error(f"获取文档列表失败: {e}")
            return []

    async def get_document_chunks(self, doc_id: str) -> List[Dict]:
        """获取指定文档的所有分块"""
        try:
            # 获取所有相关分块
            results = self.collection.get(
                where={"doc_id": doc_id}
            )
            
            chunks = []
            if results['ids']:
                for i, chunk_id in enumerate(results['ids']):
                    chunks.append({
                        'chunk_id': chunk_id,
                        'content': results['documents'][i],
                        'metadata': results['metadatas'][i],
                        'similarity': 1.0  # 完整文档时相似度设为1.0
                    })
                
                # 按chunk_index排序
                chunks.sort(key=lambda x: x['metadata'].get('chunk_index', 0))
            
            logger.info(f"获取文档 {doc_id} 的 {len(chunks)} 个分块")
            return chunks
            
        except Exception as e:
            logger.error(f"获取文档分块失败 {doc_id}: {e}")
            return []

    async def delete_document(self, doc_id: str) -> bool:
        """删除文档及其所有分块"""
        try:
            # 获取所有相关分块
            results = self.collection.get(
                where={"doc_id": doc_id}
            )
            
            if results['ids']:
                # 删除分块
                self.collection.delete(ids=results['ids'])
                logger.info(f"删除文档成功: {doc_id}, 删除分块数: {len(results['ids'])}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除文档失败 {doc_id}: {e}")
            return False
    
    async def _split_document(self, content: str, filename: str, file_type: str) -> List[DocumentChunk]:
        """分割文档"""
        try:
            # 使用线程池执行文本分割（CPU密集型操作）
            loop = asyncio.get_event_loop()
            chunks_text = await loop.run_in_executor(
                self.executor,
                self.text_splitter.split_text,
                content
            )
            
            chunks = []
            for i, chunk_text in enumerate(chunks_text):
                if chunk_text.strip():  # 跳过空分块
                    metadata = {
                        'filename': filename,
                        'file_type': file_type,
                        'chunk_index': i,
                        'chunk_length': len(chunk_text),
                        'created_at': datetime.now().isoformat()
                    }
                    chunks.append(DocumentChunk(chunk_text, metadata))
            
            return chunks
            
        except Exception as e:
            logger.error(f"文档分块失败: {e}")
            return []
    
    async def _vectorize_and_store(self, chunks: List[DocumentChunk], doc_id: str):
        """向量化并存储文档块"""
        try:
            if not chunks:
                return
            
            # 准备数据
            chunk_texts = [chunk.content for chunk in chunks]
            chunk_ids = [chunk.chunk_id for chunk in chunks]
            metadatas = []
            
            for chunk in chunks:
                metadata = chunk.metadata.copy()
                metadata['doc_id'] = doc_id
                metadatas.append(metadata)
            
            # 生成嵌入向量
            embeddings = await self._generate_embeddings_batch(chunk_texts)
            
            # 存储到ChromaDB
            self.collection.add(
                ids=chunk_ids,
                embeddings=embeddings.tolist(),
                documents=chunk_texts,
                metadatas=metadatas
            )
            
            logger.info(f"成功存储 {len(chunks)} 个文档块")
            
        except Exception as e:
            logger.error(f"向量化存储失败: {e}")
            raise
    
    async def _generate_embedding(self, text: str) -> np.ndarray:
        """生成单个文本的嵌入向量"""
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            self.executor,
            lambda: self.embedding_model.encode(text, normalize_embeddings=True)
        )
        # 确保向量被归一化
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding
    
    async def _generate_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """批量生成嵌入向量"""
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            self.executor,
            lambda: self.embedding_model.encode(texts, normalize_embeddings=True)
        )
        # 确保所有向量被归一化
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # 避免除零
        embeddings = embeddings / norms
        return embeddings
    
    def _generate_doc_id(self, content: str, filename: str) -> str:
        """生成文档唯一标识"""
        # 使用内容和文件名的哈希作为文档ID
        content_hash = hashlib.md5(
            (content + filename).encode('utf-8')
        ).hexdigest()
        return f"doc_{content_hash[:16]}"
    
    # 知识库管理方法 - 使用数据库存储（不绑定用户）
    async def create_knowledge_base(self, name: str, description: str = None, color: str = "#3B82F6") -> Dict:
        """创建知识库"""
        kb_id = str(uuid.uuid4())
        now = datetime.now()
        
        try:
            async with self.db.get_connection() as db:
                # 使用默认用户ID（0表示全局）
                await db.execute("""
                    INSERT INTO knowledge_bases (id, user_id, name, description, color, document_count, created_at, updated_at)
                    VALUES (?, 0, ?, ?, ?, 0, ?, ?)
                """, (kb_id, name, description, color, now, now))
                await db.commit()
            
            knowledge_base = {
                "id": kb_id,
                "name": name,
                "description": description,
                "color": color,
                "document_count": 0,
                "created_at": now,
                "updated_at": now
            }
            
            logger.info(f"创建知识库成功: {name} (ID: {kb_id})")
            return knowledge_base
            
        except Exception as e:
            logger.error(f"创建知识库失败: {e}")
            raise
        
    async def get_all_knowledge_bases(self) -> List[Dict]:
        """获取所有知识库"""
        try:
            async with self.db.get_connection() as db:
                cursor = await db.execute("""
                    SELECT id, name, description, color, document_count, created_at, updated_at
                    FROM knowledge_bases
                    WHERE user_id = 0
                    ORDER BY created_at DESC
                """)
                
                rows = await cursor.fetchall()
                
                knowledge_bases = []
                for row in rows:
                    kb = {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "color": row[3],
                        "document_count": row[4],
                        "created_at": row[5],
                        "updated_at": row[6]
                    }
                    knowledge_bases.append(kb)
                
                return knowledge_bases
                
        except Exception as e:
            logger.error(f"获取知识库列表失败: {e}")
            return []
        
    async def get_knowledge_base(self, kb_id: str) -> Optional[Dict]:
        """获取单个知识库"""
        try:
            async with self.db.get_connection() as db:
                cursor = await db.execute("""
                    SELECT id, name, description, color, document_count, created_at, updated_at
                    FROM knowledge_bases
                    WHERE id = ? AND user_id = 0
                """, (kb_id,))
                
                row = await cursor.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "color": row[3],
                        "document_count": row[4],
                        "created_at": row[5],
                        "updated_at": row[6]
                    }
                return None
                
        except Exception as e:
            logger.error(f"获取知识库失败: {e}")
            return None
        
    async def update_knowledge_base(self, kb_id: str, name: str = None, description: str = None, color: str = None) -> bool:
        """更新知识库"""
        try:
            # 构建更新字段
            update_fields = []
            update_values = []
            
            if name is not None:
                update_fields.append("name = ?")
                update_values.append(name)
            if description is not None:
                update_fields.append("description = ?")
                update_values.append(description)
            if color is not None:
                update_fields.append("color = ?")
                update_values.append(color)
            
            if not update_fields:
                return True  # 没有需要更新的字段
            
            update_fields.append("updated_at = ?")
            update_values.append(datetime.now())
            update_values.append(kb_id)
            
            async with self.db.get_connection() as db:
                cursor = await db.execute(f"""
                    UPDATE knowledge_bases 
                    SET {', '.join(update_fields)}
                    WHERE id = ? AND user_id = 0
                """, update_values)
                
                await db.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"更新知识库成功: ID={kb_id}")
                    return True
                else:
                    logger.warning(f"知识库不存在: ID={kb_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"更新知识库失败: {e}")
            return False
        
    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库"""
        try:
            async with self.db.get_connection() as db:
                # 首先获取知识库名称用于日志
                cursor = await db.execute("""
                    SELECT name FROM knowledge_bases 
                    WHERE id = ? AND user_id = 0
                """, (kb_id,))
                
                row = await cursor.fetchone()
                kb_name = row[0] if row else "未知"
                
                # 删除知识库
                cursor = await db.execute("""
                    DELETE FROM knowledge_bases 
                    WHERE id = ? AND user_id = 0
                """, (kb_id,))
                
                await db.commit()
                
                if cursor.rowcount > 0:
                    # 清理内存中的文档关联关系
                    for doc_id in list(self.document_kb_mapping.keys()):
                        if kb_id in self.document_kb_mapping[doc_id]:
                            self.document_kb_mapping[doc_id].remove(kb_id)
                            if not self.document_kb_mapping[doc_id]:
                                del self.document_kb_mapping[doc_id]
                    
                    logger.info(f"删除知识库成功: {kb_name} (ID: {kb_id})")
                    return True
                else:
                    logger.warning(f"知识库不存在: ID={kb_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"删除知识库失败: {e}")
            return False
        
    async def add_documents_to_knowledge_base(self, kb_id: str, doc_ids: List[str]) -> bool:
        """将文档添加到知识库"""
        try:
            # 验证知识库是否存在
            kb = await self.get_knowledge_base(kb_id)
            if not kb:
                logger.warning(f"知识库不存在: ID={kb_id}")
                return False
            
            # 检查文档是否存在
            existing_docs = await self.get_all_documents()
            existing_doc_ids = {doc["doc_id"] for doc in existing_docs}
            
            added_count = 0
            for doc_id in doc_ids:
                if doc_id in existing_doc_ids:
                    if doc_id not in self.document_kb_mapping:
                        self.document_kb_mapping[doc_id] = []
                    if kb_id not in self.document_kb_mapping[doc_id]:
                        self.document_kb_mapping[doc_id].append(kb_id)
                        added_count += 1
            
            # 更新知识库的文档计数
            if added_count > 0:
                async with self.db.get_connection() as db:
                    await db.execute("""
                        UPDATE knowledge_bases 
                        SET document_count = document_count + ?, updated_at = ?
                        WHERE id = ? AND user_id = 0
                    """, (added_count, datetime.now(), kb_id))
                    await db.commit()
            
            kb_name = kb["name"]
            logger.info(f"向知识库 '{kb_name}' 添加了 {added_count} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"添加文档到知识库失败: {e}")
            return False
        
    async def remove_documents_from_knowledge_base(self, kb_id: str, doc_ids: List[str]) -> bool:
        """从知识库中移除文档"""
        try:
            # 验证知识库是否存在
            kb = await self.get_knowledge_base(kb_id)
            if not kb:
                logger.warning(f"知识库不存在: ID={kb_id}")
                return False
            
            removed_count = 0
            for doc_id in doc_ids:
                if doc_id in self.document_kb_mapping and kb_id in self.document_kb_mapping[doc_id]:
                    self.document_kb_mapping[doc_id].remove(kb_id)
                    if not self.document_kb_mapping[doc_id]:
                        del self.document_kb_mapping[doc_id]
                    removed_count += 1
            
            # 更新知识库的文档计数
            if removed_count > 0:
                async with self.db.get_connection() as db:
                    await db.execute("""
                        UPDATE knowledge_bases 
                        SET document_count = GREATEST(0, document_count - ?), updated_at = ?
                        WHERE id = ? AND user_id = 0
                    """, (removed_count, datetime.now(), kb_id))
                    await db.commit()
            
            kb_name = kb["name"]
            logger.info(f"从知识库 '{kb_name}' 移除了 {removed_count} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"从知识库移除文档失败: {e}")
            return False
        
    async def get_knowledge_base_documents(self, kb_id: str) -> List[str]:
        """获取知识库的所有文档ID"""
        # 验证知识库是否存在
        kb = await self.get_knowledge_base(kb_id)
        if not kb:
            logger.warning(f"知识库不存在: ID={kb_id}")
            return []
            
        return [doc_id for doc_id, kb_ids in self.document_kb_mapping.items() if kb_id in kb_ids]

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

# 全局RAG服务实例
rag_service = RAGService()
