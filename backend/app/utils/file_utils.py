#!/usr/bin/env python3
"""
文件处理工具类
包含文件类型检测、文件处理等功能
"""

import mimetypes
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FileTypeDetector:
    """文件类型检测工具类"""
    
    # 支持的文件类型映射
    SUPPORTED_TYPES = {
        # PDF文件
        'application/pdf': 'PDF文档',
        
        # 文本文件
        'text/plain': '文本文件',
        
        # Word文档
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word文档 (.docx)',
        'application/msword': 'Word文档 (.doc)',
        
        # 图片文件（需要OCR）
        'image/png': 'PNG图片',
        'image/jpeg': 'JPEG图片',
        'image/jpg': 'JPG图片',
        'image/bmp': 'BMP图片',
        'image/tiff': 'TIFF图片',
        'image/webp': 'WebP图片',
        
        # 音频文件（占位符，未来可扩展语音识别）
        'audio/wav': 'WAV音频文件',
        'audio/mpeg': 'MP3音频文件',
        'audio/mp3': 'MP3音频文件'
    }
    
    @staticmethod
    def detect_file_type(file_content: bytes, filename: str) -> str:
        """
        检测文件类型
        
        Args:
            file_content: 文件内容字节
            filename: 文件名
            
        Returns:
            文件的MIME类型
        """
        try:
            # 先尝试根据文件名检测
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type:
                return mime_type
            
            # 检查文件签名（魔数）
            if file_content.startswith(b'%PDF'):
                return 'application/pdf'
            elif file_content.startswith(b'PK\x03\x04'):
                # 检查是否是DOCX文件
                if b'word/' in file_content[:1024]:
                    return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif file_content.startswith((b'\xff\xd8\xff', b'\x89PNG')):
                # JPEG或PNG图片
                return 'image/jpeg' if file_content.startswith(b'\xff\xd8\xff') else 'image/png'
            elif file_content.startswith(b'\x89PNG\r\n\x1a\n'):
                return 'image/png'
            elif file_content.startswith(b'GIF87a') or file_content.startswith(b'GIF89a'):
                return 'image/gif'
            elif file_content.startswith(b'BM'):
                return 'image/bmp'
            elif file_content.startswith((b'II*\x00', b'MM\x00*')):
                return 'image/tiff'
            elif file_content.startswith(b'RIFF') and b'WEBP' in file_content[:12]:
                return 'image/webp'
            elif file_content.startswith(b'RIFF') and b'WAVE' in file_content[:12]:
                return 'audio/wav'
            elif file_content.startswith((b'ID3', b'\xff\xfb', b'\xff\xf3', b'\xff\xf2')):
                return 'audio/mpeg'
            elif file_content.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
                # Microsoft Office 老格式 (.doc, .xls, .ppt)
                if filename.lower().endswith('.doc'):
                    return 'application/msword'
                elif filename.lower().endswith('.xls'):
                    return 'application/vnd.ms-excel'
                elif filename.lower().endswith('.ppt'):
                    return 'application/vnd.ms-powerpoint'
            
            # 尝试检测文本文件
            try:
                # 检查前1024字节是否为有效文本
                sample = file_content[:1024]
                sample.decode('utf-8')
                return 'text/plain'
            except UnicodeDecodeError:
                pass
            
            # 默认返回二进制文件类型
            return 'application/octet-stream'
            
        except Exception as e:
            logger.warning(f"文件类型检测失败 {filename}: {e}")
            return 'application/octet-stream'
    
    @staticmethod
    def get_supported_file_types() -> Dict[str, str]:
        """
        获取支持的文件类型映射
        
        Returns:
            文件类型映射字典 {mime_type: description}
        """
        return FileTypeDetector.SUPPORTED_TYPES.copy()
    
    @staticmethod
    def is_supported_file_type(file_type: str) -> bool:
        """
        检查文件类型是否支持
        
        Args:
            file_type: 文件MIME类型
            
        Returns:
            是否支持该文件类型
        """
        return file_type in FileTypeDetector.SUPPORTED_TYPES
    
    @staticmethod
    def get_file_category(file_type: str) -> str:
        """
        获取文件类别
        
        Args:
            file_type: 文件MIME类型
            
        Returns:
            文件类别 (document, image, audio, text, other)
        """
        if file_type.startswith('application/pdf') or \
           file_type.startswith('application/vnd.openxmlformats-officedocument') or \
           file_type.startswith('application/msword'):
            return 'document'
        elif file_type.startswith('image/'):
            return 'image'
        elif file_type.startswith('audio/'):
            return 'audio'
        elif file_type.startswith('text/'):
            return 'text'
        else:
            return 'other'
    
    @staticmethod
    def get_file_extension_from_mime(mime_type: str) -> str:
        """
        根据MIME类型获取推荐的文件扩展名
        
        Args:
            mime_type: MIME类型
            
        Returns:
            文件扩展名（包含点号）
        """
        extension_map = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/msword': '.doc',
            'text/plain': '.txt',
            'image/png': '.png',
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'image/tiff': '.tiff',
            'image/webp': '.webp',
            'audio/wav': '.wav',
            'audio/mpeg': '.mp3',
            'audio/mp3': '.mp3'
        }
        
        return extension_map.get(mime_type, '')
    
    @staticmethod
    def validate_file_size(file_content: bytes, max_size_mb: int = 50) -> bool:
        """
        验证文件大小
        
        Args:
            file_content: 文件内容字节
            max_size_mb: 最大文件大小（MB）
            
        Returns:
            文件大小是否在允许范围内
        """
        file_size_mb = len(file_content) / (1024 * 1024)
        return file_size_mb <= max_size_mb
    
    @staticmethod
    def get_file_info(file_content: bytes, filename: str) -> Dict[str, any]:
        """
        获取文件基本信息
        
        Args:
            file_content: 文件内容字节
            filename: 文件名
            
        Returns:
            文件信息字典
        """
        file_type = FileTypeDetector.detect_file_type(file_content, filename)
        file_size = len(file_content)
        file_category = FileTypeDetector.get_file_category(file_type)
        is_supported = FileTypeDetector.is_supported_file_type(file_type)
        
        return {
            'filename': filename,
            'file_type': file_type,
            'file_size': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'file_category': file_category,
            'is_supported': is_supported,
            'description': FileTypeDetector.SUPPORTED_TYPES.get(file_type, '未知文件类型')
        }


# 便利函数
def detect_file_type(file_content: bytes, filename: str) -> str:
    """检测文件类型"""
    return FileTypeDetector.detect_file_type(file_content, filename)


def get_supported_file_types() -> Dict[str, str]:
    """获取支持的文件类型"""
    return FileTypeDetector.get_supported_file_types()


def is_supported_file_type(file_type: str) -> bool:
    """检查文件类型是否支持"""
    return FileTypeDetector.is_supported_file_type(file_type)


def get_file_category(file_type: str) -> str:
    """获取文件类别"""
    return FileTypeDetector.get_file_category(file_type)


def get_file_info(file_content: bytes, filename: str) -> Dict[str, any]:
    """获取文件基本信息"""
    return FileTypeDetector.get_file_info(file_content, filename)


def validate_file_size(file_content: bytes, max_size_mb: int = 50) -> bool:
    """验证文件大小"""
    return FileTypeDetector.validate_file_size(file_content, max_size_mb) 