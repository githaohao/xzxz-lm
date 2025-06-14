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
from app.models.schemas import ChatRequest
from app.utils import clean_text_for_speech, split_text_for_tts, synthesize_speech_chunk
import re

# 创建 FunAudioLLM 服务实例
funaudio_service = FunAudioLLMService()

router = APIRouter(prefix="/voice", tags=["voice"])

logger = logging.getLogger(__name__)

# WebSocket连接管理器
class VoiceConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_configs: Dict[WebSocket, Dict] = {}
        self.connection_sessions: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # 为每个连接生成唯一的会话ID
        session_id = f"ws-session-{len(self.active_connections)}-{asyncio.get_event_loop().time()}"
        self.connection_sessions[websocket] = session_id
        logger.info(f"🔌 新的语音WebSocket连接: {len(self.active_connections)}个活跃连接, 会话ID: {session_id}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_configs:
            del self.connection_configs[websocket]
        if websocket in self.connection_sessions:
            del self.connection_sessions[websocket]
        logger.info(f"🔌 语音WebSocket连接断开: {len(self.active_connections)}个活跃连接")
    
    def set_config(self, websocket: WebSocket, config: Dict):
        self.connection_configs[websocket] = config
    
    def get_config(self, websocket: WebSocket) -> Dict:
        return self.connection_configs.get(websocket, {})
    
    def get_session_id(self, websocket: WebSocket) -> str:
        return self.connection_sessions.get(websocket, "default")

voice_manager = VoiceConnectionManager()

# 语音合成请求模型
class SpeechSynthesizeRequest(BaseModel):
    text: str
    voice: Optional[str] = "zh-CN-XiaoxiaoNeural"
    rate: Optional[float] = 1.0
    pitch: Optional[float] = 1.0

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
        
        if len(audio_data) == 0:
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
            content={
                "success": False,
                "error": str(e),
                "recognized_text": "",
                "response": "抱歉，语音处理出现问题。请稍后重试。",
                "engine": "FunAudioLLM-SenseVoice"
            }
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
        
        if len(audio_data) == 0:
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
            content={
                "success": False,
                "error": str(e),
                "recognized_text": "",
                "engine": "FunAudioLLM-SenseVoice"
            }
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
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="音频数据为空")
        
        if not query.strip():
            raise HTTPException(status_code=400, detail="查询文本为空")
        
        # 使用FunAudioLLM进行语音识别
        recognition_result = await funaudio_service.voice_recognition(audio_data, "auto")
        
        if recognition_result["success"]:
            result = {
                "success": True,
                "response": f"基于FunAudioLLM识别结果：「{recognition_result['recognized_text']}」\n分析查询：{query}\n情感信息：{recognition_result.get('emotion', {})}",
                "query": query,
                "engine": "FunAudioLLM-SenseVoice",
                "analysis_type": "recognition_based_analysis",
                "recognition_result": recognition_result
            }
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
            content={
                "success": False,
                "error": str(e)
            }
        )

@router.get("/engine")
async def get_voice_engine_status():
    """获取FunAudioLLM引擎状态"""
    try:
        logger.info("🔍 检查FunAudioLLM引擎状态...")
        
        # 获取服务健康状态
        status = await funaudio_service.health_check()
        
        return JSONResponse(content={
            "success": True,
            "engine": {
                "name": "FunAudioLLM",
                "status": status,
                "features": status.get("features", []),
                "supported_languages": status.get("supported_languages", [])
            },
            "message": "FunAudioLLM引擎状态检查完成"
        })
        
    except Exception as e:
        logger.error(f"❌ FunAudioLLM引擎状态检查失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "engine": {
                    "name": "FunAudioLLM",
                    "status": {"available": False}
                }
            }
        )

