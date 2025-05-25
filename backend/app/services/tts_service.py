import asyncio
import os
import uuid
from datetime import datetime
import edge_tts
import logging
from app.config import settings
from typing import Tuple

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
            communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
            
            # 保存音频文件
            await communicate.save(audio_path)
            
            # 获取文件大小
            file_size = os.path.getsize(audio_path)
            
            logger.info(f"TTS转换成功: {audio_filename}, 大小: {file_size} 字节")
            return audio_path, file_size
            
        except Exception as e:
            logger.error(f"TTS转换失败: {e}")
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