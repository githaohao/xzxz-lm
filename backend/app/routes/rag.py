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
    DocumentInfo,
    KnowledgeBaseRequest,
    KnowledgeBaseResponse,
    KnowledgeBaseDocumentRequest,
    DocumentWithKnowledgeBases,
    KnowledgeBaseListResponse
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

# 知识库管理接口
@router.post("/knowledge-bases")
async def create_knowledge_base(request: KnowledgeBaseRequest):
    """创建知识库"""
    try:
        start_time = time.time()
        
        kb = await rag_service.create_knowledge_base(
            name=request.name,
            description=request.description,
            color=request.color
        )
        
        processing_time = time.time() - start_time
        
        return ChatHistoryResponse(
            code=200,
            msg="创建知识库成功",
            data={
                "knowledge_base": kb,
                "processing_time": processing_time
            }
        )
        
    except Exception as e:
        logger.error(f"创建知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建知识库失败: {str(e)}")

@router.get("/knowledge-bases")
async def get_knowledge_bases():
    """获取所有知识库"""
    try:
        start_time = time.time()
        
        knowledge_bases = await rag_service.get_all_knowledge_bases()
        
        processing_time = time.time() - start_time
        
        return ChatHistoryResponse(
            code=200,
            msg="获取知识库列表成功",
            data={
                "knowledge_bases": knowledge_bases,
                "total_count": len(knowledge_bases),
                "processing_time": processing_time
            }
        )
        
    except Exception as e:
        logger.error(f"获取知识库列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库列表失败: {str(e)}")