@router.get("/conversation/{session_id}")
async def get_conversation_summary(session_id: str):
    """获取会话摘要"""
    try:
        logger.info(f"📊 获取FunAudioLLM会话摘要: {session_id}")
        
        summary = await funaudio_service.get_conversation_summary(session_id)
        
        return JSONResponse(content={
            "success": True,
            "summary": summary
        })
        
    except Exception as e:
        logger.error(f"❌ 获取会话摘要失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@router.delete("/conversation/{session_id}")
async def clear_conversation_history(session_id: str):
    """清除会话历史"""
    try:
        logger.info(f"🗑️ 清除FunAudioLLM会话历史: {session_id}")
        
        success = await funaudio_service.clear_conversation_history(session_id)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": f"会话 {session_id} 历史已清除"
            })
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "清除会话历史失败"
                }
            )
            
    except Exception as e:
        logger.error(f"❌ 清除会话历史异常: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """
    统一语音WebSocket端点
    
    支持实时音频流处理、唤醒词检测和语音对话
    消息格式:
    - 配置: {"type": "config", "wake_words": [...], "confidence_threshold": 0.6, "session_id": "optional"}
    - 音频: {"type": "audio", "data": "base64_audio_data", "timestamp": 1234567890, "mode": "wake_word|voice_chat"}
    - 语音对话: {"type": "voice_chat", "data": "base64_audio_data", "session_id": "optional", "language": "auto"}
    - 状态: {"type": "status", "status": "connected|listening|processing|error"}
    - 心跳: {"type": "ping"} / {"type": "pong"}
    """
    await voice_manager.connect(websocket)
    
    try:
        # 发送连接确认
        await websocket.send_json({
            "type": "status",
            "status": "connected",
            "message": "语音WebSocket连接已建立",
            "session_id": voice_manager.get_session_id(websocket),
            "timestamp": asyncio.get_event_loop().time()
        })
        
        while True:
            # 接收消息
            try:
                message = await websocket.receive_json()
                await handle_voice_message(websocket, message)
            except Exception as e:
                logger.error(f"❌ 处理WebSocket消息失败: {e}")
                await websocket.send_json({
                    "type": "error",
                    "error": str(e),
                    "timestamp": asyncio.get_event_loop().time()
                })
                
    except WebSocketDisconnect:
        logger.info("🔌 语音WebSocket客户端断开连接")
    except Exception as e:
        logger.error(f"❌ 语音WebSocket连接异常: {e}")
    finally:
        voice_manager.disconnect(websocket)



async def handle_voice_message(websocket: WebSocket, message: Dict):
    """处理统一语音WebSocket消息"""
    message_type = message.get("type")
    
    if message_type == "config":
        # 配置消息
        config = {
            "wake_words": message.get("wake_words", ["小智小智", "小智", "智能助手"]),
            "confidence_threshold": message.get("confidence_threshold", 0.6),
            "language": message.get("language", "zh"),
            "session_id": message.get("session_id") or voice_manager.get_session_id(websocket)
        }
        voice_manager.set_config(websocket, config)
        
        await websocket.send_json({
            "type": "config_ack",
            "config": config,
            "message": "配置已更新",
            "timestamp": asyncio.get_event_loop().time()
        })
        
    elif message_type == "audio":
        # 音频数据消息 - 根据mode决定处理方式
        mode = message.get("mode", "wake_word")
        if mode == "wake_word":
            await process_wake_word_audio(websocket, message)
        elif mode == "voice_chat":
            await process_voice_chat_audio(websocket, message)
        else:
            await websocket.send_json({
                "type": "error",
                "error": f"未知音频模式: {mode}",
                "timestamp": asyncio.get_event_loop().time()
            })
        
    elif message_type == "voice_chat":
        # 语音对话消息
        await process_voice_chat_audio(websocket, message)
        
    elif message_type == "ping":
        # 心跳消息
        await websocket.send_json({
            "type": "pong",
            "timestamp": asyncio.get_event_loop().time()
        })
        
    else:
        await websocket.send_json({
            "type": "error",
            "error": f"未知消息类型: {message_type}",
            "timestamp": asyncio.get_event_loop().time()
        })

# 保持向后兼容性
async def handle_wake_word_message(websocket: WebSocket, message: Dict):
    """向后兼容的唤醒词消息处理"""
    await handle_voice_message(websocket, message)

async def process_wake_word_audio(websocket: WebSocket, message: Dict):
    """处理音频数据进行唤醒词检测"""
    try:
        # 获取配置
        config = voice_manager.get_config(websocket)
        if not config:
            await websocket.send_json({
                "type": "error",
                "error": "请先发送配置信息",
                "timestamp": asyncio.get_event_loop().time()
            })
            return
        
        # 发送处理状态
        await websocket.send_json({
            "type": "status",
            "status": "processing",
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # 解码音频数据
        audio_data_b64 = message.get("data")
        if not audio_data_b64:
            raise ValueError("音频数据为空")
        
        audio_data = base64.b64decode(audio_data_b64)
        
        if len(audio_data) == 0:
            raise ValueError("音频数据解码后为空")
        
        # 调用FunAudioLLM进行唤醒词检测
        result = await funaudio_service.wake_word_detection(
            audio_data=audio_data,
            wake_words=config["wake_words"]
        )
        
        # 发送检测结果
        response = {
            "type": "detection",
            "wake_word_detected": result["wake_word_detected"],
            "detected_word": result.get("detected_word", ""),
            "recognized_text": result.get("recognized_text", ""),
            "confidence": result.get("confidence", 0.0),
            "engine": result.get("engine", "FunAudioLLM-SenseVoice"),
            "timestamp": asyncio.get_event_loop().time(),
            "success": result["success"]
        }
        
        if result["wake_word_detected"]:
            logger.info(f"✅ WebSocket检测到唤醒词: {result['detected_word']}")
        
        await websocket.send_json(response)
        
        # 发送监听状态
        await websocket.send_json({
            "type": "status",
            "status": "listening",
            "timestamp": asyncio.get_event_loop().time()
        })
        
    except Exception as e:
        logger.error(f"❌ WebSocket音频处理失败: {e}")
        await websocket.send_json({
            "type": "error",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        })

async def process_voice_chat_audio(websocket: WebSocket, message: Dict):
    """处理音频数据进行语音对话"""
    try:
        # 获取配置
        config = voice_manager.get_config(websocket)
        session_id = message.get("session_id") or voice_manager.get_session_id(websocket)
        language = message.get("language", config.get("language", "auto"))
        
        # 发送处理状态
        await websocket.send_json({
            "type": "status",
            "status": "processing",
            "message": "正在处理语音对话",
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # 解码音频数据
        audio_data_b64 = message.get("data")
        if not audio_data_b64:
            raise ValueError("音频数据为空")
        
        audio_data = base64.b64decode(audio_data_b64)
        
        if len(audio_data) == 0:
            raise ValueError("音频数据解码后为空")
        
        # 调用FunAudioLLM进行语音对话
        result = await funaudio_service.voice_chat(
            audio_data=audio_data,
            session_id=session_id,
            language=language
        )
        
        # 发送对话结果
        response = {
            "type": "voice_chat_response",
            "success": result["success"],
            "recognized_text": result.get("recognized_text", ""),
            "response": result.get("response", ""),
            "session_id": session_id,
            "history_length": result.get("history_length", 0),
            "engine": result.get("engine", "FunAudioLLM-SenseVoice"),
            "emotion": result.get("emotion", {}),
            "timestamp": asyncio.get_event_loop().time()
        }
        
        if result["success"]:
            logger.info(f"✅ WebSocket语音对话成功: {result.get('recognized_text', '')[:50]}...")
        else:
            logger.warning(f"⚠️ WebSocket语音对话失败: {result.get('error', '未知错误')}")
            response["error"] = result.get("error", "语音对话处理失败")
        
        await websocket.send_json(response)
        
        # 发送监听状态
        await websocket.send_json({
            "type": "status",
            "status": "listening",
            "message": "等待下一次语音输入",
            "timestamp": asyncio.get_event_loop().time()
        })
        
    except Exception as e:
        logger.error(f"❌ WebSocket语音对话处理失败: {e}")
        await websocket.send_json({
            "type": "error",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        })

@router.post("/speech/synthesize")
async def speech_synthesize(request: SpeechSynthesizeRequest):
    """
    语音合成端点 - 直接返回音频流
    
    与/tts端点不同，此端点直接返回音频文件内容，而不是文件信息
    专为前端/speech/synthesize路由设计
    """
    try:
        logger.info(f"🔊 语音合成请求: {request.text[:50]}...")
        
        # 清理文本，移除思考标签和表情符号
        clean_text = clean_text_for_speech(request.text)
        
        if not clean_text.strip():
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
        
        # 转换参数格式以匹配TTS服务
        rate_str = f"+{int((request.rate - 1) * 100)}%" if request.rate >= 1 else f"{int((request.rate - 1) * 100)}%"
        
        # 调用TTS服务，使用清理后的文本
        audio_path, file_size = await tts_service.text_to_speech(
            text=clean_text,
            voice=request.voice,
            rate=rate_str,
            volume="+0%"  # pitch在edge-tts中对应volume参数
        )
        
        # 检查音频文件是否存在
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=500, detail="音频文件生成失败")
        
        # 读取音频文件内容
        with open(audio_path, "rb") as audio_file:
            audio_content = audio_file.read()
        
        # 清理临时文件
        try:
            os.remove(audio_path)
        except Exception as e:
            logger.warning(f"清理临时音频文件失败: {e}")
        
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
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="音频数据为空")

        async def generate_streaming_response():
            try:
                # 第一步：语音识别
                yield f"data: {json.dumps({'type': 'status', 'message': '正在识别语音...'})}\n\n"
                
                # 使用FunAudioLLM进行语音识别
                recognition_result = await funaudio_service.voice_recognition(audio_data, language)
                
                if not recognition_result["success"]:
                    yield f"data: {json.dumps({'type': 'error', 'message': '语音识别失败'})}\n\n"
                    return
                
                recognized_text = recognition_result["recognized_text"]
                
                if not recognized_text.strip():
                    yield f"data: {json.dumps({'type': 'error', 'message': '未识别到有效语音内容'})}\n\n"
                    return
                
                # 发送识别结果
                yield f"data: {json.dumps({'type': 'recognition', 'text': recognized_text})}\n\n"
                
                # 第二步：准备AI聊天请求
                yield f"data: {json.dumps({'type': 'status', 'message': 'AI正在思考...'})}\n\n"
                
                chat_request = ChatRequest(
                    message=recognized_text,
                    history=[],  # 可以根据需要添加历史记录
                    temperature=0.7,
                    max_tokens=2048,
                    stream=True
                )
                
                # 第三步：流式AI对话 + 实时TTS
                text_buffer = ""
                chunk_counter = 0
                
                async for ai_chunk in lm_studio_service.chat_completion_stream(chat_request):
                    if ai_chunk.strip():
                        text_buffer += ai_chunk
                        
                        # 发送AI生成的文字片段
                        yield f"data: {json.dumps({'type': 'ai_text', 'content': ai_chunk})}\n\n"
                        
                        # 在进行TTS分块前，先清理思考标签
                        # 这是额外的安全措施，确保思考标签不会进入TTS系统
                        cleaned_buffer = clean_text_for_speech(text_buffer)
                        
                        # 检查是否可以进行TTS分块
                        chunks_to_synthesize = split_text_for_tts(cleaned_buffer)
                        
                        if chunks_to_synthesize:
                            # 对每个完整的文本块进行TTS
                            for chunk_text in chunks_to_synthesize:
                                try:
                                    # 再次确保文本清理（双重保险）
                                    final_clean_text = clean_text_for_speech(chunk_text)
                                    
                                    if not final_clean_text.strip():
                                        logger.info("跳过空的文本块")
                                        # 从原始缓冲区移除已处理的文本
                                        text_buffer = text_buffer.replace(chunk_text, "", 1).strip()
                                        continue
                                    
                                    # TTS合成
                                    audio_buffer = await synthesize_speech_chunk(final_clean_text)
                                    if audio_buffer:
                                        # 将音频数据编码为base64
                                        audio_base64 = base64.b64encode(audio_buffer).decode('utf-8')
                                        
                                        # 发送音频数据
                                        yield f"data: {json.dumps({'type': 'audio_chunk', 'audio': audio_base64, 'text': final_clean_text, 'chunk_id': chunk_counter})}\n\n"
                                        chunk_counter += 1
                                        
                                        logger.info(f"✅ 音频块 {chunk_counter-1} 发送成功: {len(audio_buffer)} 字节")
                                    else:
                                        logger.info(f"⚠️ 音频块TTS跳过: {repr(final_clean_text[:50])}")
                                        # 即使TTS失败，也发送一个状态消息
                                        yield f"data: {json.dumps({'type': 'tts_skip', 'message': '跳过无效文本块', 'text': final_clean_text})}\n\n"
                                    
                                    # 从原始缓冲区移除已处理的文本
                                    # 使用原始chunk_text进行移除，保持缓冲区状态正确
                                    text_buffer = text_buffer.replace(chunk_text, "", 1).strip()
                                        
                                except Exception as e:
                                    logger.error(f"❌ TTS合成异常: {e}, 文本: {repr(chunk_text[:100])}")
                                    yield f"data: {json.dumps({'type': 'tts_error', 'message': f'语音合成失败: {str(e)}', 'text': chunk_text[:100]})}\n\n"
                                    # 即使出错，也要移除已处理的文本，继续处理下一个块
                                    text_buffer = text_buffer.replace(chunk_text, "", 1).strip()
                
                # 处理剩余的文本缓冲区
                if text_buffer.strip():
                    try:
                        # 清理剩余文本
                        final_clean_text = clean_text_for_speech(text_buffer)
                        
                        if final_clean_text.strip():
                            logger.info(f"🔚 处理剩余文本: {repr(final_clean_text[:100])}")
                            audio_buffer = await synthesize_speech_chunk(final_clean_text)
                            if audio_buffer:
                                audio_base64 = base64.b64encode(audio_buffer).decode('utf-8')
                                yield f"data: {json.dumps({'type': 'audio_chunk', 'audio': audio_base64, 'text': final_clean_text, 'chunk_id': chunk_counter})}\n\n"
                                logger.info(f"✅ 最终音频块发送成功: {len(audio_buffer)} 字节")
                            else:
                                logger.info(f"⚠️ 最终文本块TTS跳过: {repr(final_clean_text[:50])}")
                                yield f"data: {json.dumps({'type': 'tts_skip', 'message': '跳过最终无效文本块', 'text': final_clean_text})}\n\n"
                        else:
                            logger.info("剩余文本清理后为空，跳过TTS合成")
                    except Exception as e:
                        logger.error(f"❌ 最终TTS合成失败: {e}, 原始文本: {repr(text_buffer[:200])}")
                        yield f"data: {json.dumps({'type': 'tts_error', 'message': f'最终语音合成失败: {str(e)}', 'text': text_buffer[:100]})}\n\n"
                
                # 发送完成信号
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"流式语音聊天处理失败: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_streaming_response(),
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