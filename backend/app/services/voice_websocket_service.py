"""
语音WebSocket连接管理服务

提供WebSocket连接管理、流式音频处理等功能
"""

from fastapi import WebSocket
from typing import Dict, List
import logging
import asyncio
import json
import base64
from app.services.funaudio_service_real import FunAudioLLMService
from app.services.lm_studio_service import lm_studio_service
from app.models.schemas import ChatRequest
from app.utils import clean_text_for_speech, synthesize_speech_chunk

logger = logging.getLogger(__name__)

class VoiceConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_configs: Dict[WebSocket, Dict] = {}
        self.connection_sessions: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket):
        """建立WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        # 为每个连接生成唯一的会话ID
        session_id = f"ws-session-{len(self.active_connections)}-{asyncio.get_event_loop().time()}"
        self.connection_sessions[websocket] = session_id
        logger.info(f"🔌 新的语音WebSocket连接: {len(self.active_connections)}个活跃连接, 会话ID: {session_id}")
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_configs:
            del self.connection_configs[websocket]
        if websocket in self.connection_sessions:
            del self.connection_sessions[websocket]
        logger.info(f"🔌 语音WebSocket连接断开: {len(self.active_connections)}个活跃连接")
    
    def set_config(self, websocket: WebSocket, config: Dict):
        """设置连接配置"""
        self.connection_configs[websocket] = config
    
    def get_config(self, websocket: WebSocket) -> Dict:
        """获取连接配置"""
        return self.connection_configs.get(websocket, {})
    
    def get_session_id(self, websocket: WebSocket) -> str:
        """获取会话ID"""
        return self.connection_sessions.get(websocket, "default")

class VoiceWebSocketService:
    """语音WebSocket服务"""
    
    def __init__(self):
        self.funaudio_service = FunAudioLLMService()
        self.connection_manager = VoiceConnectionManager()
    
    async def handle_stream_audio_data(self, websocket: WebSocket, audio_data: bytes):
        """处理流式音频数据"""
        try:
            # 获取配置
            config = self.connection_manager.get_config(websocket)
            session_id = config.get("session_id") or self.connection_manager.get_session_id(websocket)
            language = config.get("language", "auto")
            
            logger.info(f"🎵 接收到流式音频数据: {len(audio_data)} 字节")
            
            # 发送处理状态
            await websocket.send_json({
                "type": "status",
                "status": "processing",
                "message": "正在处理流式音频数据",
                "audio_size": len(audio_data),
                "timestamp": asyncio.get_event_loop().time()
            })
            
            if len(audio_data) == 0:
                raise ValueError("音频数据为空")
            
            # 调用FunAudioLLM进行语音识别
            recognition_result = await self.funaudio_service.voice_recognition(
                audio_data=audio_data,
                language=language
            )
            
            if not recognition_result["success"]:
                await websocket.send_json({
                    "type": "error",
                    "error": "语音识别失败",
                    "details": recognition_result.get("error", "未知错误"),
                    "timestamp": asyncio.get_event_loop().time()
                })
                return
            
            recognized_text = recognition_result["recognized_text"]
            
            if not recognized_text.strip():
                await websocket.send_json({
                    "type": "recognition_result",
                    "success": False,
                    "message": "未识别到有效语音内容",
                    "timestamp": asyncio.get_event_loop().time()
                })
                return
            
            # 发送识别结果
            await websocket.send_json({
                "type": "recognition_result",
                "success": True,
                "recognized_text": recognized_text,
                "emotion": recognition_result.get("emotion", {}),
                "timestamp": asyncio.get_event_loop().time()
            })
            
            # 开始流式AI对话处理
            await self.process_stream_ai_response(websocket, recognized_text, session_id)
            
        except Exception as e:
            logger.error(f"❌ 处理流式音频数据失败: {e}")
            await websocket.send_json({
                "type": "error",
                "error": f"处理音频数据失败: {str(e)}",
                "timestamp": asyncio.get_event_loop().time()
            })

    async def process_stream_ai_response(self, websocket: WebSocket, user_text: str, session_id: str):
        """处理流式AI响应和TTS合成"""
        try:
            # 准备AI聊天请求
            await websocket.send_json({
                "type": "ai_thinking",
                "message": "AI正在思考回复...",
                "timestamp": asyncio.get_event_loop().time()
            })
            
            chat_request = ChatRequest(
                message=user_text,
                history=[],  # 可以根据需要添加历史记录
                temperature=0.7,
                max_tokens=2048,
                stream=True
            )
            
            # 流式AI对话 + 实时TTS
            text_buffer = ""
            processed_text_length = 0
            chunk_counter = 0
            
            async for ai_chunk in lm_studio_service.chat_completion_stream(chat_request):
                if ai_chunk.strip():
                    text_buffer += ai_chunk
                    
                    # 发送AI生成的文字片段
                    await websocket.send_json({
                        "type": "ai_text_chunk",
                        "content": ai_chunk,
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    
                    # 清理思考标签
                    cleaned_buffer = clean_text_for_speech(text_buffer)
                    
                    # 只处理新增的部分，避免重复处理
                    if len(cleaned_buffer) > processed_text_length:
                        new_text = cleaned_buffer[processed_text_length:]
                        
                        # 检查是否可以形成完整句子进行TTS
                        sentence_endings = ['。', '！', '？', '.', '!', '?', '\n']
                        last_sentence_end = -1
                        
                        for i, char in enumerate(new_text):
                            if char in sentence_endings:
                                last_sentence_end = i
                        
                        # 如果找到完整句子，进行TTS合成
                        if last_sentence_end >= 0:
                            sentence_to_process = new_text[:last_sentence_end + 1].strip()
                            
                            if sentence_to_process and len(sentence_to_process) >= 3:
                                try:
                                    logger.info(f"🎵 TTS处理句子: {repr(sentence_to_process[:50])}")
                                    
                                    # TTS合成
                                    audio_buffer = await synthesize_speech_chunk(sentence_to_process)
                                    if audio_buffer:
                                        # 直接发送二进制音频数据
                                        await websocket.send_json({
                                            "type": "audio_chunk_info",
                                            "text": sentence_to_process,
                                            "chunk_id": chunk_counter,
                                            "audio_size": len(audio_buffer),
                                            "timestamp": asyncio.get_event_loop().time()
                                        })
                                        
                                        # 发送二进制音频数据
                                        await websocket.send_bytes(audio_buffer)
                                        chunk_counter += 1
                                        
                                except Exception as e:
                                    logger.error(f"❌ 流式TTS合成异常: {e}")
                                    await websocket.send_json({
                                        "type": "tts_error",
                                        "message": f"语音合成失败: {str(e)}",
                                        "text": sentence_to_process[:100],
                                        "timestamp": asyncio.get_event_loop().time()
                                    })
                            
                            processed_text_length += last_sentence_end + 1
                        
                        # 处理长文本块
                        elif len(new_text) > 100:
                            split_chars = [' ', '，', ',', '、', '；', ';']
                            best_split = -1
                            
                            for i in range(min(80, len(new_text) - 1), 20, -1):
                                if new_text[i] in split_chars:
                                    best_split = i
                                    break
                            
                            if best_split > 20:
                                chunk_to_process = new_text[:best_split + 1].strip()
                                
                                if chunk_to_process:
                                    try:
                                        audio_buffer = await synthesize_speech_chunk(chunk_to_process)
                                        if audio_buffer:
                                            await websocket.send_json({
                                                "type": "audio_chunk_info",
                                                "text": chunk_to_process,
                                                "chunk_id": chunk_counter,
                                                "audio_size": len(audio_buffer),
                                                "timestamp": asyncio.get_event_loop().time()
                                            })
                                            await websocket.send_bytes(audio_buffer)
                                            chunk_counter += 1
                                            
                                    except Exception as e:
                                        logger.error(f"❌ 长文本TTS异常: {e}")
                                
                                processed_text_length += best_split + 1
            
            # 处理剩余文本
            if text_buffer.strip():
                cleaned_buffer = clean_text_for_speech(text_buffer)
                
                if len(cleaned_buffer) > processed_text_length:
                    remaining_text = cleaned_buffer[processed_text_length:].strip()
                    
                    if remaining_text and len(remaining_text) >= 3:
                        try:
                            audio_buffer = await synthesize_speech_chunk(remaining_text)
                            if audio_buffer:
                                await websocket.send_json({
                                    "type": "audio_chunk_info",
                                    "text": remaining_text,
                                    "chunk_id": chunk_counter,
                                    "audio_size": len(audio_buffer),
                                    "is_final": True,
                                    "timestamp": asyncio.get_event_loop().time()
                                })
                                await websocket.send_bytes(audio_buffer)
                                
                        except Exception as e:
                            logger.error(f"❌ 最终TTS合成失败: {e}")
            
            # 发送完成信号
            await websocket.send_json({
                "type": "stream_complete",
                "full_response": text_buffer.strip(),
                "total_chunks": chunk_counter,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            # 恢复监听状态
            await websocket.send_json({
                "type": "status",
                "status": "listening",
                "message": "等待下一次语音输入",
                "timestamp": asyncio.get_event_loop().time()
            })
            
        except Exception as e:
            logger.error(f"❌ 流式AI响应处理失败: {e}")
            await websocket.send_json({
                "type": "error",
                "error": f"AI响应处理失败: {str(e)}",
                "timestamp": asyncio.get_event_loop().time()
            })

# 创建全局服务实例
voice_websocket_service = VoiceWebSocketService() 