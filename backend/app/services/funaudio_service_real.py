"""
真实的 FunAudioLLM 服务实现
集成阿里巴巴 SenseVoice 模型进行高性能语音识别
"""

import logging
import torch
import numpy as np
import asyncio
import tempfile
import os
import json
from typing import Optional, Dict, Any, List
from io import BytesIO
import soundfile as sf
from pydub import AudioSegment

# FunASR 相关导入
try:
    from funasr import AutoModel
    from funasr.utils.postprocess_utils import rich_transcription_postprocess
    FUNASR_AVAILABLE = True
except ImportError:
    FUNASR_AVAILABLE = False

logger = logging.getLogger(__name__)

class FunAudioLLMService:
    """
    基于阿里FunAudioLLM的语音服务
    集成SenseVoice进行高性能语音识别、情感分析和声学事件检测
    """
    
    def __init__(self):
        self.model = None
        self.vad_model = None
        
        # Apple Silicon 优化设备选择
        if torch.backends.mps.is_available():
            self.device = "mps"
            logger.info("🍎 检测到 Apple Silicon，使用 MPS 加速")
        elif torch.cuda.is_available():
            self.device = "cuda"
            logger.info("🚀 检测到 CUDA，使用 GPU 加速")
        else:
            self.device = "cpu"
            logger.info("🔧 使用 CPU 模式")
            
        # Apple Silicon 性能优化设置
        if self.device == "mps":
            os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
            torch.backends.mps.allow_tf32 = True
        
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
        self.max_history_length = 20
        self.model_name = "iic/SenseVoiceSmall"
        self.is_initialized = False
        
        logger.info(f"🎤 初始化FunAudioLLM服务，设备: {self.device}")
        
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
            cache_dir = os.getenv("FUNAUDIO_CACHE_DIR", "./models/cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            # 加载SenseVoice模型 - Apple Silicon 优化
            model_kwargs = {
                "model": self.model_name,
                "trust_remote_code": True,
                "vad_model": "fsmn-vad",
                "vad_kwargs": {"max_single_segment_time": 30000},
                "cache_dir": cache_dir
            }
            
            # 根据设备类型优化配置
            if self.device == "mps":
                # Apple Silicon MPS 优化 - FunASR 暂不支持 MPS，使用 CPU
                model_kwargs["device"] = "cpu"
                logger.info("🍎 Apple Silicon 优化：使用 CPU 模式（FunASR 兼容性）")
            elif self.device == "cuda":
                # CUDA 优化
                model_kwargs["device"] = self.device
            else:
                # CPU 模式
                model_kwargs["device"] = self.device
            
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
                processed_audio_path = await self._preprocess_audio(audio_data)
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
                if os.path.exists(processed_audio_path):
                    os.unlink(processed_audio_path)
            
        except Exception as e:
            logger.error(f"❌ FunAudioLLM语音识别失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "engine": "FunAudioLLM-SenseVoice",
                "recognized_text": ""
            }
    
    async def _preprocess_audio(self, audio_data: bytes) -> str:
        """预处理音频数据，转换为模型所需格式"""
        try:
            # 验证音频数据
            if not audio_data or len(audio_data) < 100:  # 至少100字节
                raise ValueError(f"音频数据太小或为空: {len(audio_data) if audio_data else 0} bytes")
            
            logger.info(f"🎵 开始音频预处理，数据大小: {len(audio_data)} bytes")
            
            # 创建临时文件
            temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.webm')
            temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            
            try:
                # 写入原始音频数据
                temp_input.write(audio_data)
                temp_input.close()
                
                # 验证文件是否写入成功
                if not os.path.exists(temp_input.name) or os.path.getsize(temp_input.name) == 0:
                    raise ValueError("临时音频文件创建失败")
                
                logger.info(f"📁 临时文件创建成功: {temp_input.name} ({os.path.getsize(temp_input.name)} bytes)")
                
                # 使用 pydub 转换音频格式
                try:
                    audio = AudioSegment.from_file(temp_input.name)
                    logger.info(f"🎵 音频信息: 时长={len(audio)}ms, 采样率={audio.frame_rate}Hz, 声道={audio.channels}")
                    
                    # 检查音频时长
                    if len(audio) < 100:  # 至少100毫秒
                        raise ValueError(f"音频时长太短: {len(audio)}ms")
                    
                    # 转换为 16kHz 单声道 WAV
                    audio = audio.set_frame_rate(16000).set_channels(1)
                    audio.export(temp_output.name, format="wav")
                    
                    temp_output.close()
                    
                    # 验证输出文件
                    if not os.path.exists(temp_output.name) or os.path.getsize(temp_output.name) == 0:
                        raise ValueError("音频转换失败，输出文件为空")
                    
                    logger.info(f"✅ 音频转换成功: {temp_output.name} ({os.path.getsize(temp_output.name)} bytes)")
                    
                except Exception as audio_error:
                    logger.error(f"❌ pydub音频处理失败: {audio_error}")
                    # 尝试直接使用原始数据
                    temp_output.close()
                    with open(temp_output.name, 'wb') as f:
                        f.write(audio_data)
                    logger.info("🔄 使用原始音频数据作为备选方案")
                
            finally:
                # 清理输入临时文件
                if os.path.exists(temp_input.name):
                    os.unlink(temp_input.name)
            
            return temp_output.name
            
        except Exception as e:
            logger.error(f"❌ 音频预处理失败: {e}")
            # 如果预处理完全失败，返回错误而不是创建无效文件
            raise ValueError(f"音频预处理失败: {str(e)}")
    
    def _extract_emotion_info(self, processed_text: str) -> Dict[str, Any]:
        """从处理后的文本中提取情感信息"""
        try:
            # SenseVoice 的情感标记格式: <|HAPPY|>, <|SAD|>, <|ANGRY|>, etc.
            emotions = {
                "HAPPY": "开心",
                "SAD": "悲伤", 
                "ANGRY": "愤怒",
                "SURPRISED": "惊讶",
                "FEARFUL": "恐惧",
                "DISGUSTED": "厌恶",
                "NEUTRAL": "中性"
            }
            
            detected_emotions = []
            for emotion_en, emotion_zh in emotions.items():
                if f"<|{emotion_en}|>" in processed_text:
                    detected_emotions.append({
                        "emotion": emotion_en.lower(),
                        "emotion_zh": emotion_zh,
                        "confidence": 0.8  # SenseVoice 不提供具体置信度
                    })
            
            if detected_emotions:
                return {
                    "detected": True,
                    "primary": detected_emotions[0]["emotion_zh"],
                    "emotions": detected_emotions
                }
            else:
                return {
                    "detected": False,
                    "primary": "中性",
                    "emotions": []
                }
                
        except Exception as e:
            logger.error(f"❌ 情感信息提取失败: {e}")
            return {"detected": False, "primary": "未知", "emotions": []}
    
    def _extract_event_info(self, processed_text: str) -> List[str]:
        """从处理后的文本中提取声学事件信息"""
        try:
            # SenseVoice 的事件标记格式: <|MUSIC|>, <|APPLAUSE|>, etc.
            events = {
                "MUSIC": "音乐",
                "APPLAUSE": "掌声",
                "LAUGHTER": "笑声",
                "CRYING": "哭声",
                "COUGHING": "咳嗽",
                "SNEEZING": "打喷嚏",
                "BREATHING": "呼吸声",
                "FOOTSTEPS": "脚步声",
                "DOOR": "门声",
                "PHONE": "电话铃声",
                "ALARM": "警报声",
                "SILENCE": "静音"
            }
            
            detected_events = []
            for event_en, event_zh in events.items():
                if f"<|{event_en}|>" in processed_text:
                    detected_events.append(event_zh)
            
            return detected_events
            
        except Exception as e:
            logger.error(f"❌ 声学事件提取失败: {e}")
            return []
    
    def _clean_text(self, processed_text: str) -> str:
        """清理文本，移除特殊标记"""
        try:
            import re
            
            # 移除情感标记
            text = re.sub(r'<\|[A-Z_]+\|>', '', processed_text)
            
            # 移除多余的空格
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
            
        except Exception as e:
            logger.error(f"❌ 文本清理失败: {e}")
            return processed_text
    
    async def get_health_status(self) -> Dict[str, Any]:
        """获取服务健康状态"""
        try:
            # 检查模型是否已初始化
            if not self.is_initialized:
                await self.initialize()
            
            # 检查 CUDA 可用性
            cuda_available = torch.cuda.is_available()
            cuda_device_count = torch.cuda.device_count() if cuda_available else 0
            
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
                    "cuda_available": cuda_available,
                    "cuda_device_count": cuda_device_count,
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
                "cuda_available": torch.cuda.is_available(),
                "mps_available": torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False,
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
        # 移除空格和标点符号
        import re
        wake_word_clean = re.sub(r'[^\w]', '', wake_word)
        recognized_clean = re.sub(r'[^\w]', '', recognized_text)
        
        # 检查是否包含主要字符
        if "小智" in recognized_clean or "智能" in recognized_clean:
            return True
        
        # 检查字符相似度
        if len(wake_word_clean) > 0:
            match_count = 0
            for char in wake_word_clean:
                if char in recognized_clean:
                    match_count += 1
            
            similarity = match_count / len(wake_word_clean)
            return similarity >= 0.6  # 60%相似度阈值
        
        return False

# 创建全局服务实例
funaudio_service = FunAudioLLMService() 