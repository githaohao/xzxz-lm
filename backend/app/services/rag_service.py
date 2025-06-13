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
        # 文档-知识库关联关系缓存，从数据库加载
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
                logger.error(f"加载嵌入模型 {model_name} 失败: {e}")
                # 使用中文友好的备用模型
                fallback_model = 'shibing624/text2vec-base-chinese'
                try:
                    self.embedding_model = SentenceTransformer(fallback_model)
                    logger.info(f"备用嵌入模型加载成功: {fallback_model}")
                except Exception as fallback_error:
                    logger.error(f"备用模型也加载失败: {fallback_error}")
                    raise RuntimeError(f"无法加载任何嵌入模型: 主模型={model_name}, 备用模型={fallback_model}")
            
            # 初始化文本分割器
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.rag_chunk_size,
                chunk_overlap=settings.rag_chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
            )
            
            # 延迟加载文档-知识库关联关系（在首次需要时加载）
            self._mapping_loaded = False
            
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
        min_similarity: float = 0.355,
        _retry_count: int = 0  # 内部重试计数器
    ) -> List[Dict]:
        """
        检索相关文档块
        
        Args:
            query: 查询文本
            doc_ids: 限定搜索的文档ID列表
            top_k: 最大返回数量（不保证返回这么多，会根据相似度筛选）
            min_similarity: 最小相似度阈值，只返回相似度达到此阈值的结果
            _retry_count: 内部重试计数器，防止无限递归
            
        Returns:
            相关文档块列表（按相似度降序排列，数量可能少于top_k）
        """
        try:
            if not query.strip():
                logger.warning("查询字符串为空")
                return []
            
            # 限制最大重试次数
            max_retries = 2
            if _retry_count > max_retries:
                logger.warning(f"已达到最大重试次数 {max_retries}，停止搜索")
                return []
            
            retry_info = f", 重试第{_retry_count}次" if _retry_count > 0 else ""
            logger.info(f"开始RAG检索{retry_info}: query='{query}', doc_ids={doc_ids}, max_results={top_k}, min_similarity={min_similarity}")
            
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
            
            # 增加检索数量以获得更多候选结果进行筛选
            search_count = min(max(top_k * 2, 20), total_docs)
            
            # 向量检索
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=search_count,
                where=where_clause
            )
            
            logger.info(f"ChromaDB返回 {len(results['ids'][0]) if results['ids'][0] else 0} 个候选结果")
            
            # 处理结果
            relevant_chunks = []
            
            if results['ids'][0]:  # 如果有结果
                logger.info("处理检索结果...")
                for i, chunk_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i]
                    
                    # 修复相似度计算：正确处理ChromaDB的L2距离
                    # ChromaDB使用平方L2距离，对于归一化向量的正确转换如下：
                    if distance >= 0:
                        similarity = max(0.0, 1.0 - distance)
                    else:
                        similarity = 1.0  # 距离为负数时设为最高相似度
                    
                    # 确保相似度在合理范围内
                    similarity = max(0.0, min(1.0, similarity))
                    
                    logger.debug(f"候选结果 {i+1}: L2距离={distance:.4f}, 计算相似度={similarity:.4f}")
                    
                    # 只保留达到相似度阈值的结果
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
                
                # 按相似度降序排序
                relevant_chunks.sort(key=lambda x: x['similarity'], reverse=True)
                
                # 只返回top_k个最相关的结果
                if len(relevant_chunks) > top_k:
                    logger.info(f"筛选出 {len(relevant_chunks)} 个相关结果，保留前 {top_k} 个最相关的")
                    relevant_chunks = relevant_chunks[:top_k]
                
            else:
                logger.warning("ChromaDB没有返回任何结果")
            
            logger.info(f"最终检索到 {len(relevant_chunks)} 个相关文档块")
            
            # 智能重试逻辑：只在特定条件下重试，且提高阈值要求
            if not relevant_chunks and _retry_count < max_retries:
                # 获取最高相似度以判断是否需要重试
                if results['ids'][0]:
                    highest_similarity = max([
                        max(0.0, 1.0 - results['distances'][0][i])  # 修正相似度计算
                        for i in range(len(results['distances'][0]))
                    ])
                    
                    # 只有在最高相似度接近阈值时才重试，且不降得太低
                    if highest_similarity >= 0.25 and min_similarity > 0.5:
                        retry_threshold = max(0.5, min_similarity - 0.1)  # 调整重试阈值下限到0.5
                        logger.info(f"最高相似度 {highest_similarity:.3f} 接近阈值，尝试降低相似度阈值从 {min_similarity} 到 {retry_threshold}")
                        return await self.search_relevant_chunks(
                            query=query,
                            doc_ids=doc_ids,
                            top_k=top_k,
                            min_similarity=retry_threshold,
                            _retry_count=_retry_count + 1
                        )
                    elif highest_similarity < 0.25:
                        logger.info(f"最高相似度 {highest_similarity:.3f} 过低，直接返回空结果")
                        return []
            
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
        """向量化并存储文档块 - 针对PDF和OCR文档优化"""
        try:
            if not chunks:
                return
            # 对chunks进行质量优化处理
            processed_chunks = await self._optimize_chunks_for_indexing(chunks)
            
            if not processed_chunks:
                logger.warning(f"文档块质量优化后为空: {doc_id}")
                return
            
            # 准备数据
            chunk_texts = [chunk.content for chunk in processed_chunks]
            chunk_ids = [chunk.chunk_id for chunk in processed_chunks]
            metadatas = []
            
            for chunk in processed_chunks:
                metadata = chunk.metadata.copy()
                metadata['doc_id'] = doc_id
                metadatas.append(metadata)
            
            # 根据文档类型选择最佳嵌入策略
            embeddings = await self._generate_optimized_embeddings(chunk_texts, metadatas)
            
            # 存储到ChromaDB
            self.collection.add(
                ids=chunk_ids,
                embeddings=embeddings.tolist(),
                documents=chunk_texts,
                metadatas=metadatas
            )
            
            logger.info(f"成功存储 {len(processed_chunks)} 个优化后的文档块")
            
        except Exception as e:
            logger.error(f"向量化存储失败: {e}")
            raise

    async def _optimize_chunks_for_indexing(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """优化文档块以提高索引质量"""
        optimized_chunks = []
        
        for chunk in chunks:
            try:
                # 检测文档类型和质量
                doc_type = chunk.metadata.get('file_type', '').lower()
                is_pdf = chunk.metadata.get('is_pdf', False)
                is_text_pdf = chunk.metadata.get('is_text_pdf', False)
                is_ocr = chunk.metadata.get('is_ocr_processed', False)
                
                # 原始内容
                original_content = chunk.content
                
                # 应用分层优化策略
                if is_ocr or (is_pdf and not is_text_pdf):
                    # OCR扫描件：需要更严格的处理
                    processed_content = await self._process_ocr_content(original_content)
                elif is_pdf and is_text_pdf:
                    # 文本PDF：中等处理
                    processed_content = await self._process_text_pdf_content(original_content)
                else:
                    # 普通文档：基础处理
                    processed_content = await self._process_standard_content(original_content)
                
                # 质量检查
                quality_score = self._calculate_content_quality(processed_content)
                
                # 只保留质量达标的分块
                if quality_score >= 0.3:  # 质量阈值
                    # 更新分块内容和元数据
                    optimized_chunk = DocumentChunk(processed_content, chunk.metadata.copy())
                    optimized_chunk.chunk_id = chunk.chunk_id
                    
                    # 增强元数据
                    optimized_chunk.metadata.update({
                        'quality_score': quality_score,
                        'content_length_original': len(original_content),
                        'content_length_processed': len(processed_content),
                        'processing_applied': self._get_processing_type(is_ocr, is_pdf, is_text_pdf),
                        'optimization_version': '2.0'
                    })
                    
                    optimized_chunks.append(optimized_chunk)
                else:
                    logger.debug(f"跳过低质量分块: quality_score={quality_score:.3f}")
                    
            except Exception as e:
                logger.warning(f"分块优化失败，使用原始内容: {e}")
                optimized_chunks.append(chunk)
        
        logger.info(f"分块优化完成: {len(chunks)} -> {len(optimized_chunks)}")
        return optimized_chunks

    async def _process_ocr_content(self, content: str) -> str:
        """处理OCR扫描内容 - 最严格的清理"""
        # 基础清理
        text = await self._process_standard_content(content)
        
        # OCR特殊错误清理
        import re
        
        # 修正常见OCR错误
        ocr_corrections = {
            r'\b0\b': 'O',  # 数字0误识别为字母O
            r'\bl\b': 'I',  # 小写l误识别为大写I
            r'rn\b': 'm',   # rn误识别为m
            r'\s+': ' ',    # 多空格合并
        }
        
        for pattern, replacement in ocr_corrections.items():
            text = re.sub(pattern, replacement, text)
        
        # 移除可能的OCR噪音
        text = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef,.!?;:"\'()\-]', '', text)
        
        # 移除过短的行（可能是噪音）
        lines = text.split('\n')
        valid_lines = [line.strip() for line in lines if len(line.strip()) > 3]
        
        return '\n'.join(valid_lines)

    async def _process_text_pdf_content(self, content: str) -> str:
        """处理文本PDF内容 - 中等清理"""
        # 基础清理
        text = await self._process_standard_content(content)
        
        import re
        
        # PDF特殊格式清理
        # 移除页眉页脚模式
        text = re.sub(r'^第\s*\d+\s*页.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\s*/\s*\d+.*$', '', text, flags=re.MULTILINE)
        
        # 移除重复的分隔符
        text = re.sub(r'-{3,}', '---', text)
        text = re.sub(r'={3,}', '===', text)
        
        # 合并破碎的行
        text = re.sub(r'(\w)\n(\w)', r'\1 \2', text)
        
        return text

    async def _process_standard_content(self, content: str) -> str:
        """标准内容处理 - 基础清理"""
        import re
        
        # 基础文本清理
        text = content.strip()
        
        # 标准化空白字符
        text = re.sub(r'\r\n', '\n', text)  # 标准化换行符
        text = re.sub(r'\r', '\n', text)
        text = re.sub(r'\t', ' ', text)     # 制表符转空格
        text = re.sub(r'[ ]{2,}', ' ', text)  # 多空格合并
        
        # 移除控制字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', text)
        
        # 移除空行过多的情况
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

    def _calculate_content_quality(self, content: str) -> float:
        """计算内容质量分数"""
        if not content or len(content.strip()) < 10:
            return 0.0
        
        import re
        
        score = 1.0
        
        # 长度检查
        length = len(content)
        if length < 20:
            score *= 0.5
        elif length < 50:
            score *= 0.8
        
        # 字符组成检查
        total_chars = len(content)
        if total_chars > 0:
            # 中文字符比例
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
            chinese_ratio = chinese_chars / total_chars
            
            # 英文字母比例
            alpha_chars = len(re.findall(r'[a-zA-Z]', content))
            alpha_ratio = alpha_chars / total_chars
            
            # 数字比例
            digit_chars = len(re.findall(r'\d', content))
            digit_ratio = digit_chars / total_chars
            
            # 有意义字符比例
            meaningful_ratio = chinese_ratio + alpha_ratio + digit_ratio
            
            if meaningful_ratio < 0.6:
                score *= 0.6
            elif meaningful_ratio < 0.8:
                score *= 0.8
        
        # 特殊字符过多检查
        special_chars = len(re.findall(r'[^\w\s\u4e00-\u9fff]', content))
        if special_chars / total_chars > 0.3:
            score *= 0.7
        
        # 重复内容检查
        lines = content.split('\n')
        unique_lines = set(line.strip() for line in lines if line.strip())
        if len(lines) > 0 and len(unique_lines) / len(lines) < 0.7:
            score *= 0.8
        
        return max(0.0, min(1.0, score))

    def _get_processing_type(self, is_ocr: bool, is_pdf: bool, is_text_pdf: bool) -> str:
        """获取处理类型标识"""
        if is_ocr or (is_pdf and not is_text_pdf):
            return 'ocr_enhanced'
        elif is_pdf and is_text_pdf:
            return 'pdf_optimized'
        else:
            return 'standard'

    async def _generate_optimized_embeddings(self, texts: List[str], metadatas: List[Dict]) -> np.ndarray:
        """根据文档类型生成优化的嵌入向量"""
        try:
            # 检查是否有特殊类型的文档需要增强处理
            has_ocr_docs = any(meta.get('processing_applied') == 'ocr_enhanced' for meta in metadatas)
            
            if has_ocr_docs:
                # 对OCR文档使用更robust的嵌入设置
                loop = asyncio.get_event_loop()
                embeddings = await loop.run_in_executor(
                    self.executor,
                    lambda: self.embedding_model.encode(
                        texts, 
                        normalize_embeddings=True,
                        batch_size=16,  # 减小批次大小提高稳定性
                        show_progress_bar=False
                    )
                )
            else:
                # 标准嵌入处理
                embeddings = await self._generate_embeddings_batch(texts)
            
            # 确保向量质量
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1  # 避免除零
            embeddings = embeddings / norms
            
            return embeddings
            
        except Exception as e:
            logger.error(f"优化嵌入生成失败，回退到标准方法: {e}")
            return await self._generate_embeddings_batch(texts)
    
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
    
    async def _load_document_kb_mapping_from_db(self):
        """从数据库加载文档-知识库关联关系"""
        try:
            if self._mapping_loaded:
                return
                
            self.document_kb_mapping.clear()
            
            async with self.db.get_connection() as db:
                cursor = await db.execute("""
                    SELECT doc_id, knowledge_base_id 
                    FROM knowledge_base_documents
                    ORDER BY doc_id, added_at
                """)
                
                rows = await cursor.fetchall()
                
                for row in rows:
                    doc_id, kb_id = row
                    
                    if doc_id not in self.document_kb_mapping:
                        self.document_kb_mapping[doc_id] = []
                    
                    if kb_id not in self.document_kb_mapping[doc_id]:
                        self.document_kb_mapping[doc_id].append(kb_id)
                
                self._mapping_loaded = True
                logger.info(f"从数据库加载了 {len(self.document_kb_mapping)} 个文档的知识库关联关系")
                
        except Exception as e:
            logger.error(f"从数据库加载文档-知识库关联关系失败: {e}")
            # 确保至少有一个空的映射，避免后续操作失败
            self.document_kb_mapping = {}
            self._mapping_loaded = True
    
    async def _ensure_mapping_loaded(self):
        """确保映射关系已加载"""
        if not self._mapping_loaded:
            await self._load_document_kb_mapping_from_db()
    
    # 知识库管理方法 - 使用数据库存储（不绑定用户）
    async def create_knowledge_base(self, name: str, description: str = None, color: str = "#3B82F6") -> Dict:
        """创建知识库"""
        kb_id = str(uuid.uuid4())
        now = datetime.now()
        
        try:
            async with self.db.get_connection() as db:
                # 使用默认用户ID（0表示全局）
                await db.execute("""
                    INSERT INTO knowledge_bases (id, name, description, color, document_count, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (kb_id, name, description, color, 0, now, now))
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
                    WHERE id = ? 
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
                    WHERE id = ?
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
                    WHERE id = ?
                """, (kb_id,))
                
                row = await cursor.fetchone()
                kb_name = row[0] if row else "未知"
                
                # 删除知识库
                cursor = await db.execute("""
                    DELETE FROM knowledge_bases 
                    WHERE id = ?
                """, (kb_id,))
                
                await db.commit()
                
                if cursor.rowcount > 0:
                    # 从数据库删除关联关系
                    await db.execute("""
                        DELETE FROM knowledge_base_documents 
                        WHERE knowledge_base_id = ?
                    """, (kb_id,))
                    
                    # 清理内存中的文档关联关系
                    if hasattr(self, '_mapping_loaded') and self._mapping_loaded:
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
            # 确保映射关系已加载
            await self._ensure_mapping_loaded()
            
            # 验证知识库是否存在
            kb = await self.get_knowledge_base(kb_id)
            if not kb:
                logger.warning(f"知识库不存在: ID={kb_id}")
                return False
            
            # 检查文档是否存在
            existing_docs = await self.get_all_documents()
            existing_doc_ids = {doc["doc_id"] for doc in existing_docs}
            
            added_count = 0
            async with self.db.get_connection() as db:
                for doc_id in doc_ids:
                    if doc_id in existing_doc_ids:
                        # 检查是否已经存在关联关系
                        if doc_id not in self.document_kb_mapping:
                            self.document_kb_mapping[doc_id] = []
                        
                        if kb_id not in self.document_kb_mapping[doc_id]:
                            try:
                                # 插入到数据库
                                await db.execute("""
                                    INSERT INTO knowledge_base_documents (knowledge_base_id, doc_id, added_at)
                                    VALUES (?, ?, ?)
                                """, (kb_id, doc_id, datetime.now()))
                                
                                # 更新内存缓存
                                self.document_kb_mapping[doc_id].append(kb_id)
                                added_count += 1
                                
                            except Exception as e:
                                # 可能是重复插入，忽略
                                if "UNIQUE constraint failed" not in str(e):
                                    logger.warning(f"插入关联关系失败 {doc_id}->{kb_id}: {e}")
                
                # 更新知识库的文档计数
                if added_count > 0:
                    await db.execute("""
                        UPDATE knowledge_bases 
                        SET document_count = document_count + ?, updated_at = ?
                        WHERE id = ?
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
            # 确保映射关系已加载
            await self._ensure_mapping_loaded()
            
            # 验证知识库是否存在
            kb = await self.get_knowledge_base(kb_id)
            if not kb:
                logger.warning(f"知识库不存在: ID={kb_id}")
                return False
            
            removed_count = 0
            async with self.db.get_connection() as db:
                for doc_id in doc_ids:
                    if doc_id in self.document_kb_mapping and kb_id in self.document_kb_mapping[doc_id]:
                        try:
                            # 从数据库删除关联关系
                            cursor = await db.execute("""
                                DELETE FROM knowledge_base_documents 
                                WHERE knowledge_base_id = ? AND doc_id = ?
                            """, (kb_id, doc_id))
                            
                            if cursor.rowcount > 0:
                                # 更新内存缓存
                                self.document_kb_mapping[doc_id].remove(kb_id)
                                if not self.document_kb_mapping[doc_id]:
                                    del self.document_kb_mapping[doc_id]
                                removed_count += 1
                                
                        except Exception as e:
                            logger.warning(f"删除关联关系失败 {doc_id}->{kb_id}: {e}")
                
                # 更新知识库的文档计数
                if removed_count > 0:
                    await db.execute("""
                        UPDATE knowledge_bases 
                        SET document_count = GREATEST(0, document_count - ?), updated_at = ?
                        WHERE id = ?
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
        try:
            # 确保映射关系已加载
            await self._ensure_mapping_loaded()
            
            # 验证知识库是否存在
            kb = await self.get_knowledge_base(kb_id)
            if not kb:
                logger.warning(f"知识库不存在: ID={kb_id}")
                return []
            
            # 从内存缓存获取（已从数据库加载）
            return [doc_id for doc_id, kb_ids in self.document_kb_mapping.items() if kb_id in kb_ids]
            
        except Exception as e:
            logger.error(f"获取知识库文档失败: {e}")
            return []

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

# 全局RAG服务实例
rag_service = RAGService()
