"""
LLM工具模块
提供消息格式化、聊天历史处理等功能
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageProcessor:
    """消息处理工具类"""
    
    @staticmethod
    def prepare_messages(request, system_prompt: str = None) -> List[Dict[str, str]]:
        """
        准备消息格式供LM Studio使用
        
        Args:
            request: 聊天请求对象
            system_prompt: 系统提示词
            
        Returns:
            List[Dict[str, str]]: 格式化的消息列表
        """
        try:
            messages = []
            
            # 添加系统提示
            if system_prompt is None:
                system_prompt = "你是一个智能助手，擅长处理文本、图像和语音等多模态内容。请用中文回答用户问题，保持友善和专业。"
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # 添加历史消息
            if hasattr(request, 'history') and request.history:
                for msg in request.history:
                    role = "user" if msg.is_user else "assistant"
                    content = msg.content
                    
                    # 如果是文件消息，添加文件信息
                    if hasattr(msg, 'file_name') and msg.file_name:
                        content = f"[文件: {msg.file_name}]\n{content}"
                        
                    messages.append({
                        "role": role,
                        "content": content
                    })
            
            # 添加当前消息
            if hasattr(request, 'message'):
                messages.append({
                    "role": "user",
                    "content": request.message
                })
            
            logger.info(f"📝 准备的消息数量: {len(messages)}")
            return messages
            
        except Exception as e:
            logger.error(f"❌ 消息格式准备失败: {e}")
            # 返回基本的消息格式
            return [
                {
                    "role": "system",
                    "content": system_prompt or "你是一个智能助手。"
                },
                {
                    "role": "user",
                    "content": getattr(request, 'message', '你好')
                }
            ]
    
    @staticmethod
    def format_chat_history(history: List[Dict[str, Any]], max_length: int = 20) -> List[Dict[str, str]]:
        """
        格式化聊天历史
        
        Args:
            history: 聊天历史列表
            max_length: 最大历史长度
            
        Returns:
            List[Dict[str, str]]: 格式化的历史消息
        """
        try:
            formatted_history = []
            
            # 限制历史长度
            recent_history = history[-max_length:] if len(history) > max_length else history
            
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                # 添加时间戳信息（如果有）
                if "timestamp" in msg:
                    timestamp = msg["timestamp"]
                    if isinstance(timestamp, (int, float)):
                        time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M")
                        content = f"[{time_str}] {content}"
                
                # 添加情感信息（如果有）
                if "emotion" in msg and msg["emotion"]:
                    emotion_info = msg["emotion"]
                    if isinstance(emotion_info, dict) and "primary" in emotion_info:
                        emotion = emotion_info["primary"]
                        if emotion != "neutral" and emotion != "中性":
                            content = f"[情感: {emotion}] {content}"
                
                formatted_history.append({
                    "role": role,
                    "content": content
                })
            
            logger.info(f"📚 格式化历史消息数量: {len(formatted_history)}")
            return formatted_history
            
        except Exception as e:
            logger.error(f"❌ 聊天历史格式化失败: {e}")
            return []
    
    @staticmethod
    def create_conversation_context(
        user_message: str,
        history: List[Dict[str, Any]] = None,
        emotion_info: Dict[str, Any] = None,
        system_prompt: str = None
    ) -> List[Dict[str, str]]:
        """
        创建对话上下文
        
        Args:
            user_message: 用户消息
            history: 聊天历史
            emotion_info: 情感信息
            system_prompt: 系统提示词
            
        Returns:
            List[Dict[str, str]]: 对话上下文
        """
        try:
            messages = []
            
            # 系统提示
            if system_prompt is None:
                system_prompt = "你是一个智能助手，擅长理解用户的情感和需求。请根据用户的情感状态给出合适的回应。"
            
            # 如果有情感信息，添加到系统提示中
            if emotion_info and emotion_info.get("primary") != "neutral":
                emotion = emotion_info.get("primary", "")
                system_prompt += f"\n当前用户情感状态：{emotion}，请据此调整回应风格。"
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # 添加历史消息
            if history:
                formatted_history = MessageProcessor.format_chat_history(history)
                messages.extend(formatted_history)
            
            # 添加当前用户消息
            current_content = user_message
            if emotion_info and emotion_info.get("primary") != "neutral":
                emotion = emotion_info.get("primary", "")
                current_content = f"[当前情感: {emotion}] {user_message}"
            
            messages.append({
                "role": "user",
                "content": current_content
            })
            
            logger.info(f"🎯 创建对话上下文，消息数量: {len(messages)}")
            return messages
            
        except Exception as e:
            logger.error(f"❌ 创建对话上下文失败: {e}")
            return [
                {
                    "role": "system",
                    "content": "你是一个智能助手。"
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
    
    @staticmethod
    def extract_response_content(response_data: Dict[str, Any]) -> str:
        """
        从LLM响应中提取内容
        
        Args:
            response_data: LLM响应数据
            
        Returns:
            str: 提取的内容
        """
        try:
            # 标准OpenAI格式
            if "choices" in response_data and response_data["choices"]:
                choice = response_data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
                elif "text" in choice:
                    return choice["text"]
            
            # 直接内容格式
            if "content" in response_data:
                return response_data["content"]
            
            # 文本格式
            if "text" in response_data:
                return response_data["text"]
            
            # 如果都没有，返回整个响应的字符串形式
            logger.warning("⚠️ 无法从响应中提取标准内容，返回原始响应")
            return str(response_data)
            
        except Exception as e:
            logger.error(f"❌ 提取响应内容失败: {e}")
            return "抱歉，处理响应时出现错误。"
    
    @staticmethod
    def validate_message_format(messages: List[Dict[str, str]]) -> bool:
        """
        验证消息格式是否正确
        
        Args:
            messages: 消息列表
            
        Returns:
            bool: 格式是否正确
        """
        try:
            if not isinstance(messages, list) or not messages:
                return False
            
            for msg in messages:
                if not isinstance(msg, dict):
                    return False
                
                if "role" not in msg or "content" not in msg:
                    return False
                
                if msg["role"] not in ["system", "user", "assistant"]:
                    return False
                
                if not isinstance(msg["content"], str):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 消息格式验证失败: {e}")
            return False
    
    @staticmethod
    def truncate_messages(messages: List[Dict[str, str]], max_tokens: int = 4000) -> List[Dict[str, str]]:
        """
        截断消息以适应token限制
        
        Args:
            messages: 消息列表
            max_tokens: 最大token数（粗略估算）
            
        Returns:
            List[Dict[str, str]]: 截断后的消息
        """
        try:
            # 粗略估算：1个token约等于4个字符（中文）
            max_chars = max_tokens * 4
            
            # 保留系统消息
            system_messages = [msg for msg in messages if msg["role"] == "system"]
            other_messages = [msg for msg in messages if msg["role"] != "system"]
            
            # 计算系统消息的字符数
            system_chars = sum(len(msg["content"]) for msg in system_messages)
            remaining_chars = max_chars - system_chars
            
            if remaining_chars <= 0:
                logger.warning("⚠️ 系统消息过长，只保留系统消息")
                return system_messages
            
            # 从后往前保留其他消息
            truncated_messages = []
            current_chars = 0
            
            for msg in reversed(other_messages):
                msg_chars = len(msg["content"])
                if current_chars + msg_chars <= remaining_chars:
                    truncated_messages.insert(0, msg)
                    current_chars += msg_chars
                else:
                    break
            
            result = system_messages + truncated_messages
            logger.info(f"📏 消息截断完成，保留 {len(result)} 条消息")
            return result
            
        except Exception as e:
            logger.error(f"❌ 消息截断失败: {e}")
            return messages

# 便利函数
def prepare_messages(request, system_prompt: str = None) -> List[Dict[str, str]]:
    """准备消息格式便利函数"""
    return MessageProcessor.prepare_messages(request, system_prompt)

def format_chat_history(history: List[Dict[str, Any]], max_length: int = 20) -> List[Dict[str, str]]:
    """格式化聊天历史便利函数"""
    return MessageProcessor.format_chat_history(history, max_length)

def create_conversation_context(
    user_message: str,
    history: List[Dict[str, Any]] = None,
    emotion_info: Dict[str, Any] = None,
    system_prompt: str = None
) -> List[Dict[str, str]]:
    """创建对话上下文便利函数"""
    return MessageProcessor.create_conversation_context(user_message, history, emotion_info, system_prompt)

def extract_response_content(response_data: Dict[str, Any]) -> str:
    """提取响应内容便利函数"""
    return MessageProcessor.extract_response_content(response_data)

def validate_message_format(messages: List[Dict[str, str]]) -> bool:
    """验证消息格式便利函数"""
    return MessageProcessor.validate_message_format(messages)

def truncate_messages(messages: List[Dict[str, str]], max_tokens: int = 4000) -> List[Dict[str, str]]:
    """截断消息便利函数"""
    return MessageProcessor.truncate_messages(messages, max_tokens)

def prepare_lm_studio_messages(request) -> List[Dict[str, str]]:
    """准备LM Studio消息格式（便捷函数）"""
    return MessageProcessor.prepare_messages(request)

def format_user_message(content: str, emotion_info: Dict[str, Any] = None, timestamp: float = None) -> Dict[str, Any]:
    """格式化用户消息（便捷函数）"""
    message = {
        "role": "user",
        "content": content
    }
    
    if emotion_info:
        message["emotion"] = emotion_info
    
    if timestamp:
        message["timestamp"] = timestamp
    
    return message

def format_assistant_message(content: str, timestamp: float = None) -> Dict[str, Any]:
    """格式化助手消息（便捷函数）"""
    message = {
        "role": "assistant",
        "content": content
    }
    
    if timestamp:
        message["timestamp"] = timestamp
    
    return message

def limit_conversation_history(history: List[Dict[str, Any]], max_length: int) -> List[Dict[str, Any]]:
    """限制对话历史长度（便捷函数）"""
    if len(history) > max_length * 2:
        return history[-max_length * 2:]
    return history 