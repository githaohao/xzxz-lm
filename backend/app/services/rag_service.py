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
import json
import httpx

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
        # 文档分析结果缓存，避免重复分析
        self.analysis_cache = {}  # content_hash -> analysis_result
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

    async def analyze_document_for_archive(
        self, 
        file_content: bytes, 
        filename: str, 
        file_type: str,
        analysis_prompt: str,
        custom_analysis: bool = False
    ) -> Dict:
        """
        分析文档内容并保存到向量数据库，预览归档建议
        
        Args:
            file_content: 文件内容（字节）
            filename: 文件名
            file_type: 文件类型
            analysis_prompt: 分析提示词
            custom_analysis: 是否使用自定义分析
            
        Returns:
            分析结果信息（包含实际的docId）
        """
        try:
            # 提取文档内容
            text_content = await self._extract_text_from_file(file_content, filename, file_type)
            
            # 🚀 优化：在分析阶段就保存文档到向量数据库
            doc_id = await self.process_document(text_content, filename, file_type)
            logger.info(f"文档已保存到向量数据库: {filename} (doc_id: {doc_id})")
            
            # 使用AI分析文档内容并匹配知识库
            analysis_result = await self._analyze_document_content(
                content=text_content,
                filename=filename,
                analysis_prompt=analysis_prompt,
                custom_analysis=custom_analysis
            )
            
            knowledge_base_name = analysis_result['knowledge_base_name']
            is_new_kb = analysis_result['is_new_knowledge_base']
            reason = analysis_result.get('reason', '')
            
            # 如果不是新建知识库，检查现有知识库是否存在
            kb_id = None
            if not is_new_kb:
                all_kbs = await self.get_all_knowledge_bases()
                for kb in all_kbs:
                    if kb['name'] == knowledge_base_name:
                        kb_id = kb['id']
                        break
                
                # 如果没找到匹配的知识库，标记为新建
                if not kb_id:
                    is_new_kb = True
            
            result = {
                "fileName": filename,
                "knowledgeBaseName": knowledge_base_name,
                "isNewKnowledgeBase": is_new_kb,
                "reason": reason,
                "knowledgeBaseId": kb_id,
                "documentType": analysis_result.get('document_type', '未知'),
                "textContent": text_content[:500] + "..." if len(text_content) > 500 else text_content,  # 预览内容
                "docId": doc_id,  # ✨ 新增：返回文档ID
                "analysisTime": datetime.now().timestamp()
            }
            
            logger.info(f"文档分析和保存完成: {filename} -> {knowledge_base_name} ({'新建' if is_new_kb else '现有'}), doc_id: {doc_id}")
            return result
            
        except Exception as e:
            logger.error(f"文档分析失败 {filename}: {e}")
            raise

    async def confirm_archive_document(
        self,
        file_content: str,  # 已弃用，保留用于兼容性
        filename: str,
        file_type: str,
        analysis_result: Dict
    ) -> Dict:
        """
        确认归档文档，仅执行文档与知识库的关联操作
        （文档在analyze阶段已保存到向量数据库）
        
        Args:
            file_content: 已弃用，文档已在分析阶段保存
            filename: 文件名
            file_type: 文件类型  
            analysis_result: 分析结果（包含doc_id）
            
        Returns:
            归档结果信息
        """
        try:
            # 🚀 优化：从分析结果直接获取doc_id，不再重复处理文档
            doc_id = analysis_result.get('docId')
            if not doc_id:
                raise ValueError("分析结果中缺少文档ID，请重新分析文档")
            
            knowledge_base_name = analysis_result['knowledgeBaseName']
            is_new_kb = analysis_result['isNewKnowledgeBase']
            reason = analysis_result.get('reason', '')
            kb_id = analysis_result.get('knowledgeBaseId')
            
            # 获取或创建知识库
            if is_new_kb or not kb_id:
                kb = await self.create_knowledge_base(
                    name=knowledge_base_name,
                    description=f"由AI智能分析创建的知识库，用于存储{analysis_result.get('documentType', '相关')}类型的文档",
                    color=self._get_random_color()
                )
                kb_id = kb['id']
                logger.info(f"创建新知识库: {knowledge_base_name} (ID: {kb_id})")
            else:
                # 验证知识库是否仍然存在
                try:
                    all_kbs = await self.get_all_knowledge_bases()
                    kb_exists = any(kb['id'] == kb_id for kb in all_kbs)
                    if not kb_exists:
                        # 知识库不存在，创建新的
                        kb = await self.create_knowledge_base(
                            name=knowledge_base_name,
                            description=f"智能归档创建的知识库",
                            color=self._get_random_color()
                        )
                        kb_id = kb['id']
                        is_new_kb = True
                        logger.info(f"原知识库不存在，创建新知识库: {knowledge_base_name}")
                except Exception as e:
                    logger.warning(f"验证知识库时出错: {e}，创建新知识库")
                    kb = await self.create_knowledge_base(
                        name=knowledge_base_name,
                        description=f"智能归档创建的知识库",
                        color=self._get_random_color()
                    )
                    kb_id = kb['id']
                    is_new_kb = True
            
            # ⚡ 核心：将已保存的文档关联到知识库
            await self.add_documents_to_knowledge_base(kb_id, [doc_id])
            
            result = {
                "fileName": filename,
                "knowledgeBaseName": knowledge_base_name,
                "isNewKnowledgeBase": is_new_kb,
                "reason": reason,
                "docId": doc_id,
                "knowledgeBaseId": kb_id
            }
            
            logger.info(f"确认归档完成（仅关联）: {filename} -> {knowledge_base_name} ({'新建' if is_new_kb else '现有'}), doc_id: {doc_id}")
            return result
            
        except Exception as e:
            logger.error(f"确认归档失败 {filename}: {e}")
            raise

    
    async def _extract_text_from_file(self, file_content: bytes, filename: str, file_type: str) -> str:
        """从文件中提取文本内容"""
        try:
            from app.services.file_extraction_service import file_extraction_service
            
            # 使用统一的文件提取服务
            text, metadata = await file_extraction_service.extract_text_from_file(
                file_content, filename, file_type
            )
            
            # 记录提取元数据到日志
            extraction_method = metadata.get('extraction_method', 'unknown')
            processing_time = metadata.get('extraction_time', 0)
            confidence = metadata.get('confidence', None)
            
            log_msg = f"文件提取完成: {filename}, 方法: {extraction_method}, 耗时: {processing_time:.2f}秒"
            if confidence is not None:
                log_msg += f", 置信度: {confidence:.2f}"
            
            logger.info(log_msg)
            
            return text
                
        except Exception as e:
            logger.error(f"文本提取失败 {filename}: {e}")
            return f"文档: {filename}\n内容提取失败: {str(e)}"
    
    async def _analyze_document_content(
        self, 
        content: str, 
        filename: str, 
        analysis_prompt: str,
        custom_analysis: bool = False
    ) -> Dict:
        """
        使用真正的LLM分析文档内容并决定归档位置
        
        对于特大文档采用智能处理策略：
        1. 小文档(<5000字符)：直接全文分析
        2. 中等文档(5000-20000字符)：提取关键段落分析
        3. 大文档(20000-100000字符)：分段摘要分析
        4. 特大文档(>100000字符)：智能采样+关键信息提取
        """
        try:
            # 检查缓存
            content_hash = hashlib.md5((content + filename + analysis_prompt).encode('utf-8')).hexdigest()
            if content_hash in self.analysis_cache:
                logger.info(f"使用缓存的分析结果: {filename}")
                return self.analysis_cache[content_hash]
            
            content_length = len(content)
            logger.info(f"开始分析文档: {filename}, 大小: {content_length} 字符")
            
            # 根据文档大小选择处理策略
            if content_length < 5000:
                # 小文档：直接全文分析
                analysis_content = content
                processing_strategy = "direct_analysis"
            elif content_length < 20000:
                # 中等文档：提取关键段落
                analysis_content = await self._extract_key_paragraphs(content, filename)
                processing_strategy = "key_paragraphs"
            elif content_length < 100000:
                # 大文档：分段摘要
                analysis_content = await self._create_document_summary(content, filename)
                processing_strategy = "segment_summary"
            else:
                # 特大文档：智能采样
                analysis_content = await self._intelligent_sampling(content, filename)
                processing_strategy = "intelligent_sampling"
            
            logger.info(f"文档处理策略: {processing_strategy}, 分析内容长度: {len(analysis_content)}")
            
            # 调用LLM进行分析
            analysis_result = await self._call_llm_for_analysis(
                content=analysis_content,
                filename=filename,
                analysis_prompt=analysis_prompt,
                custom_analysis=custom_analysis,
                processing_strategy=processing_strategy
            )
            
            # 缓存结果
            self.analysis_cache[content_hash] = analysis_result
            
            # 限制缓存大小
            if len(self.analysis_cache) > 100:
                # 移除最旧的缓存项
                oldest_key = next(iter(self.analysis_cache))
                del self.analysis_cache[oldest_key]
            
            logger.info(f"文档分析完成: {filename} -> {analysis_result['knowledge_base_name']}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"文档分析失败: {e}")
    
    async def _extract_key_paragraphs(self, content: str, filename: str) -> str:
        """提取关键段落（用于中等文档）"""
        try:
            lines = content.split('\n')
            
            # 获取文档开头（前20%或最多500行）
            start_lines = int(min(len(lines) * 0.2, 500))
            beginning = '\n'.join(lines[:start_lines])
            
            # 获取文档结尾（后10%或最多200行）
            end_lines = int(min(len(lines) * 0.1, 200))
            ending = '\n'.join(lines[-end_lines:]) if end_lines > 0 else ""
            
            # 查找包含关键词的段落
            keywords = ['摘要', '总结', '概述', '简介', '目录', 'abstract', 'summary', 'introduction']
            key_paragraphs = []
            
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in keywords):
                    # 包含关键词的段落及其周围内容
                    start_idx = max(0, i - 2)
                    end_idx = min(len(lines), i + 5)
                    key_paragraphs.append('\n'.join(lines[start_idx:end_idx]))
            
            # 组合内容
            extracted_content = f"文档开头：\n{beginning}\n\n"
            
            if key_paragraphs:
                extracted_content += f"关键段落：\n" + '\n\n'.join(key_paragraphs) + "\n\n"
            
            if ending:
                extracted_content += f"文档结尾：\n{ending}"
            
            # 如果提取的内容太长，截断
            if len(extracted_content) > 8000:
                extracted_content = extracted_content[:8000] + "...\n[内容已截断]"
            
            return extracted_content
            
        except Exception as e:
            logger.warning(f"提取关键段落失败: {e}")
            return content[:5000] + "...\n[提取失败，使用开头内容]"
    
    async def _create_document_summary(self, content: str, filename: str) -> str:
        """创建文档摘要（用于大文档）"""
        try:
            # 将文档分成多个段落
            paragraphs = content.split('\n\n')
            
            # 每段最多1000字符
            segments = []
            current_segment = ""
            
            for paragraph in paragraphs:
                if len(current_segment) + len(paragraph) < 1000:
                    current_segment += paragraph + '\n\n'
                else:
                    if current_segment:
                        segments.append(current_segment.strip())
                    current_segment = paragraph + '\n\n'
            
            if current_segment:
                segments.append(current_segment.strip())
            
            # 选择关键段落进行摘要
            key_segments = []
            
            # 总是包含开头和结尾
            if segments:
                key_segments.append(segments[0])  # 开头
                if len(segments) > 1:
                    key_segments.append(segments[-1])  # 结尾
            
            # 添加中间的关键段落
            for segment in segments[1:-1]:
                segment_lower = segment.lower()
                # 查找包含重要信息的段落
                if any(keyword in segment_lower for keyword in [
                    '摘要', '总结', '结论', '概述', '目的', '目标', '方法', '结果',
                    'abstract', 'summary', 'conclusion', 'objective', 'purpose', 'method', 'result'
                ]):
                    key_segments.append(segment)
                    if len(key_segments) >= 5:  # 限制段落数量
                        break
            
            # 如果关键段落不够，随机选择一些段落
            if len(key_segments) < 3 and len(segments) > 2:
                import random
                remaining_segments = [s for s in segments[1:-1] if s not in key_segments]
                additional_count = min(3 - len(key_segments), len(remaining_segments))
                key_segments.extend(random.sample(remaining_segments, additional_count))
            
            # 组合摘要
            summary = f"文档摘要 ({len(segments)}个段落中的{len(key_segments)}个关键段落)：\n\n"
            summary += '\n\n---段落分隔---\n\n'.join(key_segments)
            
            # 限制总长度
            if len(summary) > 6000:
                summary = summary[:6000] + "...\n[摘要已截断]"
            
            return summary
            
        except Exception as e:
            logger.warning(f"创建文档摘要失败: {e}")
            return content[:3000] + "...\n[摘要失败，使用开头内容]"
    
    async def _intelligent_sampling(self, content: str, filename: str) -> str:
        """智能采样（用于特大文档）"""
        try:
            total_length = len(content)
            
            # 提取开头、中间、结尾的样本
            start_sample = content[:2000]  # 开头2000字符
            end_sample = content[-1000:]   # 结尾1000字符
            
            # 中间采样：每隔一定间距采样
            middle_samples = []
            sample_interval = max(1000, total_length // 20)  # 最多采样20个片段
            
            for i in range(2000, total_length - 1000, sample_interval):
                sample = content[i:i+500]  # 每次采样500字符
                middle_samples.append(sample)
                if len(middle_samples) >= 10:  # 最多10个中间样本
                    break
            
            # 查找结构化信息（标题、目录等）
            lines = content.split('\n')
            structured_info = []
            
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and (
                    line_stripped.startswith('#') or  # Markdown标题
                    line_stripped.endswith(':') or   # 冒号结尾（可能是标题）
                    len(line_stripped) < 100 and (   # 短行且包含关键词
                        any(keyword in line_stripped.lower() for keyword in [
                            '第', '章', '节', '部分', 'chapter', 'section', 'part'
                        ])
                    )
                ):
                    structured_info.append(line_stripped)
                    if len(structured_info) >= 20:  # 最多20个结构化信息
                        break
            
            # 组合采样结果
            sampled_content = f"超大文档智能采样 (总长度: {total_length} 字符)：\n\n"
            sampled_content += f"文档开头：\n{start_sample}\n\n"
            
            if structured_info:
                sampled_content += f"文档结构：\n" + '\n'.join(structured_info) + "\n\n"
            
            if middle_samples:
                sampled_content += f"中间采样：\n" + '\n\n---采样分隔---\n\n'.join(middle_samples) + "\n\n"
            
            sampled_content += f"文档结尾：\n{end_sample}"
            
            # 限制总长度
            if len(sampled_content) > 8000:
                sampled_content = sampled_content[:8000] + "...\n[采样已截断]"
            
            return sampled_content
            
        except Exception as e:
            logger.warning(f"智能采样失败: {e}")
            return content[:3000] + "...\n[采样失败，使用开头内容]"
    
    async def _call_llm_for_analysis(
        self,
        content: str,
        filename: str,
        analysis_prompt: str,
        custom_analysis: bool,
        processing_strategy: str
    ) -> Dict:
        """调用LLM进行文档内容分析"""
        try:
            # 构建系统提示词
            system_prompt = """你是一个专业的文档分析专家，负责分析文档内容并决定最合适的知识库归档位置。

            你的任务是：
                1. 分析文档的主要内容和类型
                2. 从以下预设知识库中选择最合适的归档位置：
                - 个人简历：简历、CV、个人资料、求职相关
                - 合同文档：合同、协议、法律文件
                - 教育培训：培训材料、课程、教育内容
                - 技术文档：API文档、技术规范、开发资料
                - 商务文档：商业计划、市场分析、商务资料
                - 操作手册：用户手册、操作指南、说明书
                - 医疗健康：医疗报告、健康资料、医学文献
                - 政策法规：政策文件、法规条例、规章制度

                3. 如果文档不适合任何预设知识库，建议创建新的知识库

                请返回JSON格式的分析结果：
                {
                    "knowledge_base_name": "知识库名称",
                    "is_new_knowledge_base": false,
                    "document_type": "文档类型",
                    "reason": "选择理由",
                    "confidence": 0.85
                }"""

            # 构建用户提示词
            user_prompt = f"""请分析以下文档并决定最合适的知识库归档位置：

                文件名：{filename}
                用户提示：{analysis_prompt}
                处理策略：{processing_strategy}

                文档内容：
                {content}

                请仔细分析文档的主要内容、类型和用途，然后选择最合适的知识库进行归档。
                如果用户提供了特定的分类建议，请优先考虑。"""

            # 调用LLM
            response = await self._make_llm_request(system_prompt, user_prompt)
            
            # 解析LLM响应
            analysis_result = await self._parse_llm_response(response)
            
            # 验证和修正结果
            return await self._validate_analysis_result(analysis_result, filename)
            
        except Exception as e:
            logger.error(f"LLM分析调用失败: {e}")
    
    async def _make_llm_request(self, system_prompt: str, user_prompt: str) -> str:
        """向LM Studio发送请求"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": settings.lm_studio_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,  # 较低的温度以获得更一致的分析结果
                    "max_tokens": 1000,
                    "stream": False
                }
                
                response = await client.post(
                    f"{settings.lm_studio_base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {settings.lm_studio_api_key}"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"LLM请求失败: {response.status_code} - {response.text}")
                    raise Exception(f"LLM请求失败: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"LLM请求异常: {e}")
            raise
    
    async def _parse_llm_response(self, response: str) -> Dict:
        """解析LLM响应，提取JSON结果"""
        try:
            # 尝试直接解析JSON
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
            
            # 如果直接解析失败，尝试提取JSON部分
            import re
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # 如果仍然失败，从文本中提取信息
            knowledge_base_match = re.search(r'knowledge_base_name["\s]*:["\s]*([^"]*)', response)
            is_new_match = re.search(r'is_new_knowledge_base["\s]*:["\s]*(true|false)', response)
            doc_type_match = re.search(r'document_type["\s]*:["\s]*([^"]*)', response)
            reason_match = re.search(r'reason["\s]*:["\s]*([^"]*)', response)
            
            return {
                "knowledge_base_name": knowledge_base_match.group(1) if knowledge_base_match else "通用文档",
                "is_new_knowledge_base": is_new_match.group(1).lower() == 'true' if is_new_match else False,
                "document_type": doc_type_match.group(1) if doc_type_match else "未知",
                "reason": reason_match.group(1) if reason_match else "AI分析结果",
                "confidence": 0.5
            }
            
        except Exception as e:
            logger.warning(f"解析LLM响应失败: {e}")
            return {
                "knowledge_base_name": "通用文档",
                "is_new_knowledge_base": False,
                "document_type": "未知",
                "reason": "解析失败，使用默认分类",
                "confidence": 0.3
            }
    
    async def _validate_analysis_result(self, result: Dict, filename: str) -> Dict:
        """验证和修正分析结果"""
        try:
            # 确保必要字段存在
            if "knowledge_base_name" not in result:
                result["knowledge_base_name"] = "通用文档"
            
            if "is_new_knowledge_base" not in result:
                result["is_new_knowledge_base"] = False
            
            if "document_type" not in result:
                result["document_type"] = "未知"
            
            if "reason" not in result:
                result["reason"] = "AI智能分析结果"
            
            # 检查知识库名称是否在预设列表中
            preset_knowledge_bases = {
                "个人简历", "合同文档", "教育培训", "技术文档", 
                "商务文档", "操作手册", "医疗健康", "政策法规"
            }
            
            kb_name = result["knowledge_base_name"]
            if kb_name not in preset_knowledge_bases:
                # 如果不在预设列表中，标记为新知识库
                result["is_new_knowledge_base"] = True
                
                # 但如果名称很相似，修正为预设名称
                for preset in preset_knowledge_bases:
                    if any(word in kb_name for word in preset.split()) or any(word in preset for word in kb_name.split()):
                        result["knowledge_base_name"] = preset
                        result["is_new_knowledge_base"] = False
                        result["reason"] += f"（已修正为预设知识库：{preset}）"
                        break
            
            return result
            
        except Exception as e:
            logger.warning(f"验证分析结果失败: {e}")
            return {
                "knowledge_base_name": "通用文档",
                "is_new_knowledge_base": False,
                "document_type": "未知",
                "reason": "验证失败，使用默认分类",
                "confidence": 0.2
            }
    
    def _extract_document_type(self, filename: str, content: str) -> str:
        """从文件名和内容中提取文档类型"""
        filename_lower = filename.lower()
        
        # 从文件名推断类型
        if 'report' in filename_lower or '报告' in filename_lower:
            return '报告'
        elif 'plan' in filename_lower or '计划' in filename_lower:
            return '计划'
        elif 'spec' in filename_lower or '规范' in filename_lower:
            return '规范'
        elif 'note' in filename_lower or '笔记' in filename_lower:
            return '笔记'
        elif 'summary' in filename_lower or '总结' in filename_lower:
            return '总结'
        else:
            return '通用'
    
    def _get_random_color(self) -> str:
        """获取随机颜色"""
        colors = [
            "#3B82F6", "#10B981", "#F59E0B", "#EF4444", 
            "#8B5CF6", "#06B6D4", "#84CC16", "#F97316",
            "#EC4899", "#6366F1"
        ]
        import random
        return random.choice(colors)

    async def analyze_existing_document_for_archive(
        self, 
        doc_id: str,
        filename: str, 
        file_type: str,
        text_content: str,
        analysis_prompt: str,
        custom_analysis: bool = False
    ) -> Dict:
        """
        分析已有文档进行智能归档建议
        
        Args:
            doc_id: 文档ID
            filename: 文件名
            file_type: 文件类型
            text_content: 文档内容
            analysis_prompt: 分析提示词
            custom_analysis: 是否使用自定义分析
            
        Returns:
            分析结果信息
        """
        try:
            # 使用AI分析文档内容并匹配知识库
            analysis_result = await self._analyze_document_content(
                content=text_content,
                filename=filename,
                analysis_prompt=analysis_prompt,
                custom_analysis=custom_analysis
            )
            
            knowledge_base_name = analysis_result['knowledge_base_name']
            is_new_kb = analysis_result['is_new_knowledge_base']
            reason = analysis_result.get('reason', '')
            
            # 如果不是新建知识库，检查现有知识库是否存在
            kb_id = None
            if not is_new_kb:
                all_kbs = await self.get_all_knowledge_bases()
                for kb in all_kbs:
                    if kb['name'] == knowledge_base_name:
                        kb_id = kb['id']
                        break
                
                # 如果没找到匹配的知识库，标记为新建
                if not kb_id:
                    is_new_kb = True
            
            result = {
                "filename": filename,
                "knowledgeBaseName": knowledge_base_name,
                "isNewKnowledgeBase": is_new_kb,
                "reason": reason,
                "knowledgeBaseId": kb_id,
                "documentType": analysis_result.get('document_type', '未知'),
                "textContent": text_content[:500] + "..." if len(text_content) > 500 else text_content,  # 预览内容
                "docId": doc_id,  # 文档ID（已存在）
                "analysisTime": datetime.now().timestamp()
            }
            
            logger.info(f"已有文档分析完成: {filename} -> {knowledge_base_name} ({'新建' if is_new_kb else '现有'}), doc_id: {doc_id}")
            return result
            
        except Exception as e:
            logger.error(f"已有文档分析失败 {filename}: {e}")
            raise

    async def confirm_existing_document_archive(
        self,
        doc_id: str,
        analysis_result: Dict
    ) -> Dict:
        """
        确认已有文档的归档操作，执行文档与知识库的关联
        
        Args:
            doc_id: 文档ID
            analysis_result: 分析结果
            
        Returns:
            归档结果信息
        """
        try:
            knowledge_base_name = analysis_result['knowledgeBaseName']
            is_new_kb = analysis_result['isNewKnowledgeBase']
            reason = analysis_result.get('reason', '')
            kb_id = analysis_result.get('knowledgeBaseId')
            filename = analysis_result.get('filename', '未知文档')
            
            # 获取或创建知识库
            if is_new_kb or not kb_id:
                kb = await self.create_knowledge_base(
                    name=knowledge_base_name,
                    description=f"由AI智能分析创建的知识库，用于存储{analysis_result.get('documentType', '相关')}类型的文档",
                    color=self._get_random_color()
                )
                kb_id = kb['id']
                logger.info(f"创建新知识库: {knowledge_base_name} (ID: {kb_id})")
            else:
                # 验证知识库是否仍然存在
                try:
                    all_kbs = await self.get_all_knowledge_bases()
                    kb_exists = any(kb['id'] == kb_id for kb in all_kbs)
                    if not kb_exists:
                        # 知识库不存在，创建新的
                        kb = await self.create_knowledge_base(
                            name=knowledge_base_name,
                            description=f"智能归档创建的知识库",
                            color=self._get_random_color()
                        )
                        kb_id = kb['id']
                        is_new_kb = True
                        logger.info(f"原知识库不存在，创建新知识库: {knowledge_base_name}")
                except Exception as e:
                    logger.warning(f"验证知识库时出错: {e}，创建新知识库")
                    kb = await self.create_knowledge_base(
                        name=knowledge_base_name,
                        description=f"智能归档创建的知识库",
                        color=self._get_random_color()
                    )
                    kb_id = kb['id']
                    is_new_kb = True
            
            # 将文档关联到知识库
            await self.add_documents_to_knowledge_base(kb_id, [doc_id])
            
            result = {
                "filename": filename,
                "knowledgeBaseName": knowledge_base_name,
                "isNewKnowledgeBase": is_new_kb,
                "reason": reason,
                "docId": doc_id,
                "knowledgeBaseId": kb_id
            }
            
            logger.info(f"已有文档归档完成: {filename} -> {knowledge_base_name} ({'新建' if is_new_kb else '现有'}), doc_id: {doc_id}")
            return result
            
        except Exception as e:
            logger.error(f"已有文档归档失败: {e}")
            raise

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

# 全局RAG服务实例
rag_service = RAGService()
