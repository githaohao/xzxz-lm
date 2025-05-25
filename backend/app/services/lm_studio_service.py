import httpx
import asyncio
import json
from typing import List, Dict, Any, AsyncGenerator
from app.config import settings
from app.models.schemas import ChatMessage, ChatRequest
import logging

logger = logging.getLogger(__name__)

class LMStudioService:
    def __init__(self):
        self.base_url = settings.lm_studio_base_url
        self.model = settings.lm_studio_model
        self.api_key = settings.lm_studio_api_key
        
    async def health_check(self) -> bool:
        """检查LM Studio服务状态"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"LM Studio健康检查失败: {e}")
            return False
    
    def _prepare_messages(self, request: ChatRequest) -> List[Dict[str, str]]:
        """准备消息格式供LM Studio使用"""
        messages = []
        
        # 添加系统提示
        messages.append({
            "role": "system",
            "content": "你是一个智能助手，擅长处理文本、图像和语音等多模态内容。请用中文回答用户问题，保持友善和专业。"
        })
        
        # 添加历史消息
        for msg in request.history:
            role = "user" if msg.is_user else "assistant"
            content = msg.content
            
            # 如果是文件消息，添加文件信息
            if msg.file_name:
                content = f"[文件: {msg.file_name}]\n{content}"
                
            messages.append({
                "role": role,
                "content": content
            })
        
        # 添加当前消息
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        return messages
    
    async def chat_completion(self, request: ChatRequest) -> str:
        """发送聊天请求到LM Studio"""
        try:
            logger.info(f"🚀 开始处理聊天请求: {request.message[:50]}...")
            logger.info(f"📊 历史消息数量: {len(request.history)}")
            
            messages = self._prepare_messages(request)
            logger.info(f"📝 准备的消息数量: {len(messages)}")
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": False
            }
            
            logger.info(f"📤 发送到LM Studio的payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            async with httpx.AsyncClient() as client:
                logger.info(f"🔗 连接到LM Studio: {self.base_url}/chat/completions")
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    timeout=120.0
                )
                
                logger.info(f"📡 LM Studio响应状态: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result["choices"][0]["message"]["content"]
                    logger.info(f"✅ LM Studio响应成功: {ai_response[:100]}...")
                    return ai_response
                else:
                    error_text = response.text
                    logger.error(f"❌ LM Studio API错误: {response.status_code} - {error_text}")
                    return "抱歉，服务暂时不可用，请稍后再试。"
                    
        except Exception as e:
            logger.error(f"❌ 聊天完成请求失败: {e}")
            logger.error(f"❌ 错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"❌ 错误堆栈: {traceback.format_exc()}")
            return "抱歉，处理您的请求时出现错误，请稍后再试。"
    
    async def chat_completion_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        try:
            messages = self._prepare_messages(request)
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": True
            }
            
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    timeout=120.0
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]  # 移除 "data: " 前缀
                                if data == "[DONE]":
                                    break
                                try:
                                    json_data = json.loads(data)
                                    delta = json_data["choices"][0]["delta"]
                                    if "content" in delta:
                                        yield delta["content"]
                                except json.JSONDecodeError:
                                    continue
                    else:
                        yield "抱歉，服务暂时不可用，请稍后再试。"
                        
        except Exception as e:
            logger.error(f"流式聊天完成请求失败: {e}")
            yield "抱歉，处理您的请求时出现错误，请稍后再试。"

# 创建全局服务实例
lm_studio_service = LMStudioService() 