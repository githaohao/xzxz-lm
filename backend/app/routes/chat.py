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
    MessageType, MultimodalStreamRequest
)
from app.services.lm_studio_service import lm_studio_service
from app.services.ocr_service import ocr_service
from app.services.tts_service import tts_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])

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

@router.post("/chat/multimodal")
async def multimodal_chat(
    message: str = Form(...),
    file: Optional[UploadFile] = File(None),
    temperature: float = Form(0.7),
    max_tokens: int = Form(2048)
):
    """多模态聊天接口"""
    start_time = time.time()
    try:
        logger.info(f"开始处理多模态聊天请求: {message[:50]}...")
        
        # 如果有文件，先处理文件
        file_content = ""
        file_info = None
        
        if file:
            logger.info(f"处理上传文件: {file.filename} ({file.size} bytes)")
            
            # 上传文件
            upload_result = await upload_file(file)
            file_info = upload_result
            
            # 如果是PDF或图片，进行OCR
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext in ['.pdf', '.png', '.jpg', '.jpeg']:
                logger.info(f"开始OCR处理: {file_ext}文件")
                try:
                    ocr_result = await extract_text(upload_result.file_path)
                    file_content = f"\n\n[文件内容]\n{ocr_result.text}"
                    logger.info(f"OCR完成，提取文本长度: {len(ocr_result.text)}字符")
                except Exception as ocr_error:
                    logger.error(f"OCR处理失败: {ocr_error}")
                    file_content = f"\n\n[文件处理失败: {str(ocr_error)}]"
        
        # 构建聊天请求
        full_message = message + file_content
        chat_request = ChatRequest(
            message=full_message,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        logger.info("开始AI对话处理...")
        # 获取AI响应
        ai_response = await chat_completion(chat_request)
        
        total_time = time.time() - start_time
        logger.info(f"多模态聊天完成，总耗时: {total_time:.2f}秒")
        
        return {
            "response": ai_response.response,
            "message_id": ai_response.message_id,
            "processing_time": ai_response.processing_time,
            "file_info": file_info,
            "extracted_text": file_content if file_content else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"多模态聊天失败 (耗时{total_time:.2f}秒): {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        
        # 返回友好的错误消息而不是抛出异常
        return {
            "response": f"抱歉，处理您的请求时遇到问题：{str(e)}。请稍后重试或尝试发送较小的文件。",
            "message_id": str(uuid.uuid4()),
            "processing_time": total_time,
            "file_info": None,
            "extracted_text": None
        }

@router.post("/chat/multimodal/stream")
async def multimodal_chat_stream(
    message: str = Form(...),
    file: Optional[UploadFile] = File(None),
    temperature: float = Form(0.7),
    max_tokens: int = Form(2048)
):
    """流式多模态聊天接口"""
    async def generate():
        try:
            logger.info(f"开始处理流式多模态聊天请求: {message[:50]}...")
            
            # 如果有文件，先处理文件
            file_content = ""
            file_info = None
            
            if file:
                logger.info(f"处理上传文件: {file.filename} ({file.size} bytes)")
                
                # 发送文件处理状态
                yield f"data: {json.dumps({'type': 'file_processing', 'message': '正在处理文件...'})}\n\n"
                
                # 内联文件处理，避免重复读取文件流
                try:
                    # 检查文件类型
                    file_ext = os.path.splitext(file.filename)[1].lower()
                    if file_ext not in settings.allowed_file_types:
                        yield f"data: {json.dumps({'type': 'error', 'message': f'不支持的文件类型: {file_ext}'})}\n\n"
                        yield "data: [DONE]\n\n"
                        return
                    
                    # 读取文件内容
                    await file.seek(0)  # 重置文件指针到开始位置
                    content = await file.read()
                    if len(content) > settings.max_file_size:
                        yield f"data: {json.dumps({'type': 'error', 'message': f'文件大小超过限制: {settings.max_file_size / 1024 / 1024:.1f}MB'})}\n\n"
                        yield "data: [DONE]\n\n"
                        return
                    
                    # 生成唯一文件名并保存
                    file_id = str(uuid.uuid4())
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_filename = f"{timestamp}_{file_id}_{file.filename}"
                    file_path = os.path.join(settings.upload_dir, safe_filename)
                    
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(content)
                    
                    # 创建文件信息对象
                    file_info = FileUploadResponse(
                        file_id=file_id,
                        file_name=file.filename,
                        file_path=file_path,
                        file_size=len(content),
                        file_type=file_ext
                    )
                    
                    logger.info(f"文件上传成功: {safe_filename}")
                    
                    # 如果是PDF或图片，进行OCR
                    if file_ext in ['.pdf', '.png', '.jpg', '.jpeg']:
                        logger.info(f"开始OCR处理: {file_ext}文件")
                        yield f"data: {json.dumps({'type': 'ocr_processing', 'message': '正在识别文件内容...'})}\n\n"
                        
                        try:
                            ocr_result = await extract_text(file_path)
                            file_content = f"\n\n[文件内容]\n{ocr_result.text}"
                            logger.info(f"OCR完成，提取文本长度: {len(ocr_result.text)}字符")
                            yield f"data: {json.dumps({'type': 'ocr_complete', 'message': f'文件内容识别完成，提取了{len(ocr_result.text)}字符'})}\n\n"
                        except Exception as ocr_error:
                            logger.error(f"OCR处理失败: {ocr_error}")
                            file_content = f"\n\n[文件处理失败: {str(ocr_error)}]"
                            yield f"data: {json.dumps({'type': 'ocr_error', 'message': f'文件处理失败: {str(ocr_error)}'})}\n\n"
                            
                except Exception as upload_error:
                    logger.error(f"文件上传失败: {upload_error}")
                    yield f"data: {json.dumps({'type': 'error', 'message': f'文件上传失败: {str(upload_error)}'})}\n\n"
                    yield "data: [DONE]\n\n"
                    return
            
            # 发送AI思考状态
            yield f"data: {json.dumps({'type': 'thinking', 'message': '正在思考...'})}\n\n"
            
            # 构建聊天请求
            full_message = message + file_content
            chat_request = ChatRequest(
                message=full_message,
                history=[],  # 这个接口不支持历史记录，使用空列表
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            logger.info("开始AI流式对话处理...")
            
            # 流式获取AI响应
            async for chunk in lm_studio_service.chat_completion_stream(chat_request):
                if chunk.strip():
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
            
            # 发送完成信号
            file_info_dict = None
            if file_info:
                file_info_dict = {
                    'file_id': file_info.file_id,
                    'file_name': file_info.file_name,
                    'file_path': file_info.file_path,
                    'file_size': file_info.file_size,
                    'file_type': file_info.file_type
                }
            yield f"data: {json.dumps({'type': 'complete', 'file_info': file_info_dict})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"流式多模态聊天失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'处理请求时出现错误: {str(e)}'})}\n\n"
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

