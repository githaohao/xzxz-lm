"""
通用工具函数
"""

import hashlib
import random
import time
import logging
from typing import List, Any, Dict

logger = logging.getLogger(__name__)


def generate_doc_id(content: str, filename: str) -> str:
    """
    生成文档唯一标识
    
    Args:
        content: 文档内容
        filename: 文件名
        
    Returns:
        文档唯一ID
    """
    # 使用内容和文件名的哈希作为文档ID
    content_hash = hashlib.md5(
        (content + filename).encode('utf-8')
    ).hexdigest()
    return f"doc_{content_hash[:16]}"


def get_random_color() -> str:
    """
    获取随机颜色
    
    Returns:
        随机颜色的十六进制代码
    """
    colors = [
        "#3B82F6", "#10B981", "#F59E0B", "#EF4444", 
        "#8B5CF6", "#06B6D4", "#84CC16", "#F97316",
        "#EC4899", "#6366F1"
    ]
    return random.choice(colors)


def get_timestamp() -> float:
    """
    获取当前时间戳
    
    Returns:
        float: 当前时间戳
    """
    return time.time()


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    安全获取字典值
    
    Args:
        data: 字典数据
        key: 键名
        default: 默认值
        
    Returns:
        Any: 获取的值或默认值
    """
    try:
        return data.get(key, default) if isinstance(data, dict) else default
    except Exception as e:
        logger.warning(f"⚠️ 安全获取字典值失败: {e}")
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    安全转换为整数
    
    Args:
        value: 要转换的值
        default: 默认值
        
    Returns:
        int: 转换后的整数或默认值
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    安全转换为浮点数
    
    Args:
        value: 要转换的值
        default: 默认值
        
    Returns:
        float: 转换后的浮点数或默认值
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断字符串
    
    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 后缀
        
    Returns:
        str: 截断后的字符串
    """
    try:
        if not isinstance(text, str):
            text = str(text)
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    except Exception as e:
        logger.warning(f"⚠️ 字符串截断失败: {e}")
        return str(text)[:max_length] if text else ""


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个字符串的相似度（简单版本）
    
    Args:
        text1: 字符串1
        text2: 字符串2
        
    Returns:
        float: 相似度（0-1之间）
    """
    try:
        if not text1 or not text2:
            return 0.0
        
        # 简单的字符级相似度计算
        set1 = set(text1.lower())
        set2 = set(text2.lower())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
        
    except Exception as e:
        logger.warning(f"⚠️ 相似度计算失败: {e}")
        return 0.0


def safe_str_convert(value: Any, default: str = "") -> str:
    """
    安全字符串转换
    
    Args:
        value: 要转换的值
        default: 默认值
        
    Returns:
        str: 转换后的字符串或默认值
    """
    try:
        if value is None:
            return default
        return str(value)
    except Exception as e:
        logger.warning(f"⚠️ 字符串转换失败: {e}")
        return default 