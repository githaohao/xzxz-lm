import asyncio
import os
import uuid
from datetime import datetime
import edge_tts
import logging
from app.config import settings
from typing import Tuple
import re

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.voice = settings.tts_voice
        self.rate = settings.tts_rate
        self.volume = settings.tts_volume
        self.output_dir = os.path.join(settings.upload_dir, "tts_audio")
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def text_to_speech(self, text: str, voice: str = None, rate: str = None, volume: str = None) -> Tuple[str, int]:
        """将文本转换为语音"""
        try:
            # 严格的输入验证
            if not text or not isinstance(text, str):
                raise ValueError("文本输入为空或类型错误")
            
            # 清理和验证文本内容
            cleaned_text = text.strip()
            if not cleaned_text:
                raise ValueError("清理后的文本为空")
            
            # 检查文本长度
            if len(cleaned_text) < 1:
                raise ValueError("文本长度过短")
                
            # 检查是否只包含标点符号和空白字符
            # 移除所有标点符号和空白字符，检查是否还有内容
            text_without_punctuation = re.sub(r'[^\w\u4e00-\u9fff]', '', cleaned_text)
            if not text_without_punctuation:
                raise ValueError("文本只包含标点符号和空白字符，无法进行语音合成")
            
            # 检查文本是否包含无效字符（可能导致edge-tts失败的字符）
            # 移除或替换一些可能导致问题的特殊字符
            safe_text = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef.,!?;:()"""''，。！？；：（）【】《》]', '', cleaned_text)
            if not safe_text.strip():
                raise ValueError("文本包含过多特殊字符，无法进行语音合成")
                
            # 记录要合成的文本（用于调试）
            logger.info(f"🔊 TTS合成文本: {repr(safe_text[:100])}{'...' if len(safe_text) > 100 else ''}")
            
            # 使用传入参数或默认值
            voice = voice or self.voice
            rate = rate or self.rate
            volume = volume or self.volume
            
            # 生成唯一文件名
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"tts_{timestamp}_{file_id}.mp3"
            audio_path = os.path.join(self.output_dir, audio_filename)
            
            # 创建TTS通信器
            communicate = edge_tts.Communicate(safe_text, voice, rate=rate, volume=volume)
            
            # 保存音频文件
            await communicate.save(audio_path)
            
            # 验证生成的音频文件
            if not os.path.exists(audio_path):
                raise Exception("音频文件生成失败")
                
            # 获取文件大小
            file_size = os.path.getsize(audio_path)
            
            # 检查文件大小是否合理
            if file_size < 100:  # 音频文件应该至少有100字节
                logger.warning(f"⚠️ 生成的音频文件过小: {file_size} 字节")
                # 不抛出异常，但记录警告
            
            logger.info(f"✅ TTS转换成功: {audio_filename}, 大小: {file_size} 字节")
            return audio_path, file_size
            
        except ValueError as ve:
            # 输入验证错误，记录详细信息但不抛出异常给上层
            logger.warning(f"⚠️ TTS输入验证失败: {ve}, 原始文本: {repr(text[:200] if text else 'None')}")
            raise ve
        except Exception as e:
            logger.error(f"❌ TTS转换失败: {e}, 原始文本: {repr(text[:200] if text else 'None')}")
            raise Exception(f"TTS转换失败: {str(e)}")
    
    async def get_available_voices(self):
        """获取可用的语音列表"""
        try:
            voices = await edge_tts.list_voices()
            # 过滤中文语音
            chinese_voices = [
                voice for voice in voices 
                if 'zh-CN' in voice['Locale'] or 'zh-TW' in voice['Locale'] or 'zh-HK' in voice['Locale']
            ]
            return chinese_voices
        except Exception as e:
            logger.error(f"获取语音列表失败: {e}")
            return []
    
    def clean_old_files(self, days: int = 7):
        """清理旧的音频文件"""
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 60 * 60)
            
            cleaned_count = 0
            for filename in os.listdir(self.output_dir):
                file_path = os.path.join(self.output_dir, filename)
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
            
            logger.info(f"清理了 {cleaned_count} 个旧音频文件")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理音频文件失败: {e}")
            return 0

# 创建全局服务实例
tts_service = TTSService() 