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
        
        # 移除思考标签及其内容（处理嵌套标签）
        # 使用循环处理嵌套的思考标签
        cleaned = text
        while '<think>' in cleaned:
            # 找到第一个开始标签
            start_pos = cleaned.find('<think>')
            if start_pos == -1:
                break
            
            # 从开始标签位置开始，找到匹配的结束标签
            # 需要处理嵌套情况
            pos = start_pos + 7  # len('<think>')
            depth = 1
            end_pos = -1
            
            while pos < len(cleaned) and depth > 0:
                if cleaned[pos:pos+7] == '<think>':
                    depth += 1
                    pos += 7
                elif cleaned[pos:pos+8] == '</think>':
                    depth -= 1
                    if depth == 0:
                        end_pos = pos + 8
                        break
                    pos += 8
                else:
                    pos += 1
            
            if end_pos != -1:
                # 找到匹配的结束标签，移除整个标签及其内容
                cleaned = cleaned[:start_pos] + cleaned[end_pos:]
            else:
                # 没有找到匹配的结束标签，移除从开始标签到文本末尾的所有内容
                cleaned = cleaned[:start_pos]
                break
        
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
        cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)
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
            # 第一层验证：基本输入检查
            if not text or not isinstance(text, str):
                logger.info("跳过TTS: 输入文本为空或类型错误")
                return None
            
            # 清理文本，移除思考标签和表情符号
            clean_text = VoiceProcessor.clean_text_for_speech(text.strip())
            
            # 第二层验证：清理后的文本检查
            if not clean_text or not clean_text.strip():
                logger.info("跳过TTS: 清理后的文本为空")
                return None
            
            # 第三层验证：内容有效性检查
            import re
            # 检查是否只包含标点符号和空白字符
            text_without_punctuation = re.sub(r'[^\w\u4e00-\u9fff]', '', clean_text)
            if not text_without_punctuation:
                logger.info(f"跳过TTS: 文本只包含标点符号, 原文: {repr(clean_text[:50])}")
                return None
            
            # 第四层验证：文本长度检查
            if len(clean_text.strip()) < 2:
                logger.info(f"跳过TTS: 文本过短, 长度: {len(clean_text)}, 内容: {repr(clean_text)}")
                return None
            
            logger.info(f"🎵 开始TTS合成: {repr(clean_text[:100])}{'...' if len(clean_text) > 100 else ''}")
                
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
            
            logger.info(f"✅ TTS合成成功: {file_size} 字节")
            return audio_data
            
        except ValueError as ve:
            # 输入验证错误，这是预期的，不记录为错误
            logger.info(f"跳过TTS: {ve}")
            return None
        except Exception as e:
            logger.error(f"❌ TTS块合成失败: {e}, 原始文本: {repr(text[:200] if text else 'None')}")
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