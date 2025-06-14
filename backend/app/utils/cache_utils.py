#!/usr/bin/env python3
"""
缓存工具类
提供文件缓存、内存缓存等功能
"""

import os
import time
import hashlib
import logging
from typing import Dict, Tuple, Optional, Any, Union
from app.config import settings

logger = logging.getLogger(__name__)


class FileHashCache:
    """基于文件哈希的缓存系统"""
    
    def __init__(self, ttl: int = 3600, max_size: int = 100):
        """
        初始化缓存
        
        Args:
            ttl: 缓存生存时间（秒）
            max_size: 最大缓存条目数
        """
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl = ttl
        self.max_size = max_size
        self.enabled = True
    
    def _get_file_hash(self, file_path: str) -> str:
        """
        获取文件哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件的MD5哈希值
        """
        try:
            if not os.path.exists(file_path):
                return ""
                
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5()
                # 分块读取以节省内存
                chunk_size = 8192
                while chunk := f.read(chunk_size):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
                
        except (OSError, IOError) as e:
            logger.warning(f"计算文件哈希失败 {file_path}: {e}")
            return ""
    
    def _cleanup_expired(self):
        """清理过期的缓存条目"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
            
        if expired_keys:
            logger.debug(f"清理了 {len(expired_keys)} 个过期缓存条目")
    
    def _manage_size(self):
        """管理缓存大小，移除最旧的条目"""
        if len(self.cache) <= self.max_size:
            return
            
        # 按时间戳排序，移除最旧的条目
        sorted_items = sorted(
            self.cache.items(), 
            key=lambda x: x[1][1]  # 按时间戳排序
        )
        
        # 保留最新的max_size个条目
        items_to_keep = sorted_items[-self.max_size:]
        self.cache = dict(items_to_keep)
        
        removed_count = len(sorted_items) - len(items_to_keep)
        if removed_count > 0:
            logger.debug(f"移除了 {removed_count} 个旧缓存条目以控制大小")
    
    def get(self, file_path: str) -> Optional[Any]:
        """
        获取缓存结果
        
        Args:
            file_path: 文件路径
            
        Returns:
            缓存的结果，如果不存在或过期则返回None
        """
        if not self.enabled:
            return None
            
        try:
            # 清理过期条目
            self._cleanup_expired()
            
            file_hash = self._get_file_hash(file_path)
            if not file_hash:
                return None
                
            if file_hash in self.cache:
                result, timestamp = self.cache[file_hash]
                if time.time() - timestamp < self.ttl:
                    logger.debug(f"使用缓存结果: {file_path}")
                    return result
                else:
                    # 过期，删除条目
                    del self.cache[file_hash]
                    
            return None
            
        except Exception as e:
            logger.warning(f"获取缓存失败: {e}")
            return None
    
    def set(self, file_path: str, result: Any):
        """
        设置缓存结果
        
        Args:
            file_path: 文件路径
            result: 要缓存的结果
        """
        if not self.enabled:
            return
            
        try:
            file_hash = self._get_file_hash(file_path)
            if not file_hash:
                return
                
            self.cache[file_hash] = (result, time.time())
            
            # 管理缓存大小
            self._manage_size()
            
            logger.debug(f"缓存结果已保存: {file_path}")
            
        except Exception as e:
            logger.warning(f"设置缓存失败: {e}")
    
    def clear(self):
        """清空所有缓存"""
        cache_count = len(self.cache)
        self.cache.clear()
        logger.info(f"已清空 {cache_count} 个缓存条目")
    
    def enable(self):
        """启用缓存"""
        self.enabled = True
        logger.info("缓存已启用")
    
    def disable(self):
        """禁用缓存"""
        self.enabled = False
        logger.info("缓存已禁用")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        current_time = time.time()
        valid_count = sum(
            1 for _, timestamp in self.cache.values()
            if current_time - timestamp < self.ttl
        )
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_count,
            'expired_entries': len(self.cache) - valid_count,
            'ttl': self.ttl,
            'max_size': self.max_size,
            'enabled': self.enabled
        }


class ContentHashCache:
    """基于内容哈希的缓存系统"""
    
    def __init__(self, ttl: int = 3600, max_size: int = 100):
        """
        初始化缓存
        
        Args:
            ttl: 缓存生存时间（秒）
            max_size: 最大缓存条目数
        """
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl = ttl
        self.max_size = max_size
        self.enabled = True
    
    def _get_content_hash(self, content: Union[str, bytes], *args) -> str:
        """
        获取内容哈希值
        
        Args:
            content: 内容（字符串或字节）
            *args: 额外的参数用于生成唯一哈希
            
        Returns:
            内容的MD5哈希值
        """
        try:
            hasher = hashlib.md5()
            
            # 处理内容
            if isinstance(content, str):
                hasher.update(content.encode('utf-8'))
            elif isinstance(content, bytes):
                hasher.update(content)
            else:
                hasher.update(str(content).encode('utf-8'))
            
            # 处理额外参数
            for arg in args:
                if isinstance(arg, str):
                    hasher.update(arg.encode('utf-8'))
                elif isinstance(arg, bytes):
                    hasher.update(arg)
                else:
                    hasher.update(str(arg).encode('utf-8'))
            
            return hasher.hexdigest()
            
        except Exception as e:
            logger.warning(f"计算内容哈希失败: {e}")
            return ""
    
    def _cleanup_expired(self):
        """清理过期的缓存条目"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
            
        if expired_keys:
            logger.debug(f"清理了 {len(expired_keys)} 个过期缓存条目")
    
    def _manage_size(self):
        """管理缓存大小"""
        if len(self.cache) <= self.max_size:
            return
            
        # 按时间戳排序，移除最旧的条目
        sorted_items = sorted(
            self.cache.items(), 
            key=lambda x: x[1][1]
        )
        
        items_to_keep = sorted_items[-self.max_size:]
        self.cache = dict(items_to_keep)
        
        removed_count = len(sorted_items) - len(items_to_keep)
        if removed_count > 0:
            logger.debug(f"移除了 {removed_count} 个旧缓存条目")
    
    def get(self, content: Union[str, bytes], *args) -> Optional[Any]:
        """
        获取缓存结果
        
        Args:
            content: 内容
            *args: 额外参数
            
        Returns:
            缓存的结果
        """
        if not self.enabled:
            return None
            
        try:
            self._cleanup_expired()
            
            content_hash = self._get_content_hash(content, *args)
            if not content_hash:
                return None
                
            if content_hash in self.cache:
                result, timestamp = self.cache[content_hash]
                if time.time() - timestamp < self.ttl:
                    logger.debug(f"使用内容缓存结果")
                    return result
                else:
                    del self.cache[content_hash]
                    
            return None
            
        except Exception as e:
            logger.warning(f"获取内容缓存失败: {e}")
            return None
    
    def set(self, content: Union[str, bytes], result: Any, *args):
        """
        设置缓存结果
        
        Args:
            content: 内容
            result: 要缓存的结果
            *args: 额外参数
        """
        if not self.enabled:
            return
            
        try:
            content_hash = self._get_content_hash(content, *args)
            if not content_hash:
                return
                
            self.cache[content_hash] = (result, time.time())
            self._manage_size()
            
            logger.debug(f"内容缓存已保存")
            
        except Exception as e:
            logger.warning(f"设置内容缓存失败: {e}")
    
    def clear(self):
        """清空所有缓存"""
        cache_count = len(self.cache)
        self.cache.clear()
        logger.info(f"已清空 {cache_count} 个内容缓存条目")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        current_time = time.time()
        valid_count = sum(
            1 for _, timestamp in self.cache.values()
            if current_time - timestamp < self.ttl
        )
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_count,
            'expired_entries': len(self.cache) - valid_count,
            'ttl': self.ttl,
            'max_size': self.max_size,
            'enabled': self.enabled
        }


