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
import PyPDF2
from app.config import settings
from app.utils import ImageProcessor, OCRCache

# 导入PaddleOCR相关
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    
logger = logging.getLogger(__name__)

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
                    image = ImageProcessor.preprocess_for_ocr(image)
                
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
                image = ImageProcessor.preprocess_for_ocr(image)
            
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

    async def extract_full_pdf_text(self, pdf_path: str) -> str:
        """
        提取PDF的完整文本内容（用于RAG处理）
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            str: 提取的完整文本内容
        """
        try:
            logger.info(f"开始提取PDF完整文本内容: {pdf_path}")
            
            # 使用PyPDF2提取所有页面的文本
            extracted_text = ""
            failed_pages = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                logger.info(f"PDF总页数: {page_count}")
                
                # 如果页数太多，给出警告但仍然处理
                if page_count > 100:
                    logger.warning(f"PDF页数较多({page_count}页)，提取可能需要较长时间")
                
                for i in range(page_count):
                    try:
                        page = pdf_reader.pages[i]
                        page_text = page.extract_text()
                        
                        if page_text and page_text.strip():
                            # 为每页添加页面标识，便于后续处理
                            extracted_text += f"\n--- 第{i+1}页 ---\n{page_text.strip()}\n"
                        else:
                            logger.debug(f"第{i+1}页无文本内容")
                        
                        # 每处理10页记录一次进度
                        if (i + 1) % 10 == 0:
                            logger.info(f"已处理 {i+1}/{page_count} 页")
                            
                    except Exception as e:
                        logger.warning(f"提取第{i+1}页文本失败: {e}")
                        failed_pages.append(i+1)
                        continue
            
            # 清理和验证文本
            clean_text = extracted_text.strip()
            char_count = len(clean_text)
            
            # 记录提取结果统计
            success_pages = page_count - len(failed_pages)
            success_rate = (success_pages / page_count) * 100 if page_count > 0 else 0
            
            logger.info(f"✅ PDF完整文本提取完成")
            logger.info(f"   - 总页数: {page_count}")
            logger.info(f"   - 成功页数: {success_pages}")
            logger.info(f"   - 成功率: {success_rate:.1f}%")
            logger.info(f"   - 总字符数: {char_count}")
            
            if failed_pages:
                logger.warning(f"   - 失败页面: {failed_pages}")
            
            # 如果提取的文本太少，可能存在问题
            if char_count < 100:
                logger.warning(f"提取的文本内容较少({char_count}字符)，可能需要OCR处理")
                
            return clean_text
            
        except Exception as e:
            logger.error(f"PDF完整文本提取失败: {e}")
            return ""

    async def detect_pdf_text_content(self, pdf_path: str) -> Tuple[bool, str, int]:
        """
        检测PDF是否包含可提取的文本内容
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            Tuple[bool, str, int]: (是否为文本PDF, 提取的文本内容, 字符数量)
        """
        try:
            logger.info(f"开始检测PDF文本内容: {pdf_path}")
            
            # 使用PyPDF2尝试提取文本
            extracted_text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                # 提取前3页的文本进行检测（避免处理过长的文档）
                max_pages_to_check = min(3, page_count)
                
                for i in range(max_pages_to_check):
                    try:
                        page = pdf_reader.pages[i]
                        page_text = page.extract_text()
                        if page_text:
                            extracted_text += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"提取第{i+1}页文本失败: {e}")
                        continue
            
            # 清理文本并计算有效字符数
            clean_text = extracted_text.strip()
            char_count = len(clean_text)
            
            # 判断是否为文本PDF的标准：
            # 1. 提取的文本长度 > 50个字符
            # 2. 文本中包含有意义的词语（不全是符号）
            # 3. 字符密度合理（避免乱码文档）
            is_text_pdf = False
            
            if char_count >= 50:
                # 检查文本质量
                # 计算字母数字字符的比例
                alphanumeric_count = sum(1 for c in clean_text if c.isalnum() or c.isspace())
                alphanumeric_ratio = alphanumeric_count / char_count if char_count > 0 else 0
                
                # 检查是否包含中文字符
                chinese_count = sum(1 for c in clean_text if '\u4e00' <= c <= '\u9fff')
                chinese_ratio = chinese_count / char_count if char_count > 0 else 0
                
                # 如果字母数字字符比例 > 60% 或者中文字符比例 > 20%，认为是文本PDF
                if alphanumeric_ratio > 0.6 or chinese_ratio > 0.2:
                    is_text_pdf = True
                    logger.info(f"✅ 检测为文本PDF，字符数: {char_count}, 字母数字比例: {alphanumeric_ratio:.2f}, 中文比例: {chinese_ratio:.2f}")
                else:
                    logger.info(f"⚠️ PDF包含文本但质量不高，字符数: {char_count}, 字母数字比例: {alphanumeric_ratio:.2f}, 中文比例: {chinese_ratio:.2f}")
            else:
                logger.info(f"🔍 检测为扫描PDF，提取文本字符数过少: {char_count}")
            
            return is_text_pdf, clean_text, char_count
            
        except Exception as e:
            logger.error(f"PDF文本检测失败: {e}")
            # 检测失败时，默认认为是扫描PDF，需要OCR处理
            return False, "", 0

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

# 创建全局服务实例
ocr_service = OCRService()