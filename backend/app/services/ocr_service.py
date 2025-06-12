import os
import time
import asyncio
import hashlib
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, List, Optional, Dict, Any
import logging
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from pdf2image import convert_from_path
import pytesseract
from app.config import settings

# 导入PaddleOCR相关
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    
logger = logging.getLogger(__name__)

class OCRCache:
    """OCR结果缓存"""
    def __init__(self, ttl: int = 3600):
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl = ttl
    
    def _get_file_hash(self, file_path: str) -> str:
        """获取文件哈希值"""
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5()
            chunk = f.read(8192)
            while chunk:
                file_hash.update(chunk)
                chunk = f.read(8192)
        return file_hash.hexdigest()
    
    def get(self, file_path: str) -> Optional[Tuple[str, float, float]]:
        """获取缓存结果"""
        if not settings.ocr_cache_enabled:
            return None
            
        file_hash = self._get_file_hash(file_path)
        if file_hash in self.cache:
            result, timestamp = self.cache[file_hash]
            if time.time() - timestamp < self.ttl:
                logger.info(f"使用缓存的OCR结果: {file_path}")
                return result
            else:
                del self.cache[file_hash]
        return None
    
    def set(self, file_path: str, result: Tuple[str, float, float]):
        """设置缓存结果"""
        if not settings.ocr_cache_enabled:
            return
            
        file_hash = self._get_file_hash(file_path)
        self.cache[file_hash] = (result, time.time())

class ImagePreprocessor:
    """图像预处理器"""
    
    @staticmethod
    def enhance_image(image: Image.Image) -> Image.Image:
        """图像增强处理"""
        if not settings.ocr_image_enhance:
            return image
            
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
    
    @staticmethod
    def preprocess_for_ocr(image: Image.Image) -> Image.Image:
        """OCR专用预处理"""
        # 图像增强
        enhanced = ImagePreprocessor.enhance_image(image)
        
        # 亮度和对比度调整
        enhancer = ImageEnhance.Contrast(enhanced)
        enhanced = enhancer.enhance(1.2)
        
        enhancer = ImageEnhance.Brightness(enhanced)
        enhanced = enhancer.enhance(1.1)
        
        # 锐化
        enhanced = enhanced.filter(ImageFilter.SHARPEN)
        
        return enhanced

