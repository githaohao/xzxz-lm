#!/usr/bin/env python3
"""
图像处理工具类
包含图像增强、预处理等功能
"""

import cv2
import numpy as np
import logging
from PIL import Image, ImageEnhance, ImageFilter
from app.config import settings

logger = logging.getLogger(__name__)


class ImageProcessor:
    """图像处理工具类"""
    
    @staticmethod
    def enhance_image(image: Image.Image) -> Image.Image:
        """
        图像增强处理
        
        Args:
            image: PIL图像对象
            
        Returns:
            增强后的图像
        """
        if not settings.ocr_image_enhance:
            return image
            
        try:
            # 转换为RGB模式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 转换为OpenCV格式
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # 1. 去噪
            cv_image = cv2.fastNlMeansDenoisingColored(cv_image, None, 10, 10, 7, 21)
            
            # 2. 锐化
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            cv_image = cv2.filter2D(cv_image, -1, kernel)
            
            # 3. 对比度自适应均衡化
            lab = cv2.cvtColor(cv_image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            cv_image = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
            
            # 转换回PIL格式
            return Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
            
        except Exception as e:
            logger.warning(f"图像增强失败，返回原图像: {e}")
            return image
    
    @staticmethod
    def preprocess_for_ocr(image: Image.Image) -> Image.Image:
        """
        OCR专用预处理
        
        Args:
            image: PIL图像对象
            
        Returns:
            预处理后的图像
        """
        try:
            # 图像增强
            enhanced = ImageProcessor.enhance_image(image)
            
            # 亮度和对比度调整
            enhancer = ImageEnhance.Contrast(enhanced)
            enhanced = enhancer.enhance(1.2)
            
            enhancer = ImageEnhance.Brightness(enhanced)
            enhanced = enhancer.enhance(1.1)
            
            # 锐化
            enhanced = enhanced.filter(ImageFilter.SHARPEN)
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"OCR预处理失败，返回原图像: {e}")
            return image
    
    @staticmethod
    def convert_to_grayscale(image: Image.Image) -> Image.Image:
        """
        转换为灰度图像
        
        Args:
            image: PIL图像对象
            
        Returns:
            灰度图像
        """
        try:
            return image.convert('L')
        except Exception as e:
            logger.warning(f"灰度转换失败，返回原图像: {e}")
            return image
    
    @staticmethod
    def apply_gaussian_blur(image: Image.Image, radius: float = 1.0) -> Image.Image:
        """
        应用高斯模糊
        
        Args:
            image: PIL图像对象
            radius: 模糊半径
            
        Returns:
            模糊后的图像
        """
        try:
            return image.filter(ImageFilter.GaussianBlur(radius=radius))
        except Exception as e:
            logger.warning(f"高斯模糊失败，返回原图像: {e}")
            return image
    
    @staticmethod
    def adjust_brightness_contrast(
        image: Image.Image, 
        brightness: float = 1.1, 
        contrast: float = 1.2
    ) -> Image.Image:
        """
        调整亮度和对比度
        
        Args:
            image: PIL图像对象
            brightness: 亮度因子（1.0为原始亮度）
            contrast: 对比度因子（1.0为原始对比度）
            
        Returns:
            调整后的图像
        """
        try:
            # 调整对比度
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(contrast)
            
            # 调整亮度
            enhancer = ImageEnhance.Brightness(enhanced)
            enhanced = enhancer.enhance(brightness)
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"亮度对比度调整失败，返回原图像: {e}")
            return image
    
    @staticmethod
    def detect_image_orientation(image: Image.Image) -> int:
        """
        检测图像方向
        
        Args:
            image: PIL图像对象
            
        Returns:
            旋转角度（0, 90, 180, 270）
        """
        try:
            # 简单的方向检测逻辑
            width, height = image.size
            
            # 如果宽度明显大于高度，可能需要旋转
            if width > height * 1.5:
                return 90
            elif height > width * 1.5:
                return 0
            else:
                return 0
                
        except Exception as e:
            logger.warning(f"图像方向检测失败: {e}")
            return 0
    
    @staticmethod
    def auto_rotate_image(image: Image.Image) -> Image.Image:
        """
        自动旋转图像到正确方向
        
        Args:
            image: PIL图像对象
            
        Returns:
            旋转后的图像
        """
        try:
            rotation_angle = ImageProcessor.detect_image_orientation(image)
            
            if rotation_angle != 0:
                return image.rotate(-rotation_angle, expand=True)
            else:
                return image
                
        except Exception as e:
            logger.warning(f"自动旋转失败，返回原图像: {e}")
            return image
    
    @staticmethod
    def resize_for_processing(
        image: Image.Image, 
        max_width: int = 2048, 
        max_height: int = 2048
    ) -> Image.Image:
        """
        调整图像大小以优化处理性能
        
        Args:
            image: PIL图像对象
            max_width: 最大宽度
            max_height: 最大高度
            
        Returns:
            调整大小后的图像
        """
        try:
            width, height = image.size
            
            # 如果图像尺寸在限制范围内，直接返回
            if width <= max_width and height <= max_height:
                return image
            
            # 计算缩放比例
            scale_width = max_width / width
            scale_height = max_height / height
            scale = min(scale_width, scale_height)
            
            # 计算新尺寸
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # 使用LANCZOS算法进行高质量缩放
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        except Exception as e:
            logger.warning(f"图像大小调整失败，返回原图像: {e}")
            return image


# 提供便利函数
def enhance_image(image: Image.Image) -> Image.Image:
    """图像增强便利函数"""
    return ImageProcessor.enhance_image(image)


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """OCR预处理便利函数"""
    return ImageProcessor.preprocess_for_ocr(image)


def adjust_brightness_contrast(
    image: Image.Image, 
    brightness: float = 1.1, 
    contrast: float = 1.2
) -> Image.Image:
    """亮度对比度调整便利函数"""
    return ImageProcessor.adjust_brightness_contrast(image, brightness, contrast)


def resize_for_processing(
    image: Image.Image, 
    max_width: int = 2048, 
    max_height: int = 2048
) -> Image.Image:
    """图像大小调整便利函数"""
    return ImageProcessor.resize_for_processing(image, max_width, max_height) 