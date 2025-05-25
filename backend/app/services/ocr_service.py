import os
import time
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from typing import Tuple, List, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self.use_paddleocr = False  # 暂时禁用PaddleOCR
        self.tesseract_path = settings.tesseract_path
        self.languages = settings.ocr_languages
        
        # 配置Tesseract路径
        if os.path.exists(self.tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        logger.info("OCR服务初始化完成，使用Tesseract引擎")
        
    def pdf_to_images(self, pdf_path: str) -> List[str]:
        """将PDF转换为图片"""
        try:
            # 转换PDF为图片
            images = convert_from_path(
                pdf_path,
                dpi=300,  # 高DPI以获得更好的OCR效果
                fmt='PNG'
            )
            
            image_paths = []
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            
            for i, image in enumerate(images):
                image_path = os.path.join(
                    settings.upload_dir,
                    f"{base_name}_page_{i+1}.png"
                )
                image.save(image_path, 'PNG')
                image_paths.append(image_path)
                
            logger.info(f"PDF转换完成，共{len(image_paths)}页")
            return image_paths
            
        except Exception as e:
            logger.error(f"PDF转换失败: {e}")
            raise Exception(f"PDF转换失败: {str(e)}")
    

    def extract_text_tesseract(self, image_path: str) -> Tuple[str, float]:
        """使用Tesseract提取文本"""
        try:
            image = Image.open(image_path)
            
            # 获取文本和置信度
            text = pytesseract.image_to_string(
                image,
                lang=self.languages,
                config='--psm 6'  # 假设一列均匀间隔的文本
            )
            
            # 获取详细信息以计算置信度
            data = pytesseract.image_to_data(
                image,
                lang=self.languages,
                output_type=pytesseract.Output.DICT
            )
            
            # 计算平均置信度
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            
            return text.strip(), avg_confidence
            
        except Exception as e:
            logger.error(f"Tesseract提取文本失败: {e}")
            raise Exception(f"OCR提取失败: {str(e)}")
    
    async def extract_text_from_image(self, image_path: str) -> Tuple[str, float, float]:
        """从图片提取文本"""
        start_time = time.time()
        
        try:
            text, confidence = self.extract_text_tesseract(image_path)
            processing_time = time.time() - start_time
            
            logger.info(f"OCR完成，置信度: {confidence:.2f}, 耗时: {processing_time:.2f}秒")
            return text, confidence, processing_time
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"文本提取失败: {e}")
            raise Exception(f"文本提取失败: {str(e)}")
    
    async def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, float, float]:
        """从PDF提取文本"""
        start_time = time.time()
        
        try:
            # 首先将PDF转换为图片
            image_paths = self.pdf_to_images(pdf_path)
            
            all_texts = []
            all_confidences = []
            
            # 对每一页进行OCR
            for image_path in image_paths:
                try:
                    text, confidence, _ = await self.extract_text_from_image(image_path)
                    if text.strip():
                        all_texts.append(text)
                        all_confidences.append(confidence)
                    
                    # 清理临时图片文件
                    os.remove(image_path)
                    
                except Exception as e:
                    logger.error(f"处理页面 {image_path} 失败: {e}")
                    continue
            
            # 合并所有文本
            full_text = '\n\n'.join(all_texts)
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            processing_time = time.time() - start_time
            
            logger.info(f"PDF OCR完成，共{len(all_texts)}页，平均置信度: {avg_confidence:.2f}")
            return full_text, avg_confidence, processing_time
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"PDF文本提取失败: {e}")
            raise Exception(f"PDF文本提取失败: {str(e)}")

# 创建全局服务实例
ocr_service = OCRService() 