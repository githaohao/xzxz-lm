"""
流式语音聊天服务

提供流式语音识别、AI对话和TTS合成功能
"""

import json
import base64
import logging
from typing import AsyncGenerator
from app.services.funaudio_service_real import FunAudioLLMService
from app.services.lm_studio_service import lm_studio_service
from app.models.schemas import ChatRequest
from app.utils import clean_text_for_speech, synthesize_speech_chunk

logger = logging.getLogger(__name__)

class VoiceStreamService:
    """流式语音聊天服务"""
    
    def __init__(self):
        self.funaudio_service = FunAudioLLMService()
    
    async def generate_streaming_response(
        self, 
        audio_data: bytes, 
        session_id: str, 
        language: str = "auto",
        knowledge_base_id: str = None
    ) -> AsyncGenerator[str, None]:
        """生成流式语音聊天响应"""
        try:
            # 第一步：语音识别
            yield f"data: {json.dumps({'type': 'status', 'message': '正在识别语音...'})}\n\n"
            
            # 使用FunAudioLLM进行语音识别
            recognition_result = await self.funaudio_service.voice_recognition(audio_data, language)
            
            if not recognition_result["success"]:
                yield f"data: {json.dumps({'type': 'error', 'message': '语音识别失败'})}\n\n"
                return
            
            recognized_text = recognition_result["recognized_text"]
            
            if not recognized_text.strip():
                yield f"data: {json.dumps({'type': 'error', 'message': '未识别到有效语音内容'})}\n\n"
                return
            
            # 发送识别结果
            yield f"data: {json.dumps({'type': 'recognition', 'text': recognized_text})}\n\n"
            
            # 第二步：准备AI聊天请求
            yield f"data: {json.dumps({'type': 'status', 'message': 'AI正在思考...'})}\n\n"
            
            chat_request = ChatRequest(
                message=recognized_text,
                history=[],  # 可以根据需要添加历史记录
                temperature=0.7,
                max_tokens=2048,
                stream=True
            )
            
            # 第三步：流式AI对话 + 实时TTS
            await self._process_streaming_ai_response(chat_request)
            
        except Exception as e:
            logger.error(f"流式语音聊天处理失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    async def _process_streaming_ai_response(self, chat_request: ChatRequest) -> AsyncGenerator[str, None]:
        """处理流式AI响应和TTS合成"""
        text_buffer = ""
        processed_text_length = 0  # 记录已处理的文本长度
        chunk_counter = 0
        
        async for ai_chunk in lm_studio_service.chat_completion_stream(chat_request):
            if ai_chunk.strip():
                text_buffer += ai_chunk
                
                # 发送AI生成的文字片段
                yield f"data: {json.dumps({'type': 'ai_text', 'content': ai_chunk})}\n\n"
                
                # 清理思考标签
                cleaned_buffer = clean_text_for_speech(text_buffer)
                
                # 只处理新增的部分，避免重复处理
                if len(cleaned_buffer) > processed_text_length:
                    # 获取新增的文本部分
                    new_text = cleaned_buffer[processed_text_length:]
                    
                    # 检查新文本是否可以形成完整的句子进行TTS
                    # 寻找句子结束标记
                    sentence_endings = ['。', '！', '？', '.', '!', '?', '\n']
                    last_sentence_end = -1
                    
                    for i, char in enumerate(new_text):
                        if char in sentence_endings:
                            last_sentence_end = i
                    
                    # 如果找到完整句子，进行TTS合成
                    if last_sentence_end >= 0:
                        # 提取完整的句子（包括之前未处理的部分）
                        sentence_to_process = new_text[:last_sentence_end + 1].strip()
                        
                        if sentence_to_process and len(sentence_to_process) >= 3:
                            try:
                                logger.info(f"🎵 处理完整句子: {repr(sentence_to_process[:100])}")
                                
                                # TTS合成
                                audio_buffer = await synthesize_speech_chunk(sentence_to_process)
                                if audio_buffer:
                                    # 将音频数据编码为base64
                                    audio_base64 = base64.b64encode(audio_buffer).decode('utf-8')
                                    
                                    # 发送音频数据
                                    yield f"data: {json.dumps({'type': 'audio_chunk', 'audio': audio_base64, 'text': sentence_to_process, 'chunk_id': chunk_counter})}\n\n"
                                    chunk_counter += 1
                                    
                                    logger.info(f"✅ 音频块 {chunk_counter-1} 发送成功: {len(audio_buffer)} 字节")
                                else:
                                    logger.info(f"⚠️ 句子TTS跳过: {repr(sentence_to_process[:50])}")
                                    
                            except Exception as e:
                                logger.error(f"❌ 句子TTS合成异常: {e}, 文本: {repr(sentence_to_process[:100])}")
                                yield f"data: {json.dumps({'type': 'tts_error', 'message': f'语音合成失败: {str(e)}', 'text': sentence_to_process[:100]})}\n\n"
                        
                        # 更新已处理的文本长度
                        processed_text_length += last_sentence_end + 1
                    
                    # 如果缓冲区太长但没有句子结束符，强制处理一部分
                    elif len(new_text) > 100:
                        # 寻找合适的分割点（空格、逗号等）
                        split_chars = [' ', '，', ',', '、', '；', ';']
                        best_split = -1
                        
                        # 在前80个字符中寻找分割点
                        for i in range(min(80, len(new_text) - 1), 20, -1):
                            if new_text[i] in split_chars:
                                best_split = i
                                break
                        
                        if best_split > 20:
                            chunk_to_process = new_text[:best_split + 1].strip()
                            
                            if chunk_to_process:
                                try:
                                    logger.info(f"🎵 处理长文本块: {repr(chunk_to_process[:100])}")
                                    
                                    # TTS合成
                                    audio_buffer = await synthesize_speech_chunk(chunk_to_process)
                                    if audio_buffer:
                                        audio_base64 = base64.b64encode(audio_buffer).decode('utf-8')
                                        yield f"data: {json.dumps({'type': 'audio_chunk', 'audio': audio_base64, 'text': chunk_to_process, 'chunk_id': chunk_counter})}\n\n"
                                        chunk_counter += 1
                                        logger.info(f"✅ 长文本音频块 {chunk_counter-1} 发送成功: {len(audio_buffer)} 字节")
                                    
                                except Exception as e:
                                    logger.error(f"❌ 长文本TTS合成异常: {e}")
                            
                            # 更新已处理的文本长度
                            processed_text_length += best_split + 1
        
        # 处理剩余的文本缓冲区
        if text_buffer.strip():
            try:
                # 清理剩余文本
                cleaned_buffer = clean_text_for_speech(text_buffer)
                
                # 获取未处理的剩余文本
                if len(cleaned_buffer) > processed_text_length:
                    remaining_text = cleaned_buffer[processed_text_length:].strip()
                    
                    if remaining_text and len(remaining_text) >= 3:
                        logger.info(f"🔚 处理剩余文本: {repr(remaining_text[:100])}")
                        audio_buffer = await synthesize_speech_chunk(remaining_text)
                        if audio_buffer:
                            audio_base64 = base64.b64encode(audio_buffer).decode('utf-8')
                            yield f"data: {json.dumps({'type': 'audio_chunk', 'audio': audio_base64, 'text': remaining_text, 'chunk_id': chunk_counter})}\n\n"
                            logger.info(f"✅ 最终音频块发送成功: {len(audio_buffer)} 字节")
                        else:
                            logger.info(f"⚠️ 最终文本块TTS跳过: {repr(remaining_text[:50])}")
                    else:
                        logger.info("剩余文本太短或为空，跳过TTS合成")
                else:
                    logger.info("所有文本已处理完毕，无剩余文本")
            except Exception as e:
                logger.error(f"❌ 最终TTS合成失败: {e}, 原始文本: {repr(text_buffer[:200])}")
                yield f"data: {json.dumps({'type': 'tts_error', 'message': f'最终语音合成失败: {str(e)}', 'text': text_buffer[:100]})}\n\n"
        
        # 发送完成信号
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"
        yield "data: [DONE]\n\n"
    
    async def process_speech_synthesis(self, text: str, voice: str = "zh-CN-XiaoxiaoNeural", rate: float = 1.0) -> bytes:
        """处理语音合成请求"""
        try:
            # 清理文本，移除思考标签和表情符号
            clean_text = clean_text_for_speech(text)
            
            if not clean_text.strip():
                logger.warning("清理后的文本为空，跳过语音合成")
                return b""
            
            # 调用TTS合成
            audio_buffer = await synthesize_speech_chunk(clean_text)
            return audio_buffer or b""
            
        except Exception as e:
            logger.error(f"❌ 语音合成失败: {e}")
            raise e

# 创建全局服务实例
voice_stream_service = VoiceStreamService() 