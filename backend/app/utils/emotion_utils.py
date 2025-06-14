"""
情感分析工具模块
提供情感识别、声学事件检测、模糊匹配等功能
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class EmotionAnalyzer:
    """情感分析工具类"""
    
    # SenseVoice 情感标记映射
    SENSEVOICE_EMOTIONS = {
        "HAPPY": "开心",
        "SAD": "悲伤", 
        "ANGRY": "愤怒",
        "SURPRISED": "惊讶",
        "FEARFUL": "恐惧",
        "DISGUSTED": "厌恶",
        "NEUTRAL": "中性"
    }
    
    # SenseVoice 声学事件标记映射
    SENSEVOICE_EVENTS = {
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
    
    # 简单情感词汇映射
    SIMPLE_EMOTIONS = {
        "😊": "happy",
        "😡": "angry", 
        "😔": "sad",
        "😀": "laugh",
        "😭": "cry"
    }
    
    # 简单事件标记映射
    SIMPLE_EVENTS = {
        "🎼": "music",
        "👏": "applause", 
        "🤧": "cough_sneeze",
        "😭": "crying",
        "😀": "laughter"
    }
    
    @staticmethod
    def analyze_emotion(text: str) -> str:
        """
        简单的情感分析
        
        Args:
            text: 输入文本
            
        Returns:
            str: 情感类型
        """
        try:
            positive_words = ["开心", "高兴", "好", "棒", "喜欢", "爱", "满意", "快乐", "兴奋"]
            negative_words = ["难过", "生气", "不好", "讨厌", "愤怒", "失望", "伤心", "痛苦"]
            
            if any(word in text for word in positive_words):
                return "positive"
            elif any(word in text for word in negative_words):
                return "negative"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"❌ 情感分析失败: {e}")
            return "neutral"
    
    @staticmethod
    def extract_emotion_info(processed_text: str, format_type: str = "sensevoice") -> Dict[str, Any]:
        """
        从处理后的文本中提取情感信息
        
        Args:
            processed_text: 处理后的文本
            format_type: 格式类型 ("sensevoice" 或 "simple")
            
        Returns:
            Dict[str, Any]: 情感信息
        """
        try:
            if format_type == "sensevoice":
                return EmotionAnalyzer._extract_sensevoice_emotion(processed_text)
            else:
                return EmotionAnalyzer._extract_simple_emotion(processed_text)
                
        except Exception as e:
            logger.error(f"❌ 情感信息提取失败: {e}")
            return {"detected": False, "primary": "未知", "emotions": []}
    
    @staticmethod
    def _extract_sensevoice_emotion(processed_text: str) -> Dict[str, Any]:
        """提取SenseVoice格式的情感信息"""
        try:
            detected_emotions = []
            
            for emotion_en, emotion_zh in EmotionAnalyzer.SENSEVOICE_EMOTIONS.items():
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
            logger.error(f"❌ SenseVoice情感信息提取失败: {e}")
            return {"detected": False, "primary": "未知", "emotions": []}
    
    @staticmethod
    def _extract_simple_emotion(text: str) -> Dict[str, Any]:
        """提取简单格式的情感信息"""
        try:
            detected_emotions = []
            
            for emoji, emotion in EmotionAnalyzer.SIMPLE_EMOTIONS.items():
                if emoji in text:
                    detected_emotions.append(emotion)
            
            return {
                "detected": detected_emotions,
                "primary": detected_emotions[0] if detected_emotions else "neutral"
            }
            
        except Exception as e:
            logger.error(f"❌ 简单情感信息提取失败: {e}")
            return {"detected": [], "primary": "neutral"}
    
    @staticmethod
    def extract_event_info(processed_text: str, format_type: str = "sensevoice") -> List[str]:
        """
        从处理后的文本中提取声学事件信息
        
        Args:
            processed_text: 处理后的文本
            format_type: 格式类型 ("sensevoice" 或 "simple")
            
        Returns:
            List[str]: 检测到的事件列表
        """
        try:
            if format_type == "sensevoice":
                return EmotionAnalyzer._extract_sensevoice_events(processed_text)
            else:
                return EmotionAnalyzer._extract_simple_events(processed_text)
                
        except Exception as e:
            logger.error(f"❌ 声学事件提取失败: {e}")
            return []
    
    @staticmethod
    def _extract_sensevoice_events(processed_text: str) -> List[str]:
        """提取SenseVoice格式的声学事件"""
        try:
            detected_events = []
            
            for event_en, event_zh in EmotionAnalyzer.SENSEVOICE_EVENTS.items():
                if f"<|{event_en}|>" in processed_text:
                    detected_events.append(event_zh)
            
            return detected_events
            
        except Exception as e:
            logger.error(f"❌ SenseVoice声学事件提取失败: {e}")
            return []
    
    @staticmethod
    def _extract_simple_events(text: str) -> List[str]:
        """提取简单格式的声学事件"""
        try:
            detected_events = []
            
            for emoji, event in EmotionAnalyzer.SIMPLE_EVENTS.items():
                if emoji in text:
                    detected_events.append(event)
            
            return detected_events
            
        except Exception as e:
            logger.error(f"❌ 简单声学事件提取失败: {e}")
            return []
    
    @staticmethod
    def clean_text(processed_text: str, format_type: str = "sensevoice") -> str:
        """
        清理文本，移除特殊标记
        
        Args:
            processed_text: 处理后的文本
            format_type: 格式类型 ("sensevoice" 或 "simple")
            
        Returns:
            str: 清理后的文本
        """
        try:
            if format_type == "sensevoice":
                return EmotionAnalyzer._clean_sensevoice_text(processed_text)
            else:
                return EmotionAnalyzer._clean_simple_text(processed_text)
                
        except Exception as e:
            logger.error(f"❌ 文本清理失败: {e}")
            return processed_text
    
    @staticmethod
    def _clean_sensevoice_text(processed_text: str) -> str:
        """清理SenseVoice格式的文本"""
        try:
            # 移除情感标记
            text = re.sub(r'<\|[A-Z_]+\|>', '', processed_text)
            
            # 移除多余的空格
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
            
        except Exception as e:
            logger.error(f"❌ SenseVoice文本清理失败: {e}")
            return processed_text
    
    @staticmethod
    def _clean_simple_text(text: str) -> str:
        """清理简单格式的文本"""
        try:
            # 移除emoji
            emoji_pattern = re.compile("["
                                     u"\U0001F600-\U0001F64F"  # emoticons
                                     u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                     u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                     u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                     "]+", flags=re.UNICODE)
            return emoji_pattern.sub('', text).strip()
            
        except Exception as e:
            logger.error(f"❌ 简单文本清理失败: {e}")
            return text
    
    @staticmethod
    def fuzzy_match(wake_word: str, recognized_text: str, threshold: float = 0.6) -> bool:
        """
        模糊匹配唤醒词，处理语音识别的不准确性
        
        Args:
            wake_word: 唤醒词
            recognized_text: 识别的文本
            threshold: 相似度阈值
            
        Returns:
            bool: 是否匹配
        """
        try:
            # 移除空格和标点符号
            wake_word_clean = re.sub(r'[^\w]', '', wake_word.lower())
            recognized_clean = re.sub(r'[^\w]', '', recognized_text.lower())
            
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
                return similarity >= threshold
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 模糊匹配失败: {e}")
            return False
    
    @staticmethod
    def generate_simple_response(user_text: str, emotion_info: Dict[str, Any]) -> str:
        """
        生成简单的回复（可扩展接入其他LLM）
        
        Args:
            user_text: 用户文本
            emotion_info: 情感信息
            
        Returns:
            str: 回复文本
        """
        try:
            primary_emotion = emotion_info.get("primary", "neutral")
            
            if primary_emotion == "happy" or primary_emotion == "开心":
                return f"很高兴听到你开心的话语！你说：「{user_text}」"
            elif primary_emotion == "sad" or primary_emotion == "悲伤":
                return f"我能感受到你的情绪，让我来帮助你。你说：「{user_text}」"
            elif primary_emotion == "angry" or primary_emotion == "愤怒":
                return f"我理解你的感受，让我们冷静地讨论一下。你说：「{user_text}」" 
            else:
                return f"我听到你说：「{user_text}」。有什么我可以帮助你的吗？"
                
        except Exception as e:
            logger.error(f"❌ 生成回复失败: {e}")
            return f"我听到你说：「{user_text}」。有什么我可以帮助你的吗？"

# 便利函数
def analyze_emotion(text: str) -> str:
    """情感分析便利函数"""
    return EmotionAnalyzer.analyze_emotion(text)

def extract_emotion_info(processed_text: str, format_type: str = "sensevoice") -> Dict[str, Any]:
    """提取情感信息便利函数"""
    return EmotionAnalyzer.extract_emotion_info(processed_text, format_type)

def extract_event_info(processed_text: str, format_type: str = "sensevoice") -> List[str]:
    """提取声学事件信息便利函数"""
    return EmotionAnalyzer.extract_event_info(processed_text, format_type)

def clean_text(processed_text: str, format_type: str = "sensevoice") -> str:
    """清理文本便利函数"""
    return EmotionAnalyzer.clean_text(processed_text, format_type)

def fuzzy_match(wake_word: str, recognized_text: str, threshold: float = 0.6) -> bool:
    """模糊匹配便利函数"""
    return EmotionAnalyzer.fuzzy_match(wake_word, recognized_text, threshold)

def generate_simple_response(user_text: str, emotion_info: Dict[str, Any]) -> str:
    """生成简单回复便利函数"""
    return EmotionAnalyzer.generate_simple_response(user_text, emotion_info)

# 为了向后兼容，添加特定格式的便捷函数
def extract_sensevoice_emotion_info(processed_text: str) -> Dict[str, Any]:
    """提取SenseVoice格式的情感信息（便捷函数）"""
    return EmotionAnalyzer.extract_emotion_info(processed_text, "sensevoice")

def extract_sensevoice_event_info(processed_text: str) -> List[str]:
    """提取SenseVoice格式的声学事件信息（便捷函数）"""
    return EmotionAnalyzer.extract_event_info(processed_text, "sensevoice")

def clean_sensevoice_text(processed_text: str) -> str:
    """清理SenseVoice文本（便捷函数）"""
    return EmotionAnalyzer.clean_text(processed_text, "sensevoice")

def fuzzy_match_wake_word(wake_word: str, recognized_text: str) -> bool:
    """模糊匹配唤醒词（便捷函数）"""
    return EmotionAnalyzer.fuzzy_match(wake_word, recognized_text, 0.6) 