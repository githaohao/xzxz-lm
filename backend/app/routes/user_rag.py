"""
用户绑定的RAG API路由
提供每个用户独立的文档管理和检索服务
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from typing import List, Optional
import logging
import os
import uuid
from datetime import datetime

from app.models.chat_history import ChatHistoryResponse
from app.services.user_rag_service import user_rag_service
from app.middleware.auth import get_current_user_id
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user/rag", tags=["user-rag"])

@router.post("/documents/upload", response_model=ChatHistoryResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    user_id: int = Depends(get_current_user_id)
):
    """用户上传文档到个人知识库"""
    try:
        logger.info(f"用户 {user_id} 上传文档: {file.filename}")
        
        # 验证文件类型
        allowed_types = ['.pdf', '.txt', '.docx', '.doc']
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型: {file_ext}。支持的类型: {allowed_types}"
            )
        
        # 保存文件
        file_id = str(uuid.uuid4())
        file_name = f"{file_id}_{file.filename}"
        file_path = os.path.join(settings.upload_dir, file_name)
        
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 添加到用户RAG系统
        doc_id = await user_rag_service.add_document(
            user_id=user_id,
            file_path=file_path,
            title=title or file.filename
        )
        
        return ChatHistoryResponse(
            code=200,
            msg="文档上传成功",
            data={
                "doc_id": doc_id,
                "filename": file.filename,
                "title": title or file.filename,
                "file_size": len(content)
            }
        )
        
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents", response_model=ChatHistoryResponse)
async def get_user_documents(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: int = Depends(get_current_user_id)
):
    """获取用户的文档列表"""
    try:
        documents = await user_rag_service.get_user_documents(user_id)
        
        # 分页处理
        start = (page - 1) * limit
        end = start + limit
        paginated_docs = documents[start:end]
        
        return ChatHistoryResponse(
            code=200,
            msg="获取文档列表成功",
            data=paginated_docs,
            pagination={
                "page": page,
                "limit": limit,
                "total": len(documents),
                "pages": (len(documents) + limit - 1) // limit
            }
        )
        
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=ChatHistoryResponse)
async def search_user_documents(
    query: str = Form(...),
    top_k: int = Form(5, ge=1, le=20),
    user_id: int = Depends(get_current_user_id)
):
    """在用户知识库中搜索文档"""
    try:
        logger.info(f"用户 {user_id} 搜索: {query}")
        
        search_results = await user_rag_service.search_documents(
            user_id=user_id,
            query=query,
            top_k=top_k
        )
        
        return ChatHistoryResponse(
            code=200,
            msg="搜索完成",
            data={
                "query": query,
                "results": search_results,
                "total_found": len(search_results)
            }
        )
        
    except Exception as e:
        logger.error(f"文档搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{doc_id}", response_model=ChatHistoryResponse)
async def delete_user_document(
    doc_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """删除用户的文档"""
    try:
        logger.info(f"用户 {user_id} 删除文档: {doc_id}")
        
        success = await user_rag_service.delete_document(user_id, doc_id)
        
        if success:
            return ChatHistoryResponse(
                code=200,
                msg="文档删除成功"
            )
        else:
            raise HTTPException(status_code=404, detail="文档不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{doc_id}/chunks", response_model=ChatHistoryResponse)
async def get_document_chunks(
    doc_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """获取文档的分块内容"""
    try:
        # 首先验证文档是否属于该用户
        user_docs = await user_rag_service.get_user_documents(user_id)
        doc_exists = any(doc['doc_id'] == doc_id for doc in user_docs)
        
        if not doc_exists:
            raise HTTPException(status_code=404, detail="文档不存在或无权限访问")
        
        collection = await user_rag_service.get_user_collection(user_id)
        
        # 获取文档的所有分块
        results = collection.get(where={"doc_id": doc_id})
        
        chunks = []
        if results['ids']:
            for i, chunk_id in enumerate(results['ids']):
                chunks.append({
                    'chunk_id': chunk_id,
                    'content': results['documents'][i],
                    'metadata': results['metadatas'][i]
                })
            
            # 按chunk_index排序
            chunks.sort(key=lambda x: x['metadata'].get('chunk_index', 0))
        
        return ChatHistoryResponse(
            code=200,
            msg="获取文档分块成功",
            data={
                "doc_id": doc_id,
                "chunks": chunks,
                "total_chunks": len(chunks)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档分块失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=ChatHistoryResponse)
async def get_user_rag_stats(
    user_id: int = Depends(get_current_user_id)
):
    """获取用户RAG统计信息"""
    try:
        documents = await user_rag_service.get_user_documents(user_id)
        
        total_docs = len(documents)
        total_chunks = sum(doc.get('chunk_count', 0) for doc in documents)
        
        # 按文件类型统计
        type_stats = {}
        for doc in documents:
            file_type = doc.get('file_type', 'unknown')
            type_stats[file_type] = type_stats.get(file_type, 0) + 1
        
        return ChatHistoryResponse(
            code=200,
            msg="获取统计信息成功",
            data={
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "document_types": type_stats,
                "avg_chunks_per_doc": total_chunks / total_docs if total_docs > 0 else 0
            }
        )
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=ChatHistoryResponse)
async def user_rag_health_check():
    """用户RAG服务健康检查"""
    try:
        # 检查服务是否已初始化
        if not user_rag_service._initialized:
            await user_rag_service.initialize()
        
        return ChatHistoryResponse(
            code=200,
            msg="用户RAG服务运行正常",
            data={
                "status": "healthy",
                "service": "User RAG Service",
                "initialized": user_rag_service._initialized
            }
        )
        
    except Exception as e:
        logger.error(f"用户RAG健康检查失败: {e}")
        return ChatHistoryResponse(
            code=500,
            msg="用户RAG服务异常",
            data={
                "status": "unhealthy",
                "error": str(e)
            }
        ) 