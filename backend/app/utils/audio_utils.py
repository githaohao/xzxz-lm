"""
音频处理工具模块
提供音频预处理、格式转换、验证等功能
"""

import os
import tempfile
import logging
from typing import Dict, Any, Optional
from io import BytesIO
import soundfile as sf
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class AudioProcessor:
    """音频处理工具类"""
    
    @staticmethod
    async def preprocess_audio(audio_data: bytes) -> str:
        """
        预处理音频数据，转换为模型所需格式
        
        Args:
            audio_data: 音频数据（字节）
            
        Returns:
            str: 处理后的音频文件路径
            
        Raises:
            ValueError: 音频数据无效时抛出异常
        """
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
    
    @staticmethod
    def save_audio_temp(audio_data: bytes, suffix: str = '.wav') -> str:
        """
        保存音频数据到临时文件
        
        Args:
            audio_data: 音频数据（字节）
            suffix: 文件后缀
            
        Returns:
            str: 临时文件路径
            
        Raises:
            Exception: 保存失败时抛出异常
        """
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(audio_data)
            temp_file.close()
            logger.info(f"📁 临时音频文件保存成功: {temp_file.name}")
            return temp_file.name
        except Exception as e:
            logger.error(f"❌ 保存临时音频文件失败: {e}")
            raise
    
    @staticmethod
    def validate_audio_data(audio_data: bytes, min_size: int = 100) -> Dict[str, Any]:
        """
        验证音频数据的有效性
        
        Args:
            audio_data: 音频数据（字节）
            min_size: 最小数据大小（字节）
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            if not audio_data:
                return {
                    "valid": False,
                    "error": "音频数据为空",
                    "size": 0
                }
            
            size = len(audio_data)
            if size < min_size:
                return {
                    "valid": False,
                    "error": f"音频数据太小: {size} bytes (最小: {min_size} bytes)",
                    "size": size
                }
            
            # 尝试基本的音频格式检测
            format_detected = "unknown"
            if audio_data.startswith(b'RIFF'):
                format_detected = "wav"
            elif audio_data.startswith(b'\xff\xfb') or audio_data.startswith(b'\xff\xf3'):
                format_detected = "mp3"
            elif audio_data.startswith(b'OggS'):
                format_detected = "ogg"
            elif b'webm' in audio_data[:100].lower():
                format_detected = "webm"
            
            return {
                "valid": True,
                "size": size,
                "format": format_detected,
                "error": None
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"音频验证失败: {str(e)}",
                "size": len(audio_data) if audio_data else 0
            }
    
    @staticmethod
    def cleanup_temp_file(file_path: str) -> bool:
        """
        清理临时音频文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 清理是否成功
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"🗑️ 临时文件清理成功: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ 临时文件清理失败: {e}")
            return False

# 便利函数
async def preprocess_audio(audio_data: bytes) -> str:
    """音频预处理便利函数"""
    return await AudioProcessor.preprocess_audio(audio_data)

def save_audio_temp(audio_data: bytes, suffix: str = '.wav') -> str:
    """保存临时音频文件便利函数"""
    return AudioProcessor.save_audio_temp(audio_data, suffix)

def validate_audio_data(audio_data: bytes, min_size: int = 100) -> Dict[str, Any]:
    """音频数据验证便利函数"""
    return AudioProcessor.validate_audio_data(audio_data, min_size)

def cleanup_temp_file(file_path: str) -> bool:
    """清理临时文件便利函数"""
    return AudioProcessor.cleanup_temp_file(file_path)