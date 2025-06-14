import logging
import torch
import numpy as np
from typing import Optional, Dict, Any, List
from io import BytesIO
import asyncio
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

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
    官方仓库：https://github.com/FunAudioLLM
    """
    
    def __init__(self):
        self.model = None
        self.device = DeviceManager.get_optimal_device()
        
        # 对话历史管理
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
        self.max_history_length = 20
        
        logger.info(f"🎤 初始化FunAudioLLM服务，设备: {self.device}")
        
        # 设备优化配置
        optimization_result = DeviceManager.setup_device_optimization(self.device)
        if optimization_result["success"]:
            logger.info(f"✅ 设备优化已启用: {optimization_result['optimizations']}")
        else:
            logger.warning(f"⚠️ 设备优化配置失败: {optimization_result.get('error', '未知错误')}")
        
    async def initialize(self):
        """初始化SenseVoice模型"""
        try:
            logger.info("📥 加载SenseVoice模型...")
            
            # 加载SenseVoice模型
            self.model = AutoModel(
                model="iic/SenseVoiceSmall",
                trust_remote_code=True,
                vad_model="fsmn-vad",
                vad_kwargs={"max_single_segment_time": 30000},
                device=self.device,
            )
            
            logger.info("✅ FunAudioLLM SenseVoice模型加载成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ FunAudioLLM模型加载失败: {e}")
            return False
    
    def _save_audio_temp(self, audio_data: bytes) -> str:
        """保存音频数据到临时文件"""
        return AudioProcessor.save_audio_temp(audio_data)
    
    async def voice_recognition(self, audio_data: bytes, language: str = "auto") -> Dict[str, Any]:
        """
        高性能语音识别，支持情感分析和声学事件检测
        """
        try:
            if not self.model:
                await self.initialize()
            
            logger.info("🎯 开始FunAudioLLM语音识别...")
            
            # 保存音频到临时文件
            temp_audio_path = self._save_audio_temp(audio_data)
            
            try:
                # 使用SenseVoice进行识别
                result = self.model.generate(
                    input=temp_audio_path,
                    cache={},
                    language=language,  # "auto", "zh", "en", "yue", "ja", "ko", "nospeech"
                    use_itn=True,
                    batch_size_s=60,
                    merge_vad=True,
                    merge_length_s=15,
                )
                
                # 处理识别结果，提取文本和情感信息
                raw_text = result[0]["text"]
                processed_text = rich_transcription_postprocess(raw_text)
                
                # 解析情感和事件信息
                emotion_info = self._extract_emotion_info(processed_text)
                event_info = self._extract_event_info(processed_text)
                clean_text = self._clean_text(processed_text)
                
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
                    "confidence": result[0].get("confidence", 1.0)
                }
                
            finally:
                # 清理临时文件
                AudioProcessor.cleanup_temp_file(temp_audio_path)
            
        except Exception as e:
            logger.error(f"❌ FunAudioLLM语音识别失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "engine": "FunAudioLLM-SenseVoice",
                "recognized_text": ""
            }
    
    async def voice_chat(self, audio_data: bytes, session_id: str = "default", language: str = "auto") -> Dict[str, Any]:
        """
        语音聊天模式 - 结合语音识别和对话生成
        """
        try:
            logger.info(f"🗣️ 开始FunAudioLLM语音聊天，会话ID: {session_id}")
            
            # 首先进行语音识别
            recognition_result = await self.voice_recognition(audio_data, language)
            
            if not recognition_result["success"]:
                return recognition_result
            
            recognized_text = recognition_result["recognized_text"]
            emotion_info = recognition_result["emotion"]
            
            # 获取或初始化对话历史
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            
            # 构建包含情感信息的用户消息
            user_message = MessageProcessor.format_user_message(
                recognized_text, emotion_info, get_timestamp()
            )
            
            # 添加到历史
            self.conversation_history[session_id].append(user_message)
            
            # 这里可以集成其他LLM进行对话生成
            # 暂时返回识别结果和简单回复
            response_text = self._generate_response(recognized_text, emotion_info)
            
            # 添加AI回复到历史
            ai_message = MessageProcessor.format_assistant_message(
                response_text, get_timestamp()
            )
            self.conversation_history[session_id].append(ai_message)
            
            # 限制历史长度
            self.conversation_history[session_id] = MessageProcessor.limit_conversation_history(
                self.conversation_history[session_id], self.max_history_length
            )
            
            logger.info(f"✅ FunAudioLLM语音聊天成功")
            
            return {
                "success": True,
                "recognized_text": recognized_text,
                "response": response_text,
                "emotion": emotion_info,
                "events": recognition_result["events"],
                "session_id": session_id,
                "history_length": len(self.conversation_history[session_id]) // 2,
                "engine": "FunAudioLLM-SenseVoice",
                "language": language
            }
            
        except Exception as e:
            logger.error(f"❌ FunAudioLLM语音聊天失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "engine": "FunAudioLLM-SenseVoice",
                "response": "抱歉，语音处理出现问题。请稍后重试。"
            }
    
    def _extract_emotion_info(self, text: str) -> Dict[str, Any]:
        """提取情感信息"""
        return EmotionAnalyzer.extract_emotion_info(text)
    
    def _extract_event_info(self, text: str) -> List[str]:
        """提取声学事件信息"""
        return EmotionAnalyzer.extract_event_info(text)
    
    def _clean_text(self, text: str) -> str:
        """清理文本，移除情感和事件标记"""
        return EmotionAnalyzer.clean_text(text)
    
    def _generate_response(self, user_text: str, emotion_info: Dict[str, Any]) -> str:
        """生成简单的回复（可扩展接入其他LLM）"""
        primary_emotion = emotion_info.get("primary", "neutral")
        
        if primary_emotion == "happy":
            return f"很高兴听到你开心的话语！你说：「{user_text}」"
        elif primary_emotion == "sad":
            return f"我能感受到你的情绪，让我来帮助你。你说：「{user_text}」"
        elif primary_emotion == "angry":
            return f"我理解你的感受，让我们冷静地讨论一下。你说：「{user_text}」" 
        else:
            return f"我听到你说：「{user_text}」。有什么我可以帮助你的吗？"
    

    
    async def clear_conversation_history(self, session_id: str = "default") -> bool:
        """清除指定会话的对话历史"""
        try:
            if session_id in self.conversation_history:
                del self.conversation_history[session_id]
                logger.info(f"✅ 已清除FunAudioLLM会话 {session_id} 的对话历史")
            return True
        except Exception as e:
            logger.error(f"❌ 清除对话历史失败: {e}")
            return False
    
    async def get_conversation_summary(self, session_id: str = "default") -> Dict[str, Any]:
        """获取对话摘要信息"""
        try:
            history = self.conversation_history.get(session_id, [])
            user_messages = [msg for msg in history if msg["role"] == "user"]
            assistant_messages = [msg for msg in history if msg["role"] == "assistant"]
            
            # 统计情感分布
            emotions = [msg.get("emotion", {}).get("primary", "neutral") for msg in user_messages if "emotion" in msg]
            emotion_stats = {emotion: emotions.count(emotion) for emotion in set(emotions)} if emotions else {}
            
            return {
                "session_id": session_id,
                "total_messages": len(history),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "conversation_rounds": len(user_messages),
                "emotion_stats": emotion_stats,
                "has_history": len(history) > 0,
                "last_user_message": user_messages[-1]["content"] if user_messages else None,
                "last_assistant_message": assistant_messages[-1]["content"] if assistant_messages else None,
                "engine": "FunAudioLLM-SenseVoice"
            }
        except Exception as e:
            logger.error(f"❌ 获取对话摘要失败: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """检查服务健康状态"""
        try:
            if not self.model:
                await self.initialize()
            
            return {
                "available": self.model is not None,
                "model_name": "FunAudioLLM-SenseVoice",
                "device": self.device,
                "cuda_available": torch.cuda.is_available(),
                "features": [
                    "高性能语音识别 (比Whisper快15倍)",
                    "情感识别",
                    "声学事件检测", 
                    "50+语言支持",
                    "连续对话",
                    "多会话管理"
                ],
                "message": "FunAudioLLM服务正常" if self.model else "模型未加载",
                "supported_languages": ["auto", "zh", "en", "yue", "ja", "ko", "fr", "es", "de"],
                "performance": {
                    "speed": "15x faster than Whisper-Large",
                    "accuracy": "SOTA performance on multiple benchmarks"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ FunAudioLLM健康检查失败: {e}")
            return {
                "available": False,
                "error": str(e),
                "message": "FunAudioLLM服务异常"
            }

# 创建全局服务实例
funaudio_service = FunAudioLLMService() 