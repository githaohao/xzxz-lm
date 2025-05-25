"""
FunAudioLLM语音服务配置
统一使用阿里巴巴SenseVoice高性能语音识别服务
"""

from .funaudio_service_real import FunAudioLLMService

# 创建全局服务实例
funaudio_service = FunAudioLLMService()

print("✅ 使用FunAudioLLM高性能语音服务 (SenseVoice)")

__all__ = ["funaudio_service"]
