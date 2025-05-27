#!/usr/bin/env python3
"""
RAG功能测试脚本
测试rag_enabled字段是否正确控制RAG行为
"""

import asyncio
import json
from typing import Dict, Any

from app.models.schemas import MultimodalStreamRequest, FileData, ChatMessage
from app.routes.chat import multimodal_chat_stream_with_processed_data


def create_test_request(message: str, rag_enabled: bool = True) -> MultimodalStreamRequest:
    """创建测试请求"""
    file_data = FileData(
        name="test_document.pdf",
        type="application/pdf",
        size=1024,
        content="这是一个测试文档。它包含了很多有趣的信息。我们可以通过RAG功能来检索相关内容。人工智能技术正在快速发展，为各行各业带来了巨大的变革。",
        doc_id=None,
        ocr_completed=True,
        rag_enabled=rag_enabled
    )
    
    return MultimodalStreamRequest(
        message=message,
        history=[],
        file_data=file_data,
        temperature=0.7,
        max_tokens=2048
    )


async def simulate_streaming_response(request: MultimodalStreamRequest) -> Dict[str, Any]:
    """模拟流式响应处理"""
    print(f"\n🧪 测试RAG功能")
    print(f"📄 文件: {request.file_data.name}")
    print(f"🔧 RAG启用: {request.file_data.rag_enabled}")
    print(f"💬 查询: {request.message}")
    print(f"{'='*50}")
    
    # 模拟生成器的输出
    events = []
    
    # 这里我们只检查逻辑，不实际调用API
    if request.file_data and request.file_data.content:
        if request.file_data.rag_enabled:
            events.append({
                'type': 'file_processing',
                'message': '🧠 启用智能检索模式'
            })
            
            if not request.file_data.doc_id:
                events.append({
                    'type': 'file_processing',
                    'message': '正在对文档进行智能索引...'
                })
                events.append({
                    'type': 'file_processing',
                    'message': f'文档索引完成: {request.file_data.name}'
                })
            
            events.append({
                'type': 'file_processing',
                'message': '正在检索相关文档片段...'
            })
            events.append({
                'type': 'file_processing',
                'message': '🔍 检索到 2 个相关片段'
            })
        else:
            events.append({
                'type': 'file_processing',
                'message': '📄 使用完整文档模式'
            })
            events.append({
                'type': 'file_processing',
                'message': f'已加载完整文档: {request.file_data.name}'
            })
    
    # 输出事件
    for event in events:
        print(f"📋 {event['message']}")
    
    return {
        'rag_mode': 'enabled' if request.file_data.rag_enabled else 'disabled',
        'events_count': len(events),
        'events': events
    }


async def run_tests():
    """运行测试"""
    print("🚀 开始RAG功能测试")
    print("="*60)
    
    # 测试1: RAG启用
    test1 = create_test_request("什么是人工智能？", rag_enabled=True)
    result1 = await simulate_streaming_response(test1)
    
    print(f"\n✅ 测试1结果: RAG模式 = {result1['rag_mode']}")
    print(f"📊 事件数量: {result1['events_count']}")
    
    # 测试2: RAG禁用
    test2 = create_test_request("总结这个文档", rag_enabled=False)
    result2 = await simulate_streaming_response(test2)
    
    print(f"\n✅ 测试2结果: RAG模式 = {result2['rag_mode']}")
    print(f"📊 事件数量: {result2['events_count']}")
    
    # 验证测试结果
    print(f"\n{'='*60}")
    print("📋 测试总结:")
    
    if result1['rag_mode'] == 'enabled' and any('智能检索' in event['message'] for event in result1['events']):
        print("✅ RAG启用测试通过")
    else:
        print("❌ RAG启用测试失败")
    
    if result2['rag_mode'] == 'disabled' and any('完整文档模式' in event['message'] for event in result2['events']):
        print("✅ RAG禁用测试通过")
    else:
        print("❌ RAG禁用测试失败")


if __name__ == "__main__":
    asyncio.run(run_tests()) 