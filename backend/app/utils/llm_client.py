"""
LLM客户端工具类
"""

import httpx
import logging
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """LLM客户端工具类"""
    
    @staticmethod
    async def make_llm_request(system_prompt: str, user_prompt: str) -> str:
        """
        向LM Studio发送请求
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            
        Returns:
            LLM响应内容
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": settings.lm_studio_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,  # 较低的温度以获得更一致的分析结果
                    "max_tokens": 1000,
                    "stream": False
                }
                
                response = await client.post(
                    f"{settings.lm_studio_base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {settings.lm_studio_api_key}"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"LLM请求失败: {response.status_code} - {response.text}")
                    raise Exception(f"LLM请求失败: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"LLM请求异常: {e}")
            raise

    @staticmethod 
    async def call_llm_for_analysis(
        content: str,
        filename: str,
        analysis_prompt: str,
        custom_analysis: bool,
        processing_strategy: str
    ) -> Dict:
        """
        调用LLM进行文档内容分析
        
        Args:
            content: 文档内容
            filename: 文件名
            analysis_prompt: 分析提示词
            custom_analysis: 是否使用自定义分析
            processing_strategy: 处理策略
            
        Returns:
            分析结果字典
        """
        try:
            from .document_analysis import DocumentAnalyzer
            
            # 构建系统提示词
            system_prompt = DocumentAnalyzer.build_analysis_system_prompt()
            
            # 构建用户提示词
            user_prompt = DocumentAnalyzer.build_analysis_user_prompt(
                filename, content, analysis_prompt, processing_strategy
            )
            
            # 调用LLM
            response = await LLMClient.make_llm_request(system_prompt, user_prompt)
            
            # 解析LLM响应
            analysis_result = DocumentAnalyzer.parse_llm_response(response)
            
            # 验证和修正结果
            return DocumentAnalyzer.validate_analysis_result(analysis_result, filename)
            
        except Exception as e:
            logger.error(f"LLM分析调用失败: {e}")
            # 返回默认结果，避免完全失败
            return {
                "knowledge_base_name": "通用文档",
                "is_new_knowledge_base": False,
                "document_type": "未知",
                "reason": f"LLM分析失败: {str(e)}",
                "confidence": 0.1
            } 