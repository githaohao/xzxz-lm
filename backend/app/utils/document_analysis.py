"""
文档分析工具类
"""

import json
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """文档分析工具类"""
    
    @staticmethod
    def parse_llm_response(response: str) -> Dict:
        """
        解析LLM响应，提取JSON结果
        
        Args:
            response: LLM原始响应
            
        Returns:
            解析后的结果字典
        """
        try:
            # 尝试直接解析JSON
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
            
            # 如果直接解析失败，尝试提取JSON部分
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # 如果仍然失败，从文本中提取信息
            knowledge_base_match = re.search(r'knowledge_base_name["\s]*:["\s]*([^"]*)', response)
            is_new_match = re.search(r'is_new_knowledge_base["\s]*:["\s]*(true|false)', response)
            doc_type_match = re.search(r'document_type["\s]*:["\s]*([^"]*)', response)
            reason_match = re.search(r'reason["\s]*:["\s]*([^"]*)', response)
            
            return {
                "knowledge_base_name": knowledge_base_match.group(1) if knowledge_base_match else "通用文档",
                "is_new_knowledge_base": is_new_match.group(1).lower() == 'true' if is_new_match else False,
                "document_type": doc_type_match.group(1) if doc_type_match else "未知",
                "reason": reason_match.group(1) if reason_match else "AI分析结果",
                "confidence": 0.5
            }
            
        except Exception as e:
            logger.warning(f"解析LLM响应失败: {e}")
            return {
                "knowledge_base_name": "通用文档",
                "is_new_knowledge_base": False,
                "document_type": "未知",
                "reason": "解析失败，使用默认分类",
                "confidence": 0.3
            }

    @staticmethod
    def validate_analysis_result(result: Dict, filename: str) -> Dict:
        """
        验证和修正分析结果
        
        Args:
            result: 原始分析结果
            filename: 文件名
            
        Returns:
            验证后的结果
        """
        try:
            # 确保必要字段存在
            if "knowledge_base_name" not in result:
                result["knowledge_base_name"] = "通用文档"
            
            if "is_new_knowledge_base" not in result:
                result["is_new_knowledge_base"] = False
            
            if "document_type" not in result:
                result["document_type"] = "未知"
            
            if "reason" not in result:
                result["reason"] = "AI智能分析结果"
            
            # 检查知识库名称是否在预设列表中
            preset_knowledge_bases = {
                "个人简历", "合同文档", "教育培训", "技术文档", 
                "商务文档", "操作手册", "医疗健康", "政策法规"
            }
            
            kb_name = result["knowledge_base_name"]
            if kb_name not in preset_knowledge_bases:
                # 如果不在预设列表中，标记为新知识库
                result["is_new_knowledge_base"] = True
                
                # 但如果名称很相似，修正为预设名称
                for preset in preset_knowledge_bases:
                    if any(word in kb_name for word in preset.split()) or any(word in preset for word in kb_name.split()):
                        result["knowledge_base_name"] = preset
                        result["is_new_knowledge_base"] = False
                        result["reason"] += f"（已修正为预设知识库：{preset}）"
                        break
            
            return result
            
        except Exception as e:
            logger.warning(f"验证分析结果失败: {e}")
            return {
                "knowledge_base_name": "通用文档",
                "is_new_knowledge_base": False,
                "document_type": "未知",
                "reason": "验证失败，使用默认分类",
                "confidence": 0.2
            }

    @staticmethod
    def get_document_processing_strategy(content_length: int) -> str:
        """
        根据文档大小选择处理策略
        
        Args:
            content_length: 文档内容长度
            
        Returns:
            处理策略标识
        """
        if content_length < 5000:
            return "direct_analysis"
        elif content_length < 20000:
            return "key_paragraphs"
        elif content_length < 100000:
            return "segment_summary"
        else:
            return "intelligent_sampling"

    @staticmethod
    def build_analysis_system_prompt() -> str:
        """
        构建LLM分析的系统提示词
        
        Returns:
            系统提示词
        """
        return """你是一个专业的文档分析专家，负责分析文档内容并决定最合适的知识库归档位置。

        你的任务是：
            1. 分析文档的主要内容和类型
            2. 从以下预设知识库中选择最合适的归档位置：
            - 个人简历：简历、CV、个人资料、求职相关
            - 合同文档：合同、协议、法律文件
            - 教育培训：培训材料、课程、教育内容
            - 技术文档：API文档、技术规范、开发资料
            - 商务文档：商业计划、市场分析、商务资料
            - 操作手册：用户手册、操作指南、说明书
            - 医疗健康：医疗报告、健康资料、医学文献
            - 政策法规：政策文件、法规条例、规章制度

            3. 如果文档不适合任何预设知识库，建议创建新的知识库

            请返回JSON格式的分析结果：
            {
                "knowledge_base_name": "知识库名称",
                "is_new_knowledge_base": false,
                "document_type": "文档类型",
                "reason": "选择理由",
                "confidence": 0.85
            }"""

    @staticmethod
    def build_analysis_user_prompt(filename: str, content: str, analysis_prompt: str, processing_strategy: str) -> str:
        """
        构建LLM分析的用户提示词
        
        Args:
            filename: 文件名
            content: 文档内容
            analysis_prompt: 用户提供的分析提示
            processing_strategy: 处理策略
            
        Returns:
            用户提示词
        """
        return f"""请分析以下文档并决定最合适的知识库归档位置：

            文件名：{filename}
            用户提示：{analysis_prompt}
            处理策略：{processing_strategy}

            文档内容：
            {content}

            请仔细分析文档的主要内容、类型和用途，然后选择最合适的知识库进行归档。
            如果用户提供了特定的分类建议，请优先考虑。""" 