class OCRService:
    def __init__(self):
        self.tesseract_path = settings.tesseract_path
        self.languages = settings.ocr_languages
        self.cache = OCRCache(settings.ocr_cache_ttl)
        self.executor = ThreadPoolExecutor(max_workers=settings.ocr_parallel_pages)
        
        # 配置Tesseract路径
        if os.path.exists(self.tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        # 初始化PaddleOCR
        self.paddle_ocr = None
        if PADDLEOCR_AVAILABLE and settings.ocr_engine in ["paddleocr", "auto"]:
            try:
                # PaddleOCR 3.0版本参数配置 - 准确率优先
                paddle_config = {
                    'lang': settings.paddleocr_lang,
                    'use_doc_orientation_classify': settings.paddleocr_use_angle_cls,
                    'use_doc_unwarping': True,  # 启用文档去弯曲以提升准确率
                    'use_textline_orientation': True  # 启用文本行方向检测以提升准确率
                }
                
                # 根据设置添加模型路径（如果指定）
                if settings.paddleocr_det_model_dir:
                    paddle_config['text_detection_model_dir'] = settings.paddleocr_det_model_dir
                if settings.paddleocr_rec_model_dir:
                    paddle_config['text_recognition_model_dir'] = settings.paddleocr_rec_model_dir
                
                self.paddle_ocr = PaddleOCR(**paddle_config)
                logger.info(f"PaddleOCR初始化成功 (准确率优先模式)")
            except Exception as e:
                logger.warning(f"PaddleOCR初始化失败，回退到Tesseract: {e}")
                self.paddle_ocr = None

        logger.info(f"OCR服务初始化完成，主引擎: {'PaddleOCR' if self.paddle_ocr else 'Tesseract'}")
        
    def pdf_to_images(self, pdf_path: str) -> List[str]:
        """将PDF转换为图片 - 优化版本"""
        try:
            # 转换PDF为图片，使用更高DPI
            images = convert_from_path(
                pdf_path,
                dpi=settings.ocr_image_dpi,
                fmt='PNG',
                thread_count=4,  # 多线程转换
                use_pdftocairo=True  # 使用更快的渲染引擎
            )
            
            image_paths = []
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            
            for i, image in enumerate(images):
                # 预处理图像
                if settings.ocr_image_enhance:
                    image = ImagePreprocessor.preprocess_for_ocr(image)
                
                image_path = os.path.join(
                    settings.upload_dir,
                    f"{base_name}_page_{i+1}.png"
                )
                image.save(image_path, 'PNG', optimize=True)
                image_paths.append(image_path)
                
            logger.info(f"PDF转换完成，共{len(image_paths)}页，DPI: {settings.ocr_image_dpi}")
            return image_paths
            
        except Exception as e:
            logger.error(f"PDF转换失败: {e}")
            raise Exception(f"PDF转换失败: {str(e)}")

    def extract_text_paddleocr(self, image_path: str) -> Tuple[str, float]:
        """使用PaddleOCR提取文本"""
        try:
            # PaddleOCR 3.0版本识别
            result = self.paddle_ocr.predict(image_path)
            
            if not result or not result[0] or not result[0].get('rec_texts'):
                return "", 0.0
            
            # 提取文本和置信度 - 直接从结果字典获取
            res = result[0]
            texts = res['rec_texts']
            scores = res.get('rec_scores', [])
            
            # 合并文本
            full_text = '\n'.join(texts)
            avg_confidence = sum(scores) / len(scores) if scores else 0.0
            
            return full_text.strip(), avg_confidence
            
        except Exception as e:
            logger.error(f"PaddleOCR提取文本失败: {e}")
            raise Exception(f"PaddleOCR提取失败: {str(e)}")

    def extract_text_tesseract(self, image_path: str) -> Tuple[str, float]:
        """使用Tesseract提取文本 - 准确率优先版本"""
        try:
            image = Image.open(image_path)
            
            # 图像预处理
            if settings.ocr_image_enhance:
                image = ImagePreprocessor.preprocess_for_ocr(image)
            
            # 统一使用准确率优先配置：OEM 3 + PSM 6，移除字符白名单限制
            custom_config = r'--oem 3 --psm 6'
            
            # 获取文本
            text = pytesseract.image_to_string(
                image,
                lang=self.languages,
                config=custom_config
            )
            
            # 获取详细信息以计算置信度
            data = pytesseract.image_to_data(
                image,
                lang=self.languages,
                output_type=pytesseract.Output.DICT,
                config=custom_config
            )
            
            # 计算平均置信度
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            
            return text.strip(), avg_confidence
            
        except Exception as e:
            logger.error(f"Tesseract提取文本失败: {e}")
            raise Exception(f"Tesseract OCR提取失败: {str(e)}")
    
    async def extract_text_from_image(self, image_path: str) -> Tuple[str, float, float]:
        """从图片提取文本 - 优化版本"""
        start_time = time.time()
        
        # 检查缓存
        cached_result = self.cache.get(image_path)
        if cached_result:
            return cached_result
        
        try:
            # 智能引擎选择 - 准确率优先
            if self.paddle_ocr and settings.ocr_engine in ["paddleocr"]:
                # 使用PaddleOCR
                text, confidence = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self.extract_text_paddleocr, image_path
                )
                engine_used = "PaddleOCR"
            else:
                # 使用Tesseract
                text, confidence = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self.extract_text_tesseract, image_path
                )
                engine_used = "Tesseract"
            
            processing_time = time.time() - start_time
            result = (text, confidence, processing_time)
            
            # 缓存结果
            self.cache.set(image_path, result)
            
            logger.info(f"OCR完成 ({engine_used})，置信度: {confidence:.2f}, 耗时: {processing_time:.2f}秒")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"文本提取失败: {e}")
            raise Exception(f"文本提取失败: {str(e)}")
    
    async def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, float, float]:
        """从PDF提取文本 - 并行优化版本"""
        start_time = time.time()
        
        # 检查缓存
        cached_result = self.cache.get(pdf_path)
        if cached_result:
            return cached_result
        
        try:
            # 将PDF转换为图片
            image_paths = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.pdf_to_images, pdf_path
            )
            
            # 并行处理所有页面
            tasks = []
            for image_path in image_paths:
                task = self.extract_text_from_image(image_path)
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_texts = []
            all_confidences = []
            
            # 处理结果并清理临时文件
            for i, (image_path, result) in enumerate(zip(image_paths, results)):
                try:
                    # 清理临时图片文件
                    if os.path.exists(image_path):
                        os.remove(image_path)
                    
                    if isinstance(result, Exception):
                        logger.error(f"处理页面 {i+1} 失败: {result}")
                        continue
                        
                    text, confidence, _ = result
                    if text.strip():
                        all_texts.append(f"--- 第{i+1}页 ---\n{text}")
                        all_confidences.append(confidence)
                        
                except Exception as e:
                    logger.error(f"清理页面 {i+1} 失败: {e}")
                    continue
            
            # 合并所有文本
            full_text = '\n\n'.join(all_texts)
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            processing_time = time.time() - start_time
            
            result = (full_text, avg_confidence, processing_time)
            
            # 缓存结果
            self.cache.set(pdf_path, result)
            
            engine_used = "PaddleOCR" if self.paddle_ocr else "Tesseract"
            logger.info(f"PDF OCR完成 ({engine_used})，共{len(all_texts)}页，平均置信度: {avg_confidence:.2f}，总耗时: {processing_time:.2f}秒")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"PDF文本提取失败: {e}")
            raise Exception(f"PDF文本提取失败: {str(e)}")

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

# 创建全局服务实例
ocr_service = OCRService() 