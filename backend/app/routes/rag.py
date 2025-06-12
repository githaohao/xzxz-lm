"""
用户绑定的RAG API路由
提供每个用户独立的文档管理和检索服务
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from typing import List, Optional
import logging
import time

from app.models.schemas import ( 
    RAGSearchRequest, 
    RAGSearchResponse, 
    DocumentInfo
)
from app.models.chat_history import ChatHistoryResponse

from app.services.rag_service import rag_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["rag"])

@router.post("/process")
async def process_document_for_rag(
    content: str = Form(...),
    filename: str = Form(...),
    file_type: str = Form(...)
):
    """处理文档进行RAG索引"""
    try:
        start_time = time.time()
        
        # 处理文档并生成doc_id
        doc_id = await rag_service.process_document(
            content=content,
            filename=filename,
            file_type=file_type
        )
        
        processing_time = time.time() - start_time
        
        return {
            "doc_id": doc_id,
            "message": "文档处理完成",
            "processing_time": processing_time
        }
        
    except Exception as e:
        logger.error(f"RAG文档处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")

@router.get("/documents")
async def get_all_documents():
    """获取所有RAG文档列表"""
    try:
        start_time = time.time()
        
        # 获取文档列表
        documents = await rag_service.get_all_documents()
        
        processing_time = time.time() - start_time
        
        return {
            "documents": documents,
            "total_count": len(documents),
            "processing_time": processing_time
        }
        
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")

@router.post("/search", response_model=RAGSearchResponse)
async def search_documents(request: RAGSearchRequest):
    """RAG文档检索接口"""
    try:
        start_time = time.time()
        
        # 执行检索
        chunks = await rag_service.search_relevant_chunks(
            query=request.query,
            doc_ids=request.doc_ids,
            top_k=request.top_k,
            min_similarity=request.min_similarity
        )
        
        search_time = time.time() - start_time
        
        return RAGSearchResponse(
            chunks=chunks,
            total_found=len(chunks),
            search_time=search_time
        )
        
    except Exception as e:
        logger.error(f"RAG检索失败: {e}")
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")

@router.get("/documents/{doc_id}", response_model=DocumentInfo)
async def get_document_info(doc_id: str):
    """获取文档信息"""
    try:
        doc_info = await rag_service.get_document_info(doc_id)
        
        if not doc_info:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return DocumentInfo(**doc_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档信息失败: {str(e)}")

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档及其索引"""
    try:
        success = await rag_service.delete_document(doc_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return {"message": "文档删除成功", "doc_id": doc_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")


@router.get("/documents/{doc_id}/chunks", response_model=ChatHistoryResponse)
async def get_document_chunks(doc_id: str):
    """获取文档的分块内容"""
    try:
        start_time = time.time()
        
        # 获取文档分块数据
        chunks_data = await rag_service.get_document_chunks(doc_id)
        
        if not chunks_data:
            raise HTTPException(status_code=404, detail="文档不存在或没有分块数据")
        
        processing_time = time.time() - start_time
        
        return ChatHistoryResponse(
            code=200,
            msg="获取文档分块成功",
            data={
                "doc_id": doc_id,
                "chunks": chunks_data,
                "total_chunks": len(chunks_data),
                "processing_time": processing_time
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档分块失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档分块失败: {str(e)}")