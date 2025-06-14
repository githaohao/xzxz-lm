"""
语音处理工具类
"""

import re
import os
import base64
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """语音处理工具类"""
    
    @staticmethod
    def clean_text_for_speech(text: str) -> str:
        """
        清理文本用于语音合成
        - 移除 <think></think> 标签及其内容
        - 移除表情符号
        - 移除多余的空白字符
        """
        if not text:
            return ''
        
        # 移除思考标签及其内容（包括不完整的标签）
        cleaned = re.sub(r'<think>[\s\S]*?</think>', '', text)
        # 移除不完整的思考标签（只有开始标签的情况）
        cleaned = re.sub(r'<think>.*$', '', cleaned)
        
        # 移除表情符号（更全面的Unicode范围）
        # Emoticons and symbols
        cleaned = re.sub(r'[\U0001F600-\U0001F64F]', '', cleaned)  # 表情符号
        cleaned = re.sub(r'[\U0001F300-\U0001F5FF]', '', cleaned)  # 符号和图标
        cleaned = re.sub(r'[\U0001F680-\U0001F6FF]', '', cleaned)  # 交通和地图符号
        cleaned = re.sub(r'[\U0001F700-\U0001F77F]', '', cleaned)  # 炼金术符号
        cleaned = re.sub(r'[\U0001F780-\U0001F7FF]', '', cleaned)  # 几何图形扩展
        cleaned = re.sub(r'[\U0001F800-\U0001F8FF]', '', cleaned)  # 补充箭头-C
        cleaned = re.sub(r'[\U0001F900-\U0001F9FF]', '', cleaned)  # 补充符号和图标
        cleaned = re.sub(r'[\U0001FA00-\U0001FA6F]', '', cleaned)  # 扩展-A
        cleaned = re.sub(r'[\U0001FA70-\U0001FAFF]', '', cleaned)  # 符号和图标扩展-A
        cleaned = re.sub(r'[\U00002600-\U000026FF]', '', cleaned)  # 杂项符号
        cleaned = re.sub(r'[\U00002700-\U000027BF]', '', cleaned)  # 装饰符号
        cleaned = re.sub(r'[\U0000FE00-\U0000FE0F]', '', cleaned)  # 变体选择器
        
        # 移除Markdown格式（可选，已有的清理逻辑）
        cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)  # 粗体
        cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)      # 斜体
        cleaned = re.sub(r'`(.*?)`', r'\1', cleaned)        # 代码
        cleaned = re.sub(r'#{1,6}\s*(.*)', r'\1', cleaned) # 标题
        cleaned = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', cleaned)  # 链接
        
        # 移除多余的空白字符
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned

    @staticmethod
    def split_text_for_tts(text: str) -> List[str]:
        """智能文本分块，用于TTS合成"""
        if not text.strip():
            return []
        
        # 先清理文本，移除思考标签和表情符号
        clean_text = VoiceProcessor.clean_text_for_speech(text)
        
        if not clean_text.strip():
            return []
        
        # 按句子分割的正则表达式
        sentence_endings = r'[.!?。！？；;]\s*'
        sentences = re.split(sentence_endings, clean_text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 检查当前块+新句子的长度
            potential_chunk = current_chunk + sentence
            
            if len(potential_chunk) <= 100:  # 最大块大小
                current_chunk = potential_chunk
            else:
                # 当前块达到合适大小，添加到结果中
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        # 处理最后一个不完整的块
        # 只有在原始文本以句号结尾时才处理剩余部分
        if current_chunk and (clean_text.rstrip().endswith('.') or 
                             clean_text.rstrip().endswith('!') or 
                             clean_text.rstrip().endswith('?') or
                             clean_text.rstrip().endswith('。') or
                             clean_text.rstrip().endswith('！') or
                             clean_text.rstrip().endswith('？')):
            chunks.append(current_chunk.strip())
        
        return chunks

    @staticmethod
    async def synthesize_speech_chunk(text: str) -> Optional[bytes]:
        """合成单个文本块的语音"""
        try:
            # 清理文本，移除思考标签和表情符号
            clean_text = VoiceProcessor.clean_text_for_speech(text.strip())
            if not clean_text:
                return None
                
            # 延迟导入避免循环导入
            from app.services.tts_service import tts_service
            
            # 调用TTS服务
            audio_path, file_size = await tts_service.text_to_speech(
                text=clean_text,
                voice="zh-CN-XiaoxiaoNeural",
                rate="+0%",
                volume="+0%"
            )
            
            # 读取音频文件
            with open(audio_path, "rb") as audio_file:
                audio_data = audio_file.read()
            
            # 清理临时文件
            try:
                os.remove(audio_path)
            except Exception as e:
                logger.warning(f"清理临时TTS文件失败: {e}")
            
            return audio_data
            
        except Exception as e:
            logger.error(f"TTS块合成失败: {e}")
            return None


# 便利函数，保持向后兼容性
def clean_text_for_speech(text: str) -> str:
    """清理文本用于语音合成 - 便利函数"""
    return VoiceProcessor.clean_text_for_speech(text)


def split_text_for_tts(text: str) -> List[str]:
    """智能文本分块，用于TTS合成 - 便利函数"""
    return VoiceProcessor.split_text_for_tts(text)


async def synthesize_speech_chunk(text: str) -> Optional[bytes]:
    """合成单个文本块的语音 - 便利函数"""
    return await VoiceProcessor.synthesize_speech_chunk(text) 