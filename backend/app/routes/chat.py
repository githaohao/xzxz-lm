from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse, FileResponse
import uuid
import os
import time
from datetime import datetime
from typing import List, Optional
import aiofiles
import logging
import traceback
import json

from app.models.schemas import (
    ChatRequest, ChatResponse, FileUploadResponse, 
    OCRRequest, OCRResponse, TTSRequest, TTSResponse,
    MessageType, MultimodalStreamRequest, RAGSearchRequest, 
    RAGSearchResponse, DocumentInfo
)
from app.services.lm_studio_service import lm_studio_service
from app.services.ocr_service import ocr_service
from app.services.tts_service import tts_service
from app.services.rag_service import rag_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """处理聊天请求"""
    try:
        start_time = time.time()
        
        # 调用LM Studio服务
        response_text = await lm_studio_service.chat_completion(request)
        
        processing_time = time.time() - start_time
        message_id = str(uuid.uuid4())
        
        return ChatResponse(
            response=response_text,
            message_id=message_id,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"聊天请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")

@router.post("/chat/stream")
async def chat_completion_stream(request: ChatRequest):
    """流式聊天响应"""
    try:
        async def generate():
            async for chunk in lm_studio_service.chat_completion_stream(request):
                if chunk.strip():
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"流式聊天请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """文件上传处理"""
    try:
        # 检查文件类型
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_ext}"
            )
        
        # 检查文件大小
        content = await file.read()
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制: {settings.max_file_size / 1024 / 1024:.1f}MB"
            )
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file_id}_{file.filename}"
        file_path = os.path.join(settings.upload_dir, safe_filename)
        
        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"文件上传成功: {safe_filename}")
        
        return FileUploadResponse(
            file_id=file_id,
            file_name=file.filename,
            file_path=file_path,
            file_size=len(content),
            file_type=file_ext
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.post("/ocr", response_model=OCRResponse)
async def extract_text(file_path: str = Form(...)):
    """OCR文本提取"""
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            text, confidence, processing_time = await ocr_service.extract_text_from_pdf(file_path)
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            text, confidence, processing_time = await ocr_service.extract_text_from_image(file_path)
        else:
            raise HTTPException(status_code=400, detail="不支持的文件类型进行OCR")
        
        return OCRResponse(
            text=text,
            confidence=confidence,
            processing_time=processing_time,
            detected_language="zh-cn" if confidence > 0 else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"OCR处理失败: {str(e)}")

@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """文字转语音"""
    try:
        audio_path, file_size = await tts_service.text_to_speech(
            text=request.text,
            voice=request.voice,
            rate=request.rate,
            volume=request.volume
        )
        
        return TTSResponse(
            audio_file=os.path.basename(audio_path),
            file_size=file_size
        )
        
    except Exception as e:
        logger.error(f"TTS转换失败: {e}")
        raise HTTPException(status_code=500, detail=f"TTS转换失败: {str(e)}")

@router.get("/tts/audio/{filename}")
async def get_tts_audio(filename: str):
    """获取TTS音频文件"""
    try:
        audio_path = os.path.join(settings.upload_dir, "tts_audio", filename)
        
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        return FileResponse(
            audio_path,
            media_type="audio/mpeg",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取音频文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取音频文件失败: {str(e)}")

# 新增：处理已预处理文件数据的流式聊天接口
@router.post("/chat/multimodal/stream/processed")
async def multimodal_chat_stream_with_processed_data(
    request: MultimodalStreamRequest
):
    """处理已预处理文件数据的流式多模态聊天接口"""
    async def generate():
        try:
            logger.info(f"开始处理流式多模态聊天请求: {request.message[:50]}...")
            
            # 构建完整消息
            full_message = request.message
            
            # 如果有文件数据，根据rag_enabled决定处理方式
            if request.file_data:
                logger.info(f"处理文件数据: {request.file_data.name}")
                
                # 检查是否启用RAG功能
                if request.file_data.rag_enabled:
                    logger.info("启用RAG模式，进行智能检索...")
                    yield f"data: {json.dumps({'type': 'file_processing', 'message': '🧠 启用智能检索模式'})}\n\n"
                    
                    # 如果文件还没有进行RAG处理，先进行处理
                    if not request.file_data.doc_id and request.file_data.content:
                        logger.info("开始RAG文档处理...")
                        yield f"data: {json.dumps({'type': 'file_processing', 'message': '正在对文档进行智能索引...'})}\n\n"
                        
                        # 处理文档并生成doc_id
                        doc_id = await rag_service.process_document(
                            content=request.file_data.content,
                            filename=request.file_data.name,
                            file_type=request.file_data.type
                        )
                        request.file_data.doc_id = doc_id
                        yield f"data: {json.dumps({'type': 'file_processing', 'message': f'文档索引完成: {request.file_data.name}'})}\n\n"
                    
                    # 如果有doc_id，使用RAG检索相关内容
                    if request.file_data.doc_id:
                        logger.info("开始RAG检索相关内容...")
                        yield f"data: {json.dumps({'type': 'file_processing', 'message': '正在检索相关文档片段...'})}\n\n"
                        
                        relevant_chunks = await rag_service.search_relevant_chunks(
                            query=request.message,
                            doc_ids=[request.file_data.doc_id],
                            top_k=settings.rag_default_top_k,
                            min_similarity=settings.rag_default_min_similarity
                        )
                        
                        if relevant_chunks:
                            # 构建RAG上下文
                            rag_context = "\n\n[相关文档内容]\n"
                            for i, chunk in enumerate(relevant_chunks, 1):
                                rag_context += f"片段{i} (相似度: {chunk['similarity']:.2f}):\n{chunk['content']}\n\n"
                            
                            full_message = request.message + rag_context
                            chunk_count = len(relevant_chunks)
                            yield f"data: {json.dumps({'type': 'file_processing', 'message': f'🔍 检索到 {chunk_count} 个相关片段'})}\n\n"
                        else:
                            # 如果没有找到相关内容，提示无相关内容
                            yield f"data: {json.dumps({'type': 'file_processing', 'message': '⚠️ 未找到相关片段'})}\n\n"
                    else:
                        # 没有doc_id且没有content，无法处理
                        yield f"data: {json.dumps({'type': 'file_processing', 'message': '❌ 文档处理失败：缺少内容'})}\n\n"
                else:
                    # 关闭RAG模式，使用完整文档内容
                    logger.info("关闭RAG模式，使用完整文档内容...")
                    yield f"data: {json.dumps({'type': 'file_processing', 'message': '📄 使用完整文档模式'})}\n\n"
                    
                    if request.file_data.content:
                        # 如果有直接的内容，使用它
                        file_content = f"\n\n[文件内容: {request.file_data.name}]\n{request.file_data.content}"
                        full_message = request.message + file_content
                        yield f"data: {json.dumps({'type': 'file_processing', 'message': f'已加载完整文档: {request.file_data.name}'})}\n\n"
                    elif request.file_data.doc_id:
                        # 如果只有doc_id，从RAG系统获取所有分块内容
                        logger.info("从RAG系统获取完整文档内容...")
                        yield f"data: {json.dumps({'type': 'file_processing', 'message': '正在获取完整文档内容...'})}\n\n"
                        
                        # 获取所有文档分块
                        all_chunks = await rag_service.get_document_chunks(request.file_data.doc_id)
                        
                        if all_chunks:
                            # 重建完整文档（分块已经排序）
                            full_content = "\n".join([chunk['content'] for chunk in all_chunks])
                            
                            file_content = f"\n\n[文件内容: {request.file_data.name}]\n{full_content}"
                            full_message = request.message + file_content
                            yield f"data: {json.dumps({'type': 'file_processing', 'message': f'已重建完整文档: {request.file_data.name}'})}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'file_processing', 'message': '❌ 无法获取文档内容'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'file_processing', 'message': '❌ 文档处理失败：缺少内容和ID'})}\n\n"
            

            
            # 构建聊天请求
            chat_request = ChatRequest(
                message=full_message,
                history=request.history,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True
            )
            
            logger.info("开始AI流式对话处理...")
            
            # 流式获取AI响应
            async for chunk in lm_studio_service.chat_completion_stream(chat_request):
                if chunk.strip():
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"流式多模态聊天失败: {e}")
            error_message = f"处理请求时出现错误: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'message': error_message})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/rag/process")
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

@router.get("/rag/documents")
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

@router.post("/rag/search", response_model=RAGSearchResponse)
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

@router.get("/rag/documents/{doc_id}", response_model=DocumentInfo)
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

@router.delete("/rag/documents/{doc_id}")
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