"""
情感分析工具模块
提供情感识别、声学事件检测等功能
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
    def analyze_emotion(text: str, format_type: str = "sensevoice") -> Dict[str, Any]:
        """
        分析文本中的情感信息
        
        Args:
            text: 输入文本
            format_type: 格式类型 ("sensevoice" 或 "simple")
            
        Returns:
            Dict[str, Any]: 情感分析结果
        """
        try:
            if format_type == "sensevoice":
                return EmotionAnalyzer._analyze_sensevoice_emotion(text)
            else:
                return EmotionAnalyzer._analyze_simple_emotion(text)
                
        except Exception as e:
            logger.error(f"❌ 情感分析失败: {e}")
            return {
                "primary": "neutral",
                "confidence": 0.0,
                "details": {},
                "raw_emotions": []
            }
    
    @staticmethod
    def _analyze_sensevoice_emotion(processed_text: str) -> Dict[str, Any]:
        """分析SenseVoice格式的情感信息"""
        try:
            detected_emotions = {}
            raw_emotions = []
            
            for emotion_en, emotion_zh in EmotionAnalyzer.SENSEVOICE_EMOTIONS.items():
                if f"<|{emotion_en}|>" in processed_text:
                    detected_emotions[emotion_zh] = 1.0
                    raw_emotions.append(emotion_en)
            
            # 确定主要情感
            if detected_emotions:
                primary_emotion = max(detected_emotions.keys(), key=lambda k: detected_emotions[k])
                confidence = detected_emotions[primary_emotion]
            else:
                primary_emotion = "中性"
                confidence = 1.0
            
            return {
                "primary": primary_emotion,
                "confidence": confidence,
                "details": detected_emotions,
                "raw_emotions": raw_emotions
            }
            
        except Exception as e:
            logger.error(f"❌ SenseVoice情感分析失败: {e}")
            return {
                "primary": "中性",
                "confidence": 0.0,
                "details": {},
                "raw_emotions": []
            }
    
    @staticmethod
    def _analyze_simple_emotion(text: str) -> Dict[str, Any]:
        """分析简单格式的情感信息"""
        try:
            detected_emotions = {}
            
            for emoji, emotion in EmotionAnalyzer.SIMPLE_EMOTIONS.items():
                if emoji in text:
                    detected_emotions[emotion] = 1.0
            
            # 确定主要情感
            if detected_emotions:
                primary_emotion = max(detected_emotions.keys(), key=lambda k: detected_emotions[k])
                confidence = detected_emotions[primary_emotion]
            else:
                primary_emotion = "neutral"
                confidence = 1.0
            
            return {
                "primary": primary_emotion,
                "confidence": confidence,
                "details": detected_emotions,
                "raw_emotions": list(detected_emotions.keys())
            }
            
        except Exception as e:
            logger.error(f"❌ 简单情感分析失败: {e}")
            return {
                "primary": "neutral",
                "confidence": 0.0,
                "details": {},
                "raw_emotions": []
            }
    
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
    def clean_text(text: str, format_type: str = "sensevoice") -> str:
        """
        清理文本，移除情感和事件标记
        
        Args:
            text: 输入文本
            format_type: 格式类型 ("sensevoice" 或 "simple")
            
        Returns:
            str: 清理后的文本
        """
        try:
            if format_type == "sensevoice":
                return EmotionAnalyzer._clean_sensevoice_text(text)
            else:
                return EmotionAnalyzer._clean_simple_text(text)
                
        except Exception as e:
            logger.error(f"❌ 文本清理失败: {e}")
            return text
    
    @staticmethod
    def _clean_sensevoice_text(text: str) -> str:
        """清理SenseVoice格式的文本"""
        try:
            # 移除情感标记
            for emotion_en in EmotionAnalyzer.SENSEVOICE_EMOTIONS.keys():
                text = text.replace(f"<|{emotion_en}|>", "")
            
            # 移除事件标记
            for event_en in EmotionAnalyzer.SENSEVOICE_EVENTS.keys():
                text = text.replace(f"<|{event_en}|>", "")
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ SenseVoice文本清理失败: {e}")
            return text
    
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
def analyze_emotion(text: str, format_type: str = "sensevoice") -> Dict[str, Any]:
    """情感分析便利函数"""
    return EmotionAnalyzer.analyze_emotion(text, format_type)

def extract_emotion_info(processed_text: str, format_type: str = "sensevoice") -> Dict[str, Any]:
    """提取情感信息便利函数"""
    return EmotionAnalyzer.analyze_emotion(processed_text, format_type)

def extract_event_info(processed_text: str, format_type: str = "sensevoice") -> List[str]:
    """提取事件信息便利函数"""
    return EmotionAnalyzer.extract_event_info(processed_text, format_type)

def clean_text(text: str, format_type: str = "sensevoice") -> str:
    """清理文本便利函数"""
    return EmotionAnalyzer.clean_text(text, format_type)

def generate_simple_response(user_text: str, emotion_info: Dict[str, Any]) -> str:
    """生成简单回复便利函数"""
    return EmotionAnalyzer.generate_simple_response(user_text, emotion_info)

# SenseVoice 专用便利函数
def extract_sensevoice_emotion_info(processed_text: str) -> Dict[str, Any]:
    """提取SenseVoice情感信息"""
    return EmotionAnalyzer.analyze_emotion(processed_text, "sensevoice")

def extract_sensevoice_event_info(processed_text: str) -> List[str]:
    """提取SenseVoice事件信息"""
    return EmotionAnalyzer.extract_event_info(processed_text, "sensevoice")

def clean_sensevoice_text(processed_text: str) -> str:
    """清理SenseVoice文本"""
    return EmotionAnalyzer.clean_text(processed_text, "sensevoice")