class OCRCache(FileHashCache):
    """OCR专用缓存类（继承自FileHashCache）"""
    
    def __init__(self, ttl: int = 3600):
        """
        初始化OCR缓存
        
        Args:
            ttl: 缓存生存时间（秒）
        """
        super().__init__(ttl=ttl, max_size=100)
        
        # 根据设置决定是否启用缓存
        self.enabled = getattr(settings, 'ocr_cache_enabled', True)
    
    def get(self, file_path: str) -> Optional[Tuple[str, float, float]]:
        """
        获取OCR缓存结果
        
        Args:
            file_path: 文件路径
            
        Returns:
            (提取的文本, 置信度, 处理时间) 或 None
        """
        return super().get(file_path)
    
    def set(self, file_path: str, result: Tuple[str, float, float]):
        """
        设置OCR缓存结果
        
        Args:
            file_path: 文件路径
            result: (提取的文本, 置信度, 处理时间)
        """
        super().set(file_path, result)


# 提供便利函数
def create_file_cache(ttl: int = 3600, max_size: int = 100) -> FileHashCache:
    """创建文件哈希缓存"""
    return FileHashCache(ttl=ttl, max_size=max_size)


def create_content_cache(ttl: int = 3600, max_size: int = 100) -> ContentHashCache:
    """创建内容哈希缓存"""
    return ContentHashCache(ttl=ttl, max_size=max_size)


