"""
文本处理工具类
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TextProcessor:
    """文本处理工具类"""
    
    @staticmethod
    async def process_ocr_content(content: str) -> str:
        """
        处理OCR扫描内容 - 最严格的清理
        
        Args:
            content: 原始OCR内容
            
        Returns:
            清理后的内容
        """
        # 基础清理
        text = await TextProcessor.process_standard_content(content)
        
        # OCR特殊错误清理
        ocr_corrections = {
            r'\b0\b': 'O',  # 数字0误识别为字母O
            r'\bl\b': 'I',  # 小写l误识别为大写I
            r'rn\b': 'm',   # rn误识别为m
            r'\s+': ' ',    # 多空格合并
        }
        
        for pattern, replacement in ocr_corrections.items():
            text = re.sub(pattern, replacement, text)
        
        # 移除可能的OCR噪音
        text = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef,.!?;:"\'()\-]', '', text)
        
        # 移除过短的行（可能是噪音）
        lines = text.split('\n')
        valid_lines = [line.strip() for line in lines if len(line.strip()) > 3]
        
        return '\n'.join(valid_lines)

    @staticmethod
    async def process_text_pdf_content(content: str) -> str:
        """
        处理文本PDF内容 - 中等清理
        
        Args:
            content: 原始PDF内容
            
        Returns:
            清理后的内容
        """
        # 基础清理
        text = await TextProcessor.process_standard_content(content)
        
        # PDF特殊格式清理
        # 移除页眉页脚模式
        text = re.sub(r'^第\s*\d+\s*页.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\s*/\s*\d+.*$', '', text, flags=re.MULTILINE)
        
        # 移除重复的分隔符
        text = re.sub(r'-{3,}', '---', text)
        text = re.sub(r'={3,}', '===', text)
        
        # 合并破碎的行
        text = re.sub(r'(\w)\n(\w)', r'\1 \2', text)
        
        return text

    @staticmethod
    async def process_standard_content(content: str) -> str:
        """
        标准内容处理 - 基础清理
        
        Args:
            content: 原始内容
            
        Returns:
            清理后的内容
        """
        # 基础文本清理
        text = content.strip()
        
        # 标准化空白字符
        text = re.sub(r'\r\n', '\n', text)  # 标准化换行符
        text = re.sub(r'\r', '\n', text)
        text = re.sub(r'\t', ' ', text)     # 制表符转空格
        text = re.sub(r'[ ]{2,}', ' ', text)  # 多空格合并
        
        # 移除控制字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', text)
        
        # 移除空行过多的情况
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

    @staticmethod
    def calculate_content_quality(content: str) -> float:
        """
        计算内容质量分数
        
        Args:
            content: 文本内容
            
        Returns:
            质量分数 (0.0-1.0)
        """
        if not content or len(content.strip()) < 10:
            return 0.0
        
        score = 1.0
        
        # 长度检查
        length = len(content)
        if length < 20:
            score *= 0.5
        elif length < 50:
            score *= 0.8
        
        # 字符组成检查
        total_chars = len(content)
        if total_chars > 0:
            # 中文字符比例
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
            chinese_ratio = chinese_chars / total_chars
            
            # 英文字母比例
            alpha_chars = len(re.findall(r'[a-zA-Z]', content))
            alpha_ratio = alpha_chars / total_chars
            
            # 数字比例
            digit_chars = len(re.findall(r'\d', content))
            digit_ratio = digit_chars / total_chars
            
            # 有意义字符比例
            meaningful_ratio = chinese_ratio + alpha_ratio + digit_ratio
            
            if meaningful_ratio < 0.6:
                score *= 0.6
            elif meaningful_ratio < 0.8:
                score *= 0.8
        
        # 特殊字符过多检查
        special_chars = len(re.findall(r'[^\w\s\u4e00-\u9fff]', content))
        if special_chars / total_chars > 0.3:
            score *= 0.7
        
        # 重复内容检查
        lines = content.split('\n')
        unique_lines = set(line.strip() for line in lines if line.strip())
        if len(lines) > 0 and len(unique_lines) / len(lines) < 0.7:
            score *= 0.8
        
        return max(0.0, min(1.0, score))

    @staticmethod
    def get_processing_type(is_ocr: bool, is_pdf: bool, is_text_pdf: bool) -> str:
        """
        获取处理类型标识
        
        Args:
            is_ocr: 是否为OCR文档
            is_pdf: 是否为PDF文档
            is_text_pdf: 是否为文本PDF
            
        Returns:
            处理类型标识
        """
        if is_ocr or (is_pdf and not is_text_pdf):
            return 'ocr_enhanced'
        elif is_pdf and is_text_pdf:
            return 'pdf_optimized'
        else:
            return 'standard'

    @staticmethod
    async def extract_key_paragraphs(content: str, filename: str) -> str:
        """
        提取关键段落（用于中等文档）
        
        Args:
            content: 文档内容
            filename: 文件名
            
        Returns:
            提取的关键内容
        """
        try:
            lines = content.split('\n')
            
            # 获取文档开头（前20%或最多500行）
            start_lines = int(min(len(lines) * 0.2, 500))
            beginning = '\n'.join(lines[:start_lines])
            
            # 获取文档结尾（后10%或最多200行）
            end_lines = int(min(len(lines) * 0.1, 200))
            ending = '\n'.join(lines[-end_lines:]) if end_lines > 0 else ""
            
            # 查找包含关键词的段落
            keywords = ['摘要', '总结', '概述', '简介', '目录', 'abstract', 'summary', 'introduction']
            key_paragraphs = []
            
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in keywords):
                    # 包含关键词的段落及其周围内容
                    start_idx = max(0, i - 2)
                    end_idx = min(len(lines), i + 5)
                    key_paragraphs.append('\n'.join(lines[start_idx:end_idx]))
            
            # 组合内容
            extracted_content = f"文档开头：\n{beginning}\n\n"
            
            if key_paragraphs:
                extracted_content += f"关键段落：\n" + '\n\n'.join(key_paragraphs) + "\n\n"
            
            if ending:
                extracted_content += f"文档结尾：\n{ending}"
            
            # 如果提取的内容太长，截断
            if len(extracted_content) > 8000:
                extracted_content = extracted_content[:8000] + "...\n[内容已截断]"
            
            return extracted_content
            
        except Exception as e:
            logger.warning(f"提取关键段落失败: {e}")
            return content[:5000] + "...\n[提取失败，使用开头内容]"

    @staticmethod
    async def create_document_summary(content: str, filename: str) -> str:
        """
        创建文档摘要（用于大文档）
        
        Args:
            content: 文档内容
            filename: 文件名
            
        Returns:
            文档摘要
        """
        try:
            # 将文档分成多个段落
            paragraphs = content.split('\n\n')
            
            # 每段最多1000字符
            segments = []
            current_segment = ""
            
            for paragraph in paragraphs:
                if len(current_segment) + len(paragraph) < 1000:
                    current_segment += paragraph + '\n\n'
                else:
                    if current_segment:
                        segments.append(current_segment.strip())
                    current_segment = paragraph + '\n\n'
            
            if current_segment:
                segments.append(current_segment.strip())
            
            # 选择关键段落进行摘要
            key_segments = []
            
            # 总是包含开头和结尾
            if segments:
                key_segments.append(segments[0])  # 开头
                if len(segments) > 1:
                    key_segments.append(segments[-1])  # 结尾
            
            # 添加中间的关键段落
            for segment in segments[1:-1]:
                segment_lower = segment.lower()
                # 查找包含重要信息的段落
                if any(keyword in segment_lower for keyword in [
                    '摘要', '总结', '结论', '概述', '目的', '目标', '方法', '结果',
                    'abstract', 'summary', 'conclusion', 'objective', 'purpose', 'method', 'result'
                ]):
                    key_segments.append(segment)
                    if len(key_segments) >= 5:  # 限制段落数量
                        break
            
            # 如果关键段落不够，随机选择一些段落
            if len(key_segments) < 3 and len(segments) > 2:
                import random
                remaining_segments = [s for s in segments[1:-1] if s not in key_segments]
                additional_count = min(3 - len(key_segments), len(remaining_segments))
                key_segments.extend(random.sample(remaining_segments, additional_count))
            
            # 组合摘要
            summary = f"文档摘要 ({len(segments)}个段落中的{len(key_segments)}个关键段落)：\n\n"
            summary += '\n\n---段落分隔---\n\n'.join(key_segments)
            
            # 限制总长度
            if len(summary) > 6000:
                summary = summary[:6000] + "...\n[摘要已截断]"
            
            return summary
            
        except Exception as e:
            logger.warning(f"创建文档摘要失败: {e}")
            return content[:3000] + "...\n[摘要失败，使用开头内容]"

    @staticmethod
    async def intelligent_sampling(content: str, filename: str) -> str:
        """
        智能采样（用于特大文档）
        
        Args:
            content: 文档内容
            filename: 文件名
            
        Returns:
            采样后的内容
        """
        try:
            total_length = len(content)
            
            # 提取开头、中间、结尾的样本
            start_sample = content[:2000]  # 开头2000字符
            end_sample = content[-1000:]   # 结尾1000字符
            
            # 中间采样：每隔一定间距采样
            middle_samples = []
            sample_interval = max(1000, total_length // 20)  # 最多采样20个片段
            
            for i in range(2000, total_length - 1000, sample_interval):
                sample = content[i:i+500]  # 每次采样500字符
                middle_samples.append(sample)
                if len(middle_samples) >= 10:  # 最多10个中间样本
                    break
            
            # 查找结构化信息（标题、目录等）
            lines = content.split('\n')
            structured_info = []
            
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and (
                    line_stripped.startswith('#') or  # Markdown标题
                    line_stripped.endswith(':') or   # 冒号结尾（可能是标题）
                    len(line_stripped) < 100 and (   # 短行且包含关键词
                        any(keyword in line_stripped.lower() for keyword in [
                            '第', '章', '节', '部分', 'chapter', 'section', 'part'
                        ])
                    )
                ):
                    structured_info.append(line_stripped)
                    if len(structured_info) >= 20:  # 最多20个结构化信息
                        break
            
            # 组合采样结果
            sampled_content = f"超大文档智能采样 (总长度: {total_length} 字符)：\n\n"
            sampled_content += f"文档开头：\n{start_sample}\n\n"
            
            if structured_info:
                sampled_content += f"文档结构：\n" + '\n'.join(structured_info) + "\n\n"
            
            if middle_samples:
                sampled_content += f"中间采样：\n" + '\n\n---采样分隔---\n\n'.join(middle_samples) + "\n\n"
            
            sampled_content += f"文档结尾：\n{end_sample}"
            
            # 限制总长度
            if len(sampled_content) > 8000:
                sampled_content = sampled_content[:8000] + "...\n[采样已截断]"
            
            return sampled_content
            
        except Exception as e:
            logger.warning(f"智能采样失败: {e}")
            return content[:3000] + "...\n[采样失败，使用开头内容]"

    @staticmethod
    def extract_document_type(filename: str, content: str) -> str:
        """
        从文件名和内容中提取文档类型
        
        Args:
            filename: 文件名
            content: 文档内容
            
        Returns:
            文档类型
        """
        filename_lower = filename.lower()
        
        # 从文件名推断类型
        if 'report' in filename_lower or '报告' in filename_lower:
            return '报告'
        elif 'plan' in filename_lower or '计划' in filename_lower:
            return '计划'
        elif 'spec' in filename_lower or '规范' in filename_lower:
            return '规范'
        elif 'note' in filename_lower or '笔记' in filename_lower:
            return '笔记'
        elif 'summary' in filename_lower or '总结' in filename_lower:
            return '总结'
        else:
            return '通用'
    
    @staticmethod
    def clean_extracted_text(text: str) -> str:
        """
        清理提取的文本
        
        Args:
            text: 原始提取的文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 基本清理
        text = text.strip()
        
        # 移除过多的空行
        import re
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # 移除行首行尾多余空格
        lines = []
        for line in text.split('\n'):
            lines.append(line.strip())
        
        return '\n'.join(lines)


# 便利函数
def clean_extracted_text(text: str) -> str:
    """清理提取的文本"""
    return TextProcessor.clean_extracted_text(text) 