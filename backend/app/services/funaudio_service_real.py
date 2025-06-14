"""
真实的 FunAudioLLM 服务实现
集成阿里巴巴 SenseVoice 模型进行高性能语音识别
"""

import logging
import torch
import numpy as np
import asyncio
import json
from typing import Optional, Dict, Any, List
from io import BytesIO
import soundfile as sf

# FunASR 相关导入
try:
    from funasr import AutoModel
    from funasr.utils.postprocess_utils import rich_transcription_postprocess
    FUNASR_AVAILABLE = True
except ImportError:
    FUNASR_AVAILABLE = False

# 导入工具模块
from app.utils import (
    DeviceManager, AudioProcessor, EmotionAnalyzer, 
    MessageProcessor, get_timestamp
)

logger = logging.getLogger(__name__)

class FunAudioLLMService:
    """
    基于阿里FunAudioLLM的语音服务
    集成SenseVoice进行高性能语音识别、情感分析和声学事件检测
    """
    
    def __init__(self):
        self.model = None
        self.vad_model = None
        
        # 使用DeviceManager获取最优设备
        self.device = DeviceManager.get_optimal_device()
        
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
        self.max_history_length = 20
        self.model_name = "iic/SenseVoiceSmall"
        self.is_initialized = False
        
        logger.info(f"🎤 初始化FunAudioLLM服务，设备: {self.device}")
        
        # 设备优化配置
        optimization_result = DeviceManager.setup_device_optimization(self.device)
        if optimization_result["success"]:
            logger.info(f"✅ 设备优化已启用: {optimization_result['optimizations']}")
        else:
            logger.warning(f"⚠️ 设备优化配置失败: {optimization_result.get('error', '未知错误')}")
        
        if not FUNASR_AVAILABLE:
            logger.warning("⚠️ FunASR 未安装，请运行: pip install funasr")
        
    async def initialize(self):
        """初始化SenseVoice模型"""
        if self.is_initialized:
            return True
            
        if not FUNASR_AVAILABLE:
            logger.error("❌ FunASR 未安装，无法初始化模型")
            return False
            
        try:
            logger.info("📥 加载SenseVoice模型...")
            
            # 设置模型缓存目录
            cache_dir = DeviceManager.get_cache_dir("FUNAUDIO_CACHE_DIR", "./models/cache")
            
            # 加载SenseVoice模型 - Apple Silicon 优化
            model_kwargs = {
                "model": self.model_name,
                "trust_remote_code": True,
                "vad_model": "fsmn-vad",
                "vad_kwargs": {"max_single_segment_time": 30000},
                "cache_dir": cache_dir
            }
            
            # 根据设备类型优化配置
            device_config = DeviceManager.get_model_device_config(self.device, "funasr")
            model_kwargs["device"] = device_config["device"]
            
            if device_config.get("fallback_reason"):
                logger.info(f"🔄 设备回退: {device_config['fallback_reason']}")
            
            self.model = AutoModel(**model_kwargs)
            
            self.is_initialized = True
            logger.info("✅ FunAudioLLM SenseVoice模型加载成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ FunAudioLLM模型加载失败: {e}")
            self.is_initialized = False
            return False
    
    async def voice_recognition(self, audio_data: bytes, language: str = "auto") -> Dict[str, Any]:
        """
        高性能语音识别，支持情感分析和声学事件检测
        """
        try:
            if not self.is_initialized:
                success = await self.initialize()
                if not success:
                    return {
                        "success": False,
                        "error": "FunAudioLLM模型未初始化",
                        "engine": "FunAudioLLM-SenseVoice",
                        "recognized_text": ""
                    }
            
            logger.info("🎯 开始FunAudioLLM语音识别...")
            
            # 预处理音频数据
            try:
                processed_audio_path = await AudioProcessor.preprocess_audio(audio_data)
            except ValueError as ve:
                # 音频预处理失败，返回特定错误
                logger.error(f"❌ 音频预处理失败: {ve}")
                return {
                    "success": False,
                    "error": "未识别到有效语音内容",
                    "engine": "FunAudioLLM-SenseVoice",
                    "recognized_text": ""
                }
            
            try:
                # 使用SenseVoice进行识别
                result = self.model.generate(
                    input=processed_audio_path,
                    cache={},
                    language=language,  # "auto", "zh", "en", "yue", "ja", "ko"
                    use_itn=True,  # 启用逆文本标准化
                    batch_size_s=60,
                    merge_vad=True,  # 合并VAD结果
                    merge_length_s=15,
                )
                
                if not result or len(result) == 0:
                    return {
                        "success": False,
                        "error": "语音识别返回空结果",
                        "engine": "FunAudioLLM-SenseVoice",
                        "recognized_text": ""
                    }
                
                # 处理识别结果
                raw_text = result[0]["text"]
                processed_text = rich_transcription_postprocess(raw_text)
                
                # 解析情感和事件信息
                emotion_info = self._extract_emotion_info(processed_text)
                event_info = self._extract_event_info(processed_text)
                clean_text = self._clean_text(processed_text)
                
                # 获取置信度
                confidence = result[0].get("confidence", 1.0)
                
                logger.info(f"✅ 语音识别成功: {clean_text[:50]}...")
                
                return {
                    "success": True,
                    "recognized_text": clean_text,
                    "raw_text": raw_text,
                    "processed_text": processed_text,
                    "emotion": emotion_info,
                    "events": event_info,
                    "language": language,
                    "engine": "FunAudioLLM-SenseVoice",
                    "confidence": confidence,
                    "model_name": self.model_name,
                    "device": self.device
                }
                
            finally:
                # 清理临时文件
                AudioProcessor.cleanup_temp_file(processed_audio_path)
            
        except Exception as e:
            logger.error(f"❌ FunAudioLLM语音识别失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "engine": "FunAudioLLM-SenseVoice",
                "recognized_text": ""
            }
    

    
    def _extract_emotion_info(self, processed_text: str) -> Dict[str, Any]:
        """从处理后的文本中提取情感信息"""
        return EmotionAnalyzer.extract_sensevoice_emotion_info(processed_text)
    
    def _extract_event_info(self, processed_text: str) -> List[str]:
        """从处理后的文本中提取声学事件信息"""
        return EmotionAnalyzer.extract_sensevoice_event_info(processed_text)
    
    def _clean_text(self, processed_text: str) -> str:
        """清理文本，移除特殊标记"""
        return EmotionAnalyzer.clean_sensevoice_text(processed_text)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """获取服务健康状态"""
        try:
            # 检查模型是否已初始化
            if not self.is_initialized:
                await self.initialize()
            
            # 获取设备信息
            device_info = DeviceManager.get_device_info()
            
            # 检查模型状态
            model_loaded = self.model is not None
            
            return {
                "available": model_loaded and FUNASR_AVAILABLE,
                "model_name": f"FunAudioLLM-{self.model_name}",
                "device": self.device,
                "audio_model": {
                    "name": "SenseVoice",
                    "available": model_loaded,
                    "device": self.device,
                    "model_path": self.model_name
                },
                "chat_model": {
                    "name": "LM Studio",
                    "available": True,  # 假设 LM Studio 可用
                    "endpoint": "http://localhost:1234"
                },
                "features": [
                    "高性能语音识别 (比Whisper快15倍)",
                    "情感识别",
                    "声学事件检测", 
                    "50+语言支持",
                    "实时VAD语音活动检测",
                    "逆文本标准化(ITN)"
                ],
                "system_info": {
                    "funasr_available": FUNASR_AVAILABLE,
                    **device_info,
                    "torch_version": torch.__version__
                },
                "message": "FunAudioLLM SenseVoice 服务运行正常" if model_loaded else "模型未加载",
                "lm_studio_available": True  # 这里可以添加实际的 LM Studio 检查
            }
            
        except Exception as e:
            logger.error(f"❌ 获取健康状态失败: {e}")
            return {
                "available": False,
                "model_name": "FunAudioLLM-Error",
                "device": "unknown",
                "audio_model": {"name": "SenseVoice", "available": False},
                "chat_model": {"name": "LM Studio", "available": False},
                "features": [],
                "message": f"服务异常: {str(e)}",
                "lm_studio_available": False
            }
    
    async def voice_chat(self, audio_data: bytes, session_id: str = "default", language: str = "auto") -> Dict[str, Any]:
        """完整的语音聊天流程：语音识别 + AI对话"""
        try:
            # 1. 语音识别
            recognition_result = await self.voice_recognition(audio_data, language)
            
            if not recognition_result["success"]:
                return {
                    "success": False,
                    "error": f"语音识别失败: {recognition_result['error']}",
                    "recognized_text": "",
                    "response": ""
                }
            
            recognized_text = recognition_result["recognized_text"]
            
            if not recognized_text.strip():
                return {
                    "success": False,
                    "error": "未识别到有效语音内容",
                    "recognized_text": "",
                    "response": ""
                }
            
            # 2. 调用 LM Studio 进行对话
            try:
                from app.services.lm_studio_service import lm_studio_service
                from app.models.schemas import ChatRequest, ChatMessage, MessageType
                
                logger.info(f"🤖 开始AI对话处理，识别文本: {recognized_text}")
                
                # 获取对话历史
                history = self.conversation_history.get(session_id, [])
                logger.info(f"📚 对话历史长度: {len(history)}")
                
                # 转换历史记录格式
                chat_history = []
                for msg in history[-self.max_history_length:]:
                    chat_history.append(ChatMessage(
                        content=msg["content"],
                        message_type=MessageType.TEXT,
                        is_user=(msg["role"] == "user")
                    ))
                
                # 构建聊天请求
                chat_request = ChatRequest(
                    message=recognized_text,
                    history=chat_history,
                    temperature=0.7,
                    max_tokens=500
                )
                
                logger.info("🤖 调用LM Studio进行AI对话...")
                logger.info(f"📝 请求消息: {recognized_text}")
                logger.info(f"📊 历史消息数: {len(chat_history)}")
                
                # 直接调用LM Studio服务
                ai_response = await lm_studio_service.chat_completion(chat_request)
                
                logger.info(f"✅ LM Studio响应: {ai_response[:100]}...")
                
                # 更新对话历史
                if session_id not in self.conversation_history:
                    self.conversation_history[session_id] = []
                
                self.conversation_history[session_id].extend([
                    {"role": "user", "content": recognized_text},
                    {"role": "assistant", "content": ai_response}
                ])
                
                # 限制历史长度
                if len(self.conversation_history[session_id]) > self.max_history_length * 2:
                    self.conversation_history[session_id] = self.conversation_history[session_id][-self.max_history_length * 2:]
                
                logger.info(f"✅ AI对话成功: {ai_response[:50]}...")
                
                return {
                    "success": True,
                    "recognized_text": recognized_text,
                    "response": ai_response,
                    "emotion": recognition_result.get("emotion"),
                    "events": recognition_result.get("events"),
                    "confidence": recognition_result.get("confidence"),
                    "engine": "FunAudioLLM-SenseVoice",
                    "session_id": session_id
                }
                
            except Exception as e:
                logger.error(f"❌ AI对话失败: {e}")
                logger.error(f"❌ 错误类型: {type(e).__name__}")
                logger.error(f"❌ 错误详情: {str(e)}")
                import traceback
                logger.error(f"❌ 错误堆栈: {traceback.format_exc()}")
                return {
                    "success": True,  # 语音识别成功
                    "recognized_text": recognized_text,
                    "response": f"语音识别成功，但AI对话服务异常: {str(e)}",
                    "emotion": recognition_result.get("emotion"),
                    "events": recognition_result.get("events"),
                    "confidence": recognition_result.get("confidence"),
                    "engine": "FunAudioLLM-SenseVoice"
                }
            
        except Exception as e:
            logger.error(f"❌ 语音聊天失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "recognized_text": "",
                "response": ""
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查方法"""
        try:
            await self.initialize()
            
            # 检查LM Studio状态
            lm_studio_available = False
            try:
                from app.services.lm_studio_service import lm_studio_service
                lm_studio_available = await lm_studio_service.health_check()
            except Exception as e:
                logger.warning(f"LM Studio健康检查失败: {e}")
            
            return {
                "available": True,
                "model_name": self.model_name,
                "device": self.device,
                **DeviceManager.get_device_info(),
                "lm_studio_available": lm_studio_available,
                "audio_model": {
                    "name": "SenseVoice",
                    "available": self.is_initialized,
                    "type": "speech_recognition"
                },
                "chat_model": {
                    "name": "LM Studio Chat Model", 
                    "available": lm_studio_available,
                    "type": "chat_completion"
                },
                "features": [
                    "高性能语音识别", 
                    "情感识别", 
                    "声学事件检测",
                    "多语言支持",
                    "连续对话",
                    "多会话管理"
                ],
                "supported_languages": ["auto", "zh", "en", "yue", "ja", "ko", "fr", "es", "de"],
                "performance": {
                    "speed": "比Whisper快15倍",
                    "accuracy": "高精度识别"
                },
                "message": f"FunAudioLLM服务正常 (设备: {self.device}, LM Studio: {'可用' if lm_studio_available else '不可用'})"
            }
        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            return {
                "available": False,
                "error": str(e),
                "message": "FunAudioLLM服务异常"
            }
    
    async def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话摘要"""
        if session_id not in self.conversation_history:
            return {
                "session_id": session_id,
                "total_messages": 0,
                "messages": []
            }
        
        history = self.conversation_history[session_id]
        return {
            "session_id": session_id,
            "total_messages": len(history),
            "messages": history[-10:]  # 返回最近10条消息
        }
    
    async def clear_conversation_history(self, session_id: str) -> bool:
        """清除指定会话的对话历史"""
        try:
            if session_id in self.conversation_history:
                del self.conversation_history[session_id]
                logger.info(f"✅ 已清除会话 {session_id} 的对话历史")
            else:
                logger.info(f"ℹ️ 会话 {session_id} 不存在对话历史")
            return True
        except Exception as e:
            logger.error(f"❌ 清除会话历史失败: {e}")
            return False
    
    async def wake_word_detection(self, audio_data: bytes, wake_words: List[str] = None) -> Dict[str, Any]:
        """
        唤醒词检测功能
        检测音频中是否包含指定的唤醒词（如"小智小智"）
        """
        if wake_words is None:
            wake_words = ["小智小智", "小智", "智能助手", "hey xiaozhi"]
        
        try:
            if not self.is_initialized:
                success = await self.initialize()
                if not success:
                    return {
                        "success": False,
                        "wake_word_detected": False,
                        "error": "FunAudioLLM模型未初始化",
                        "confidence": 0.0
                    }
            
            logger.info("🎯 开始唤醒词检测...")
            
            # 使用快速语音识别检测唤醒词
            recognition_result = await self.voice_recognition(audio_data, language="zh")
            
            if not recognition_result["success"]:
                return {
                    "success": False,
                    "wake_word_detected": False,
                    "error": recognition_result["error"],
                    "confidence": 0.0
                }
            
            recognized_text = recognition_result["recognized_text"].lower()
            confidence = recognition_result.get("confidence", 0.0)
            
            # 检测唤醒词
            wake_word_detected = False
            detected_word = ""
            
            for wake_word in wake_words:
                if wake_word.lower() in recognized_text:
                    wake_word_detected = True
                    detected_word = wake_word
                    logger.info(f"✅ 检测到唤醒词: {wake_word}")
                    break
            
            # 提高唤醒词检测的准确性
            if not wake_word_detected:
                # 模糊匹配，处理语音识别的不准确性
                for wake_word in wake_words:
                    # 检查相似度
                    if self._fuzzy_match(wake_word.lower(), recognized_text):
                        wake_word_detected = True
                        detected_word = wake_word
                        logger.info(f"✅ 模糊匹配检测到唤醒词: {wake_word}")
                        break
            
            return {
                "success": True,
                "wake_word_detected": wake_word_detected,
                "detected_word": detected_word,
                "recognized_text": recognition_result["recognized_text"],
                "confidence": confidence,
                "engine": "FunAudioLLM-SenseVoice",
                "emotion": recognition_result.get("emotion"),
                "events": recognition_result.get("events")
            }
            
        except Exception as e:
            logger.error(f"❌ 唤醒词检测失败: {e}")
            return {
                "success": False,
                "wake_word_detected": False,
                "error": str(e),
                "confidence": 0.0
            }
    
    def _fuzzy_match(self, wake_word: str, recognized_text: str) -> bool:
        """
        模糊匹配唤醒词，处理语音识别的不准确性
        """
        return EmotionAnalyzer.fuzzy_match_wake_word(wake_word, recognized_text)

# 创建全局服务实例
funaudio_service = FunAudioLLMService() 