async def multimodal_chat_stream_with_data(
    message: str,
    file_data: Optional[dict] = None,
    history: List = [],
    temperature: float = 0.7,
    max_tokens: int = 2048
):
    """使用预处理文件数据的流式多模态聊天接口"""
    try:
        logger.info(f"开始处理流式多模态聊天请求: {message[:50]}...")
        
        # 如果有文件，先处理文件
        file_content = ""
        file_info = None
        
        if file_data:
            logger.info(f"处理上传文件: {file_data['filename']} ({file_data['size']} bytes)")
            
            # 发送文件处理状态
            yield f"data: {json.dumps({'type': 'file_processing', 'message': '正在处理文件...'})}\n\n"
            
            # 内联文件处理，使用预处理的文件数据
            try:
                # 检查文件类型
                file_ext = os.path.splitext(file_data['filename'])[1].lower()
                if file_ext not in settings.allowed_file_types:
                    raise HTTPException(
                        status_code=400,
                        detail=f"不支持的文件类型: {file_ext}"
                    )
                
                # 检查文件大小
                content = file_data['content']
                if len(content) > settings.max_file_size:
                    raise HTTPException(
                        status_code=400,
                        detail=f"文件大小超过限制: {settings.max_file_size / 1024 / 1024:.1f}MB"
                    )
                
                # 生成唯一文件名并保存
                file_id = str(uuid.uuid4())
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = f"{timestamp}_{file_id}_{file_data['filename']}"
                file_path = os.path.join(settings.upload_dir, safe_filename)
                
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(content)
                
                # 创建文件信息对象
                file_info = FileUploadResponse(
                    file_id=file_id,
                    file_name=file_data['filename'],
                    file_path=file_path,
                    file_size=len(content),
                    file_type=file_ext
                )
                
                logger.info(f"文件上传成功: {safe_filename}")
                
                # 如果是PDF或图片，进行OCR
                if file_ext in ['.pdf', '.png', '.jpg', '.jpeg']:
                    logger.info(f"开始OCR处理: {file_ext}文件")
                    yield f"data: {json.dumps({'type': 'ocr_processing', 'message': '正在识别文件内容...'})}\n\n"
                    
                    try:
                        ocr_result = await extract_text(file_path)
                        file_content = f"\n\n[文件内容]\n{ocr_result.text}"
                        logger.info(f"OCR完成，提取文本长度: {len(ocr_result.text)}字符")
                        yield f"data: {json.dumps({'type': 'ocr_complete', 'message': f'文件内容识别完成，提取了{len(ocr_result.text)}字符'})}\n\n"
                    except Exception as ocr_error:
                        logger.error(f"OCR处理失败: {ocr_error}")
                        file_content = f"\n\n[文件处理失败: {str(ocr_error)}]"
                        yield f"data: {json.dumps({'type': 'ocr_error', 'message': f'文件处理失败: {str(ocr_error)}'})}\n\n"
                        
            except Exception as upload_error:
                logger.error(f"文件上传失败: {upload_error}")
                yield f"data: {json.dumps({'type': 'error', 'message': f'文件上传失败: {str(upload_error)}'})}\n\n"
                yield "data: [DONE]\n\n"
                return
        
        # 发送AI思考状态
        yield f"data: {json.dumps({'type': 'thinking', 'message': '正在思考...'})}\n\n"
        
        # 构建聊天请求
        full_message = message + file_content
        chat_request = ChatRequest(
            message=full_message,
            history=history,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        logger.info("开始AI流式对话处理...")
        
        # 流式获取AI响应
        async for chunk in lm_studio_service.chat_completion_stream(chat_request):
            if chunk.strip():
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
        
        # 发送完成信号
        file_info_dict = None
        if file_info:
            file_info_dict = {
                'file_id': file_info.file_id,
                'file_name': file_info.file_name,
                'file_path': file_info.file_path,
                'file_size': file_info.file_size,
                'file_type': file_info.file_type
            }
        yield f"data: {json.dumps({'type': 'complete', 'file_info': file_info_dict})}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"流式多模态聊天失败: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': f'处理请求时出现错误: {str(e)}'})}\n\n"
        yield "data: [DONE]\n\n"

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
            
            # 如果有已处理的文件数据，直接使用OCR文本
            if request.file_data and request.file_data.ocr_text:
                logger.info(f"使用已处理的文件数据: {request.file_data.name}")
                file_content = f"\n\n[文件内容: {request.file_data.name}]\n{request.file_data.ocr_text}"
                full_message = request.message + file_content
                
                # 发送文件处理完成状态
                file_message = f"使用已处理文件: {request.file_data.name}"
                yield f"data: {json.dumps({'type': 'file_processing', 'message': file_message})}\n\n"
            

            
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

# 包装为StreamingResponse
@router.post("/chat/multimodal/stream/response")
async def multimodal_chat_stream_response(
    message: str = Form(...),
    file: Optional[UploadFile] = File(None),
    temperature: float = Form(0.7),
    max_tokens: int = Form(2048)
):
    """流式多模态聊天响应包装"""
    # 预处理文件，避免在生成器中处理文件流
    file_data = None
    if file:
        try:
            await file.seek(0)  # 重置文件指针
            file_content = await file.read()
            file_data = {
                'filename': file.filename,
                'content': file_content,
                'content_type': file.content_type,
                'size': len(file_content)
            }
        except Exception as e:
            logger.error(f"预处理文件失败: {e}")
            # 返回错误响应
            async def error_generator():
                yield f"data: {json.dumps({'type': 'error', 'message': f'文件预处理失败: {str(e)}'})}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(
                error_generator(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
            )
    
    return StreamingResponse(
        multimodal_chat_stream_with_data(message, file_data, [], temperature, max_tokens),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )