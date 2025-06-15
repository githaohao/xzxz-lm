from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse, Response
from typing import Optional, Dict, List, Any
import logging
from app.services.funaudio_service_real import FunAudioLLMService
from app.services.tts_service import tts_service
import json
import base64
import asyncio
import os
from pydantic import BaseModel
from app.services.lm_studio_service import lm_studio_service
from app.models.schemas import ChatRequest, SpeechSynthesizeRequest
from app.utils import clean_text_for_speech, split_text_for_tts, synthesize_speech_chunk, convert_rate_to_string, validate_audio_data, format_voice_response
import re
import hashlib
from app.services.voice_websocket_service import voice_websocket_service
from app.services.voice_stream_service import voice_stream_service

# 创建 FunAudioLLM 服务实例
funaudio_service = FunAudioLLMService()

router = APIRouter(prefix="/voice", tags=["voice"])

logger = logging.getLogger(__name__)

# 这些类已经移到相应的服务文件中

@router.post("/chat")
async def voice_chat(
    audio: UploadFile = File(...),
    session_id: str = Form("default"),
    language: str = Form("auto")
):
    """
    语音聊天接口 - 使用FunAudioLLM进行高性能语音识别和对话
    
    特性:
    - 高性能语音识别（比Whisper快15倍）
    - 情感识别和声学事件检测
    - 支持50+语言
    - 对话历史管理
    """
    try:
        logger.info(f"🎤 FunAudioLLM语音聊天请求 - 会话: {session_id}, 语言: {language}")
        
        # 读取音频数据
        audio_data = await audio.read()
        
        if not validate_audio_data(audio_data):
            raise HTTPException(status_code=400, detail="音频数据为空")
        
        # 调用FunAudioLLM服务进行语音聊天
        result = await funaudio_service.voice_chat(
            audio_data=audio_data,
            session_id=session_id,
            language=language
        )
        
        if result["success"]:
            logger.info(f"✅ FunAudioLLM语音聊天成功 - 识别: {result['recognized_text'][:50]}...")
            return JSONResponse(content=result)
        else:
            # 检查是否是"未识别到有效语音内容"的情况
            error_msg = result.get('error', '未知错误')
            if "未识别到有效语音内容" in error_msg:
                logger.info(f"🔇 未检测到语音内容: {error_msg}")
                # 返回200状态码，但success为false，表示正常处理但没有语音
                return JSONResponse(content=result)
            else:
                # 真正的错误才返回500
                logger.error(f"❌ FunAudioLLM语音聊天失败: {error_msg}")
                return JSONResponse(
                    status_code=500,
                    content=result
                )
            
    except Exception as e:
        logger.error(f"❌ FunAudioLLM语音聊天异常: {e}")
        return JSONResponse(
            status_code=500,
            content=format_voice_response(
                success=False,
                error=str(e),
                data={
                    "recognized_text": "",
                    "response": "抱歉，语音处理出现问题。请稍后重试。",
                    "engine": "FunAudioLLM-SenseVoice"
                }
            )
        )

@router.post("/recognize")
async def voice_recognize(
    audio: UploadFile = File(...),
    language: str = Form("auto")
):
    """FunAudioLLM语音识别"""
    try:
        logger.info(f"🎯 FunAudioLLM语音识别请求 - 语言: {language}")
        
        # 读取音频数据
        audio_data = await audio.read()
        
        if not validate_audio_data(audio_data):
            raise HTTPException(status_code=400, detail="音频数据为空")
        
        # 调用FunAudioLLM服务进行语音识别
        result = await funaudio_service.voice_recognition(
            audio_data=audio_data,
            language=language
        )
        
        if result["success"]:
            logger.info(f"✅ FunAudioLLM语音识别成功: {result['recognized_text'][:50]}...")
            return JSONResponse(content=result)
        else:
            logger.error(f"❌ FunAudioLLM语音识别失败: {result.get('error', '未知错误')}")
            return JSONResponse(
                status_code=500,
                content=result
            )
            
    except Exception as e:
        logger.error(f"❌ FunAudioLLM语音识别异常: {e}")
        return JSONResponse(
            status_code=500,
            content=format_voice_response(
                success=False,
                error=str(e),
                data={
                    "recognized_text": "",
                    "engine": "FunAudioLLM-SenseVoice"
                }
            )
        )

@router.post("/analyze")
async def audio_analysis(
    audio: UploadFile = File(...),
    query: str = Form(...),
    session_id: str = Form("default")
):
    """
    音频分析接口 - 基于FunAudioLLM的语音识别结果进行分析
    """
    try:
        logger.info(f"🔍 收到音频分析请求")
        
        # 读取音频数据
        audio_data = await audio.read()
        
        if not validate_audio_data(audio_data):
            raise HTTPException(status_code=400, detail="音频数据为空")
        
        if not query.strip():
            raise HTTPException(status_code=400, detail="查询文本为空")
        
        # 使用FunAudioLLM进行语音识别
        recognition_result = await funaudio_service.voice_recognition(audio_data, "auto")
        
        if recognition_result["success"]:
            result = format_voice_response(
                success=True,
                data={
                    "response": f"基于FunAudioLLM识别结果：「{recognition_result['recognized_text']}」\n分析查询：{query}\n情感信息：{recognition_result.get('emotion', {})}",
                    "query": query,
                    "engine": "FunAudioLLM-SenseVoice",
                    "analysis_type": "recognition_based_analysis",
                    "recognition_result": recognition_result
                }
            )
        else:
            result = recognition_result
        
        if result["success"]:
            logger.info(f"✅ 音频分析成功")
            return JSONResponse(content=result)
        else:
            logger.error(f"❌ 音频分析失败: {result.get('error', '未知错误')}")
            return JSONResponse(
                status_code=500,
                content=result
            )
            
    except Exception as e:
        logger.error(f"❌ 音频分析接口错误: {e}")
        return JSONResponse(
            status_code=500,
            content=format_voice_response(
                success=False,
                error=str(e)
            )
        )

@router.get("/engine")
async def get_voice_engine_status():
    """获取FunAudioLLM引擎状态"""
    try:
        logger.info("🔍 检查FunAudioLLM引擎状态...")
        
        # 获取服务健康状态
        status = await funaudio_service.health_check()
        
        return JSONResponse(content=format_voice_response(
            success=True,
            data={
                "engine": {
                    "name": "FunAudioLLM",
                    "status": status,
                    "features": status.get("features", []),
                    "supported_languages": status.get("supported_languages", [])
                },
                "message": "FunAudioLLM引擎状态检查完成"
            }
        ))
        
    except Exception as e:
        logger.error(f"❌ FunAudioLLM引擎状态检查失败: {e}")
        return JSONResponse(
            status_code=500,
            content=format_voice_response(
                success=False,
                error=str(e),
                data={
                    "engine": {
                        "name": "FunAudioLLM",
                        "status": {"available": False}
                    }
                }
            )
        )

@router.get("/conversation/{session_id}")
async def get_conversation_summary(session_id: str):
    """获取会话摘要"""
    try:
        logger.info(f"📊 获取FunAudioLLM会话摘要: {session_id}")
        
        summary = await funaudio_service.get_conversation_summary(session_id)
        
        return JSONResponse(content=format_voice_response(
            success=True,
            data={"summary": summary}
        ))
        
    except Exception as e:
        logger.error(f"❌ 获取会话摘要失败: {e}")
        return JSONResponse(
            status_code=500,
            content=format_voice_response(
                success=False,
                error=str(e)
            )
        )

@router.delete("/conversation/{session_id}")
async def clear_conversation_history(session_id: str):
    """清除会话历史"""
    try:
        logger.info(f"🗑️ 清除FunAudioLLM会话历史: {session_id}")
        
        success = await funaudio_service.clear_conversation_history(session_id)
        
        if success:
            return JSONResponse(content=format_voice_response(
                success=True,
                data={"message": f"会话 {session_id} 历史已清除"}
            ))
        else:
            return JSONResponse(
                status_code=500,
                content=format_voice_response(
                    success=False,
                    error="清除会话历史失败"
                )
            )
            
    except Exception as e:
        logger.error(f"❌ 清除会话历史异常: {e}")
        return JSONResponse(
            status_code=500,
            content=format_voice_response(
                success=False,
                error=str(e)
            )
        )

@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """
    语音WebSocket端点 - 支持流式音频传输
    
    支持实时语音对话和流式音频传输
    消息格式:
    - 配置: {"type": "config", "session_id": "optional", "language": "auto"}
    - 流式音频: 直接发送二进制音频数据
    - 语音对话: {"type": "voice_chat", "session_id": "optional", "language": "auto"} + 二进制数据
    - 状态: {"type": "status", "status": "connected|listening|processing|error"}
    - 心跳: {"type": "ping"} / {"type": "pong"}
    """
    await voice_websocket_service.connection_manager.connect(websocket)
    
    try:
        # 发送连接确认
        await websocket.send_json({
            "type": "status",
            "status": "connected",
            "message": "语音WebSocket连接已建立，支持流式音频传输",
            "session_id": voice_websocket_service.connection_manager.get_session_id(websocket),
            "features": ["stream_audio", "binary_transfer", "real_time"],
            "timestamp": voice_websocket_service.connection_manager.get_session_id(websocket)
        })
        
        while True:
            # 接收消息 - 支持JSON、文本和二进制数据
            try:
                # 尝试接收消息
                data = await websocket.receive()
                if "bytes" in data:
                    # 处理二进制消息（音频数据）
                    binary_data = data["bytes"]
                    await voice_websocket_service.handle_stream_audio_data(websocket, binary_data)
                        
            except Exception as e:
                logger.error(f"❌ 处理WebSocket消息失败: {e}")
                await websocket.send_json({
                    "type": "error",
                    "error": str(e),
                    "timestamp": voice_websocket_service.connection_manager.get_session_id(websocket)
                })
                
    except WebSocketDisconnect:
        logger.info("🔌 语音WebSocket客户端断开连接")
    except Exception as e:
        logger.error(f"❌ 语音WebSocket连接异常: {e}")
    finally:
        voice_websocket_service.connection_manager.disconnect(websocket)

@router.post("/speech/synthesize")
async def speech_synthesize(request: SpeechSynthesizeRequest):
    """
    语音合成端点 - 直接返回音频流
    
    与/tts端点不同，此端点直接返回音频文件内容，而不是文件信息
    专为前端/speech/synthesize路由设计
    """
    try:
        logger.info(f"🔊 语音合成请求: {request.text[:50]}...")
        
        # 使用语音流服务处理合成
        audio_content = await voice_stream_service.process_speech_synthesis(
            text=request.text,
            voice=request.voice,
            rate=request.rate
        )
        
        if not audio_content:
            logger.warning("清理后的文本为空，跳过语音合成")
            # 返回空的音频响应
            return Response(
                content=b"",
                media_type="audio/mpeg",
                headers={
                    "Content-Length": "0",
                    "Content-Disposition": "inline; filename=empty_speech.mp3"
                }
            )
        
        logger.info(f"✅ 语音合成成功，文件大小: {len(audio_content)} 字节")
        
        # 直接返回音频内容
        return Response(
            content=audio_content,
            media_type="audio/mpeg",
            headers={
                "Content-Length": str(len(audio_content)),
                "Content-Disposition": "inline; filename=synthesized_speech.mp3"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 语音合成失败: {e}")
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")

@router.post("/chat/stream")
async def voice_chat_stream(
    audio: UploadFile = File(...),
    session_id: str = Form(...),
    language: str = Form(default="auto"),
    knowledge_base_id: Optional[str] = Form(default=None)
):
    """流式语音聊天 - AI生成回复的同时进行TTS合成"""
    try:
        logger.info(f"🎤 开始流式语音聊天处理，会话ID: {session_id}")
        
        # 读取音频数据
        audio_data = await audio.read()
        if not validate_audio_data(audio_data):
            raise HTTPException(status_code=400, detail="音频数据为空")

        # 使用语音流服务生成流式响应
        return StreamingResponse(
            voice_stream_service.generate_streaming_response(
                audio_data=audio_data,
                session_id=session_id,
                language=language,
                knowledge_base_id=knowledge_base_id
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"流式语音聊天请求失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")