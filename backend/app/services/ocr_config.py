"""
OCR服务配置文件 - Apple Silicon优化版本

本文件包含OCR服务的详细配置选项，特别优化了Apple Silicon的性能。
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class PaddleOCRConfig:
    """PaddleOCR配置"""
    # 基础配置
    lang: str = "ch"  # 语言：ch, en, japan, korean等
    use_gpu: bool = True  # 使用GPU加速
    use_angle_cls: bool = True  # 文字方向分类
    
    # 模型路径（None表示使用默认）
    det_model_dir: Optional[str] = None  # 检测模型路径
    rec_model_dir: Optional[str] = None  # 识别模型路径
    cls_model_dir: Optional[str] = None  # 分类模型路径
    
    # 性能优化
    det_db_thresh: float = 0.3  # 文本检测阈值
    det_db_box_thresh: float = 0.6  # 文本框阈值
    det_db_unclip_ratio: float = 1.5  # 文本框扩展比例
    
    # Apple Silicon特定优化
    use_mkldnn: bool = True  # 使用Intel MKL-DNN优化
    cpu_threads: int = 8  # CPU线程数
    enable_mkldnn: bool = True  # 启用MKLDNN
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'lang': self.lang,
            'use_gpu': self.use_gpu,
            'use_angle_cls': self.use_angle_cls,
            'det_model_dir': self.det_model_dir,
            'rec_model_dir': self.rec_model_dir,
            'cls_model_dir': self.cls_model_dir,
            'det_db_thresh': self.det_db_thresh,
            'det_db_box_thresh': self.det_db_box_thresh,
            'det_db_unclip_ratio': self.det_db_unclip_ratio,
            'use_mkldnn': self.use_mkldnn,
            'cpu_threads': self.cpu_threads,
            'enable_mkldnn': self.enable_mkldnn,
            'show_log': False
        }

@dataclass
class TesseractConfig:
    """Tesseract配置"""
    # 基础配置
    lang: str = "chi_sim+eng"  # 语言
    oem: int = 3  # OCR引擎模式
    psm: int = 6  # 页面分割模式
    
    # 中文优化配置
    char_whitelist: str = (
        "0123456789"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        "一二三四五六七八九十百千万亿"
        "的在是了不了有大这个人们我们他们我你她它"
        "是的得地都能会要可以上下左右前后来去进出"
        "东西南北年月日时分秒"
    )
    
    # 性能配置
    timeout: int = 30  # 超时时间（秒）
    
    def get_config_string(self) -> str:
        """获取Tesseract配置字符串"""
        return f'--oem {self.oem} --psm {self.psm} -c tessedit_char_whitelist={self.char_whitelist}'

@dataclass
class ImageProcessConfig:
    """图像处理配置"""
    # PDF转换配置
    pdf_dpi: int = 300  # PDF转图片DPI
    pdf_format: str = "PNG"  # 图片格式
    use_pdftocairo: bool = True  # 使用pdftocairo
    thread_count: int = 4  # 转换线程数
    
    # 图像增强配置
    enable_enhancement: bool = True  # 启用图像增强
    contrast_factor: float = 1.2  # 对比度增强因子
    brightness_factor: float = 1.1  # 亮度增强因子
    
    # 去噪配置
    denoise_strength: int = 10  # 去噪强度
    
    # CLAHE配置
    clahe_clip_limit: float = 2.0  # CLAHE限制
    clahe_tile_grid_size: tuple = (8, 8)  # CLAHE网格大小

@dataclass
class PerformanceConfig:
    """性能配置"""
    # 并发配置
    max_workers: int = 4  # 最大工作线程数
    parallel_pages: int = 4  # 并行处理页数
    
    # 缓存配置
    enable_cache: bool = True  # 启用缓存
    cache_ttl: int = 3600  # 缓存时间（秒）
    max_cache_size: int = 100  # 最大缓存条目数
    
    # Apple Silicon优化
    use_mps: bool = True  # 使用MPS
    mps_memory_fraction: float = 0.8  # MPS内存占用比例
    
    # 内存管理
    cleanup_temp_files: bool = True  # 清理临时文件
    gc_threshold: int = 100  # 垃圾回收阈值

class OCRConfigManager:
    """OCR配置管理器"""
    
    def __init__(self):
        self.paddleocr_config = PaddleOCRConfig()
        self.tesseract_config = TesseractConfig()
        self.image_config = ImageProcessConfig()
        self.performance_config = PerformanceConfig()
    
    def get_apple_silicon_optimized_config(self) -> Dict[str, Any]:
        """获取Apple Silicon优化配置"""
        return {
            "paddleocr": self.paddleocr_config.to_dict(),
            "tesseract": {
                "lang": self.tesseract_config.lang,
                "config": self.tesseract_config.get_config_string(),
                "timeout": self.tesseract_config.timeout
            },
            "image_processing": {
                "pdf_dpi": self.image_config.pdf_dpi,
                "enhancement": self.image_config.enable_enhancement,
                "thread_count": self.image_config.thread_count
            },
            "performance": {
                "max_workers": self.performance_config.max_workers,
                "use_mps": self.performance_config.use_mps,
                "cache_enabled": self.performance_config.enable_cache
            }
        }
    
    def update_config_from_settings(self, settings):
        """从设置更新配置"""
        # 更新PaddleOCR配置
        if hasattr(settings, 'paddleocr_lang'):
            self.paddleocr_config.lang = settings.paddleocr_lang
        if hasattr(settings, 'paddleocr_use_gpu'):
            self.paddleocr_config.use_gpu = settings.paddleocr_use_gpu
        if hasattr(settings, 'paddleocr_use_angle_cls'):
            self.paddleocr_config.use_angle_cls = settings.paddleocr_use_angle_cls
        
        # 更新Tesseract配置
        if hasattr(settings, 'ocr_languages'):
            self.tesseract_config.lang = settings.ocr_languages
        
        # 更新图像处理配置
        if hasattr(settings, 'ocr_image_dpi'):
            self.image_config.pdf_dpi = settings.ocr_image_dpi
        if hasattr(settings, 'ocr_image_enhance'):
            self.image_config.enable_enhancement = settings.ocr_image_enhance
        
        # 更新性能配置
        if hasattr(settings, 'ocr_parallel_pages'):
            self.performance_config.max_workers = settings.ocr_parallel_pages
            self.performance_config.parallel_pages = settings.ocr_parallel_pages
        if hasattr(settings, 'ocr_cache_enabled'):
            self.performance_config.enable_cache = settings.ocr_cache_enabled
        if hasattr(settings, 'ocr_cache_ttl'):
            self.performance_config.cache_ttl = settings.ocr_cache_ttl
        if hasattr(settings, 'use_mps'):
            self.performance_config.use_mps = settings.use_mps

# 全局配置管理器实例
ocr_config_manager = OCRConfigManager()

# Apple Silicon优化建议
APPLE_SILICON_OPTIMIZATION_TIPS = {
    "硬件优化": [
        "确保系统有足够的内存（建议16GB+）",
        "使用SSD存储以加快文件I/O",
        "保持系统温度较低以维持最佳性能"
    ],
    "软件优化": [
        "使用最新版本的Python（3.9+）",
        "安装优化的深度学习库",
        "配置正确的Metal Performance Shaders"
    ],
    "配置优化": [
        "启用GPU加速（PaddleOCR）",
        "调整并行处理线程数",
        "优化缓存设置",
        "使用适当的图像DPI"
    ],
    "性能监控": [
        "监控内存使用情况",
        "检查GPU利用率",
        "测量处理时间",
        "优化批处理大小"
    ]
}

def print_optimization_tips():
    """打印优化建议"""
    print("=== Apple Silicon OCR优化建议 ===")
    for category, tips in APPLE_SILICON_OPTIMIZATION_TIPS.items():
        print(f"\n{category}:")
        for tip in tips:
            print(f"  • {tip}")
    print("\n" + "="*40) 