@router.get("/knowledge-bases/{kb_id}")
async def get_knowledge_base(kb_id: str):
    """获取单个知识库详情"""
    try:
        kb = await rag_service.get_knowledge_base(kb_id)
        
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        return ChatHistoryResponse(
            code=200,
            msg="获取知识库详情成功",
            data={
                "knowledge_base": kb
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识库详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库详情失败: {str(e)}")

@router.put("/knowledge-bases/{kb_id}")
async def update_knowledge_base(kb_id: str, request: KnowledgeBaseRequest):
    """更新知识库"""
    try:
        success = await rag_service.update_knowledge_base(
            kb_id=kb_id,
            name=request.name,
            description=request.description,
            color=request.color
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        return ChatHistoryResponse(
            code=200,
            msg="更新知识库成功",
            data={
                "kb_id": kb_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新知识库失败: {str(e)}")

@router.delete("/knowledge-bases/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    """删除知识库"""
    try:
        success = await rag_service.delete_knowledge_base(kb_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        return ChatHistoryResponse(
            code=200,
            msg="删除知识库成功",
            data={
                "kb_id": kb_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除知识库失败: {str(e)}")

@router.post("/knowledge-bases/{kb_id}/documents")
async def add_documents_to_knowledge_base(kb_id: str, request: KnowledgeBaseDocumentRequest):
    """向知识库添加文档"""
    try:
        success = await rag_service.add_documents_to_knowledge_base(
            kb_id=kb_id,
            doc_ids=request.document_ids
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        return ChatHistoryResponse(
            code=200,
            msg="添加文档到知识库成功",
            data={
                "kb_id": kb_id,
                "added_count": len(request.document_ids)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加文档到知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加文档到知识库失败: {str(e)}")

@router.delete("/knowledge-bases/{kb_id}/documents")
async def remove_documents_from_knowledge_base(kb_id: str, request: KnowledgeBaseDocumentRequest):
    """从知识库移除文档"""
    try:
        success = await rag_service.remove_documents_from_knowledge_base(
            kb_id=kb_id,
            doc_ids=request.document_ids
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        return ChatHistoryResponse(
            code=200,
            msg="从知识库移除文档成功",
            data={
                "kb_id": kb_id,
                "removed_count": len(request.document_ids)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从知识库移除文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"从知识库移除文档失败: {str(e)}")

@router.post("/knowledge-bases/{kb_id}/documents/remove")
async def remove_documents_from_knowledge_base_post(kb_id: str, request: KnowledgeBaseDocumentRequest):
    """从知识库移除文档 (POST方式)"""
    try:
        success = await rag_service.remove_documents_from_knowledge_base(
            kb_id=kb_id,
            doc_ids=request.document_ids
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        return ChatHistoryResponse(
            code=200,
            msg="从知识库移除文档成功",
            data={
                "kb_id": kb_id,
                "removed_count": len(request.document_ids)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从知识库移除文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"从知识库移除文档失败: {str(e)}")

@router.get("/knowledge-bases/{kb_id}/documents")
async def get_knowledge_base_documents(kb_id: str):
    """获取知识库的所有文档"""
    try:
        start_time = time.time()
        
        doc_ids = await rag_service.get_knowledge_base_documents(kb_id)
        
        # 获取文档详细信息
        all_docs = await rag_service.get_all_documents()
        kb_docs = [doc for doc in all_docs if doc["doc_id"] in doc_ids]
        
        processing_time = time.time() - start_time
        
        return ChatHistoryResponse(
            code=200,
            msg="获取知识库文档成功",
            data={
                "kb_id": kb_id,
                "documents": kb_docs,
                "total_count": len(kb_docs),
                "processing_time": processing_time
            }
        )
        
    except Exception as e:
        logger.error(f"获取知识库文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库文档失败: {str(e)}")


@router.post("/analyze-documents")
async def analyze_documents_for_archive(
    files: List[UploadFile] = File(...),
    prompt: str = Form(...),
    custom_analysis: Optional[str] = Form(None)
):
    """分析文档内容，预览归档建议（不实际保存）"""
    try:
        start_time = time.time()
        
        if len(files) > 20:  # 限制批量上传数量
            raise HTTPException(
                status_code=400,
                detail="批量上传文件数量不能超过20个"
            )
        
        results = []
        success_count = 0
        failure_count = 0
        
        for file in files:
            try:
                # 检查文件类型
                file_ext = file.filename.split('.')[-1].lower() if file.filename else ''
                if f".{file_ext}" not in settings.allowed_file_types:
                    results.append({
                        "fileName": file.filename or "unknown",
                        "success": False,
                        "error": f"不支持的文件类型: {file_ext}"
                    })
                    failure_count += 1
                    continue
                
                # 读取文件内容
                content = await file.read()
                if len(content) > settings.max_file_size:
                    results.append({
                        "fileName": file.filename or "unknown",
                        "success": False,
                        "error": f"文件大小超过限制"
                    })
                    failure_count += 1
                    continue
                
                # 调用文档分析服务（仅分析，不保存）
                result = await rag_service.analyze_document_for_archive(
                    file_content=content,
                    filename=file.filename or "unknown",
                    file_type=file.content_type or "application/octet-stream",
                    analysis_prompt=prompt,
                    custom_analysis=custom_analysis == "true"
                )
                
                results.append({
                    **result,
                    "success": True
                })
                success_count += 1
                
            except Exception as e:
                results.append({
                    "fileName": file.filename or "unknown",
                    "success": False,
                    "error": str(e)
                })
                failure_count += 1
        
        processing_time = time.time() - start_time
        
        return ChatHistoryResponse(
            code=200,
            msg=f"文档分析完成: 成功{success_count}个, 失败{failure_count}个",
            data={
                "results": results,
                "totalFiles": len(files),
                "successCount": success_count,
                "failureCount": failure_count,
                "processing_time": processing_time
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"文档分析失败: {str(e)}")


@router.post("/confirm-smart-archive")
async def confirm_smart_archive(
    request: dict
):
    """确认归档分析结果，执行实际归档操作"""
    try:
        start_time = time.time()
        
        files_data = request.get("files", [])
        analysis_results = request.get("analysisResults", [])
        
        if len(files_data) != len(analysis_results):
            raise HTTPException(
                status_code=400,
                detail="文件数据与分析结果数量不匹配"
            )
        
        results = []
        success_count = 0
        failure_count = 0
        
        for i, (file_data, analysis_result) in enumerate(zip(files_data, analysis_results)):
            try:
                if not analysis_result.get("success"):
                    results.append({
                        "fileName": file_data.get("fileName", "unknown"),
                        "success": False,
                        "error": analysis_result.get("error", "分析失败")
                    })
                    failure_count += 1
                    continue
                
                # 执行实际归档操作
                result = await rag_service.confirm_archive_document(
                    file_content=file_data.get("content"),  # Base64编码的文件内容
                    filename=file_data.get("fileName"),
                    file_type=file_data.get("fileType"),
                    analysis_result=analysis_result
                )
                
                results.append({
                    **result,
                    "success": True
                })
                success_count += 1
                
            except Exception as e:
                results.append({
                    "fileName": file_data.get("fileName", "unknown"),
                    "success": False,
                    "error": str(e)
                })
                failure_count += 1
        
        processing_time = time.time() - start_time
        
        return ChatHistoryResponse(
            code=200,
            msg=f"智能归档完成: 成功{success_count}个, 失败{failure_count}个",
            data={
                "results": results,
                "totalFiles": len(files_data),
                "successCount": success_count,
                "failureCount": failure_count,
                "processing_time": processing_time
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认归档失败: {e}")
        raise HTTPException(status_code=500, detail=f"确认归档失败: {str(e)}")

@router.post("/analyze-existing-documents")
async def analyze_existing_documents_for_archive(
    request: dict
):
    """分析已有文档进行智能归档（基于doc_id）"""
    try:
        start_time = time.time()
        
        doc_ids = request.get("docIds", [])
        prompt = request.get("prompt", "请根据文档内容自动判断文档类型和主题，选择最合适的知识库进行归档")
        custom_analysis = request.get("customAnalysis", True)
        
        if len(doc_ids) > 20:  # 限制批量分析数量
            raise HTTPException(
                status_code=400,
                detail="批量分析文档数量不能超过20个"
            )
        
        results = []
        success_count = 0
        failure_count = 0
        
        # 获取所有文档信息
        all_docs = await rag_service.get_all_documents()
        doc_map = {doc["doc_id"]: doc for doc in all_docs}
        
        for doc_id in doc_ids:
            try:
                if doc_id not in doc_map:
                    results.append({
                        "docId": doc_id,
                        "success": False,
                        "error": "文档不存在"
                    })
                    failure_count += 1
                    continue
                
                doc_info = doc_map[doc_id]
                
                # 获取文档内容（从已存储的分块中重构）
                chunks = await rag_service.get_document_chunks(doc_id)
                if not chunks:
                    results.append({
                        "docId": doc_id,
                        "filename": doc_info.get("filename", "unknown"),
                        "success": False,
                        "error": "无法获取文档内容"
                    })
                    failure_count += 1
                    continue
                
                # 重构文档内容
                text_content = "\n".join([chunk["content"] for chunk in chunks])
                
                # 调用文档分析服务
                result = await rag_service.analyze_existing_document_for_archive(
                    doc_id=doc_id,
                    filename=doc_info.get("filename", "unknown"),
                    file_type=doc_info.get("file_type", "application/octet-stream"),
                    text_content=text_content,
                    analysis_prompt=prompt,
                    custom_analysis=custom_analysis
                )
                
                results.append({
                    **result,
                    "docId": doc_id,
                    "success": True
                })
                success_count += 1
                
            except Exception as e:
                results.append({
                    "docId": doc_id,
                    "filename": doc_map.get(doc_id, {}).get("filename", "unknown"),
                    "success": False,
                    "error": str(e)
                })
                failure_count += 1
        
        processing_time = time.time() - start_time
        
        return ChatHistoryResponse(
            code=200,
            msg=f"文档分析完成: 成功{success_count}个, 失败{failure_count}个",
            data={
                "results": results,
                "totalDocuments": len(doc_ids),
                "successCount": success_count,
                "failureCount": failure_count,
                "processing_time": processing_time
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析已有文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析已有文档失败: {str(e)}")


@router.post("/confirm-existing-archive")
async def confirm_existing_archive(
    request: dict
):
    """确认已有文档的归档操作"""
    try:
        start_time = time.time()
        
        analysis_results = request.get("analysisResults", [])
        
        results = []
        success_count = 0
        failure_count = 0
        
        for analysis_result in analysis_results:
            try:
                if not analysis_result.get("success"):
                    results.append({
                        "docId": analysis_result.get("docId"),
                        "filename": analysis_result.get("filename", "unknown"),
                        "success": False,
                        "error": analysis_result.get("error", "分析失败")
                    })
                    failure_count += 1
                    continue
                
                # 执行实际归档操作
                result = await rag_service.confirm_existing_document_archive(
                    doc_id=analysis_result.get("docId"),
                    analysis_result=analysis_result
                )
                
                results.append({
                    **result,
                    "docId": analysis_result.get("docId"),
                    "success": True
                })
                success_count += 1
                
            except Exception as e:
                results.append({
                    "docId": analysis_result.get("docId"),
                    "filename": analysis_result.get("filename", "unknown"),
                    "success": False,
                    "error": str(e)
                })
                failure_count += 1
        
        processing_time = time.time() - start_time
        
        return ChatHistoryResponse(
            code=200,
            msg=f"智能归档完成: 成功{success_count}个, 失败{failure_count}个",
            data={
                "results": results,
                "totalDocuments": len(analysis_results),
                "successCount": success_count,
                "failureCount": failure_count,
                "processing_time": processing_time
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认已有文档归档失败: {e}")
        raise HTTPException(status_code=500, detail=f"确认已有文档归档失败: {str(e)}")