def create_ocr_cache(ttl: int = 3600) -> OCRCache:
    """创建OCR专用缓存"""
    return OCRCache(ttl=ttl)


class FileExtractionCache:
    """文件提取结果缓存"""
    
    def __init__(self, ttl: int = 3600):
        """
        初始化文件提取缓存
        
        Args:
            ttl: 缓存生存时间（秒）
        """
        self.cache: Dict[str, Tuple[str, float, Dict]] = {}  # {hash: (text, timestamp, metadata)}
        self.ttl = ttl
        self.enabled = True
    
    def _get_content_hash(self, content: bytes, filename: str) -> str:
        """
        生成内容哈希值
        
        Args:
            content: 文件内容字节
            filename: 文件名
            
        Returns:
            内容的MD5哈希值
        """
        try:
            hasher = hashlib.md5()
            hasher.update(content)
            hasher.update(filename.encode('utf-8'))
            return hasher.hexdigest()
        except Exception as e:
            logger.warning(f"计算文件内容哈希失败: {e}")
            return ""
    
    def get(self, content: bytes, filename: str) -> Optional[Tuple[str, Dict]]:
        """
        获取缓存的文件提取结果
        
        Args:
            content: 文件内容字节
            filename: 文件名
            
        Returns:
            (提取的文本, 元数据) 或 None
        """
        if not self.enabled:
            return None
            
        try:
            content_hash = self._get_content_hash(content, filename)
            if not content_hash:
                return None
                
            if content_hash in self.cache:
                text, timestamp, metadata = self.cache[content_hash]
                if time.time() - timestamp < self.ttl:
                    logger.info(f"使用缓存的文件提取结果: {filename}")
                    return text, metadata
                else:
                    del self.cache[content_hash]
                    
            return None
            
        except Exception as e:
            logger.warning(f"获取文件提取缓存失败: {e}")
            return None
    
    def set(self, content: bytes, filename: str, text: str, metadata: Dict):
        """
        设置缓存的文件提取结果
        
        Args:
            content: 文件内容字节
            filename: 文件名
            text: 提取的文本
            metadata: 元数据
        """
        if not self.enabled:
            return
            
        try:
            content_hash = self._get_content_hash(content, filename)
            if not content_hash:
                return
                
            self.cache[content_hash] = (text, time.time(), metadata)
            logger.debug(f"文件提取结果已缓存: {filename}")
            
        except Exception as e:
            logger.warning(f"设置文件提取缓存失败: {e}")
    
    def clear(self):
        """清空所有缓存"""
        cache_count = len(self.cache)
        self.cache.clear()
        logger.info(f"已清空 {cache_count} 个文件提取缓存条目")
    
    def enable(self):
        """启用缓存"""
        self.enabled = True
        logger.info("文件提取缓存已启用")
    
    def disable(self):
        """禁用缓存"""
        self.enabled = False
        logger.info("文件提取缓存已禁用")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        current_time = time.time()
        valid_entries = sum(
            1 for _, timestamp, _ in self.cache.values()
            if current_time - timestamp < self.ttl
        )
        
        return {
            'cache_type': 'file_extraction_cache',
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.cache) - valid_entries,
            'ttl_seconds': self.ttl,
            'enabled': self.enabled
        }


def create_file_extraction_cache(ttl: int = 3600) -> FileExtractionCache:
    """创建文件提取缓存"""
    return FileExtractionCache(ttl=ttl) 