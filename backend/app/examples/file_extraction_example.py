"""
文件提取服务使用示例
演示如何在项目中使用统一的文件提取服务
"""

import asyncio
from typing import List, Dict, Any
from app.services.file_extraction_service import file_extraction_service
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """文档处理器示例类"""
    
    def __init__(self):
        self.extraction_service = file_extraction_service
    
    async def process_uploaded_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        处理上传的文件
        
        Args:
            file_content: 文件内容
            filename: 文件名
            
        Returns:
            Dict: 处理结果
        """
        try:
            # 检查文件类型是否支持
            file_type = self.extraction_service._detect_file_type(file_content, filename)
            
            if not self.extraction_service.is_supported_file_type(file_type):
                return {
                    "status": "error",
                    "message": f"不支持的文件类型: {file_type}",
                    "filename": filename
                }
            
            # 提取文本内容
            extracted_text, metadata = await self.extraction_service.extract_text_from_file(
                file_content, filename, file_type
            )
            
            # 进行后续处理
            processed_result = await self._post_process_text(extracted_text, metadata)
            
            return {
                "status": "success",
                "filename": filename,
                "extracted_text": extracted_text,
                "metadata": metadata,
                "processed_result": processed_result
            }
            
        except Exception as e:
            logger.error(f"文件处理失败: {e}")
            return {
                "status": "error",
                "message": str(e),
                "filename": filename
            }
    
    async def _post_process_text(self, text: str, metadata: Dict) -> Dict[str, Any]:
        """
        对提取的文本进行后处理
        
        Args:
            text: 提取的文本
            metadata: 提取元数据
            
        Returns:
            Dict: 处理结果
        """
        # 文本质量分析
        quality_score = self._analyze_text_quality(text, metadata)
        
        # 关键信息提取
        key_info = self._extract_key_information(text)
        
        # 文本分类
        category = self._classify_document(text, metadata)
        
        return {
            "quality_score": quality_score,
            "key_information": key_info,
            "document_category": category,
            "word_count": len(text.split()) if text else 0,
            "char_count": len(text) if text else 0
        }
    
    def _analyze_text_quality(self, text: str, metadata: Dict) -> float:
        """分析文本质量"""
        if not text:
            return 0.0
        
        # 基础质量分析
        quality_score = 0.5  # 基础分数
        
        # OCR置信度影响质量
        if 'confidence' in metadata:
            confidence = metadata['confidence']
            quality_score = quality_score * 0.3 + confidence * 0.7
        
        # 文本长度影响质量
        text_length = len(text)
        if text_length > 100:
            quality_score += 0.1
        if text_length > 1000:
            quality_score += 0.1
        
        # 中文内容检测
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        if chinese_chars > 0:
            quality_score += 0.1
        
        return min(1.0, quality_score)
    
    def _extract_key_information(self, text: str) -> Dict[str, Any]:
        """提取关键信息"""
        import re
        
        key_info = {}
        
        # 提取日期
        date_patterns = [
            r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?',
            r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text))
        key_info['dates'] = list(set(dates))
        
        # 提取邮箱
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        key_info['emails'] = list(set(emails))
        
        # 提取电话号码
        phone_pattern = r'1[3-9]\d{9}'
        phones = re.findall(phone_pattern, text)
        key_info['phones'] = list(set(phones))
        
        # 提取金额
        money_pattern = r'[￥$¥]\s*\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s*[元美元]'
        amounts = re.findall(money_pattern, text)
        key_info['amounts'] = list(set(amounts))
        
        return key_info
    
    def _classify_document(self, text: str, metadata: Dict) -> str:
        """文档分类"""
        if not text:
            return "unknown"
        
        text_lower = text.lower()
        
        # 关键词分类
        if any(keyword in text_lower for keyword in ['合同', '协议', '甲方', '乙方']):
            return "contract"
        elif any(keyword in text_lower for keyword in ['报告', '分析', '总结']):
            return "report"
        elif any(keyword in text_lower for keyword in ['发票', '收据', '金额']):
            return "financial"
        elif any(keyword in text_lower for keyword in ['说明书', '手册', '操作']):
            return "manual"
        elif metadata.get('extraction_method') == 'ocr_image':
            return "scanned_document"
        else:
            return "general"

# 使用示例
async def example_usage():
    """使用示例"""
    processor = DocumentProcessor()
    
    # 模拟文件内容
    test_content = "这是一个测试文档。\n联系方式: example@test.com\n电话: 13800138000".encode('utf-8')
    
    # 处理文件
    result = await processor.process_uploaded_file(test_content, "test.txt")
    
    print("处理结果:")
    print(f"状态: {result['status']}")
    if result['status'] == 'success':
        print(f"文件名: {result['filename']}")
        print(f"提取方法: {result['metadata']['extraction_method']}")
        print(f"质量分数: {result['processed_result']['quality_score']:.2f}")
        print(f"关键信息: {result['processed_result']['key_information']}")
        print(f"文档类别: {result['processed_result']['document_category']}")

if __name__ == "__main__":
    asyncio.run(example_usage())
