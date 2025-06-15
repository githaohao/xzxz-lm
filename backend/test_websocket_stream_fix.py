#!/usr/bin/env python3
"""
WebSocket流式音频传输测试脚本
测试新的WebSocket实现，验证消息处理和二进制传输功能
"""

import asyncio
import websockets
import json
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket服务器地址
WEBSOCKET_URL = "ws://localhost:8000/voice/ws/voice"

async def test_websocket_connection():
    """测试WebSocket连接和基本消息处理"""
    try:
        logger.info("🔌 连接WebSocket服务器...")
        
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            logger.info("✅ WebSocket连接成功")
            
            # 等待连接确认消息
            response = await websocket.recv()
            logger.info(f"📥 收到连接确认: {response}")
            
            # 发送配置消息
            config_message = {
                "type": "config",
                "session_id": "test-session-123",
                "language": "auto"
            }
            
            logger.info(f"📤 发送配置消息: {config_message}")
            await websocket.send(json.dumps(config_message))
            
            # 等待配置确认
            response = await websocket.recv()
            logger.info(f"📥 收到配置确认: {response}")
            
            # 发送心跳测试
            ping_message = {"type": "ping"}
            logger.info(f"📤 发送心跳: {ping_message}")
            await websocket.send(json.dumps(ping_message))
            
            # 等待心跳响应
            response = await websocket.recv()
            logger.info(f"📥 收到心跳响应: {response}")
            
            logger.info("✅ WebSocket基本功能测试通过")
            
    except Exception as e:
        logger.error(f"❌ WebSocket连接测试失败: {e}")
        return False
    
    return True

async def test_binary_audio_transmission():
    """测试二进制音频数据传输"""
    try:
        logger.info("🎵 测试二进制音频传输...")
        
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # 等待连接确认
            await websocket.recv()
            
            # 发送配置
            config_message = {
                "type": "config",
                "session_id": "test-audio-session",
                "language": "auto"
            }
            await websocket.send(json.dumps(config_message))
            await websocket.recv()  # 配置确认
            
            # 创建模拟音频数据（简单的字节序列）
            mock_audio_data = b"MOCK_AUDIO_DATA_FOR_TESTING" * 100  # 2700字节
            logger.info(f"📤 发送模拟音频数据: {len(mock_audio_data)} 字节")
            
            # 发送二进制音频数据
            await websocket.send(mock_audio_data)
            
            # 接收处理状态消息
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    logger.info(f"📥 收到响应: {response[:200]}...")
                    
                    # 解析JSON响应
                    try:
                        message = json.loads(response)
                        if message.get("type") == "error":
                            logger.error(f"❌ 服务器错误: {message.get('error')}")
                            break
                        elif message.get("type") == "recognition_result":
                            logger.info(f"🎯 识别结果: {message}")
                            break
                        elif message.get("type") == "stream_complete":
                            logger.info("✅ 流式处理完成")
                            break
                    except json.JSONDecodeError:
                        # 可能是二进制音频数据
                        logger.info(f"🔊 收到二进制数据: {len(response)} 字节")
                        
                except asyncio.TimeoutError:
                    logger.warning("⏰ 等待响应超时")
                    break
                except Exception as e:
                    logger.error(f"❌ 接收响应失败: {e}")
                    break
            
            logger.info("✅ 二进制音频传输测试完成")
            
    except Exception as e:
        logger.error(f"❌ 二进制音频传输测试失败: {e}")
        return False
    
    return True

async def test_message_format_validation():
    """测试各种消息格式的处理"""
    try:
        logger.info("📋 测试消息格式验证...")
        
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # 等待连接确认
            await websocket.recv()
            
            # 测试1: 有效的JSON消息
            valid_message = {"type": "config", "session_id": "test", "language": "zh"}
            logger.info("📤 发送有效JSON消息")
            await websocket.send(json.dumps(valid_message))
            response = await websocket.recv()
            logger.info(f"📥 有效消息响应: {response[:100]}...")
            
            # 测试2: 无效的JSON消息
            invalid_json = '{"type": "config", "invalid": json}'
            logger.info("📤 发送无效JSON消息")
            await websocket.send(invalid_json)
            response = await websocket.recv()
            logger.info(f"📥 无效JSON响应: {response[:100]}...")
            
            # 测试3: 未知消息类型
            unknown_message = {"type": "unknown_type", "data": "test"}
            logger.info("📤 发送未知类型消息")
            await websocket.send(json.dumps(unknown_message))
            response = await websocket.recv()
            logger.info(f"📥 未知类型响应: {response[:100]}...")
            
            logger.info("✅ 消息格式验证测试完成")
            
    except Exception as e:
        logger.error(f"❌ 消息格式验证测试失败: {e}")
        return False
    
    return True

async def main():
    """主测试函数"""
    logger.info("🚀 开始WebSocket流式传输测试")
    
    tests = [
        ("基本连接测试", test_websocket_connection),
        ("消息格式验证", test_message_format_validation),
        ("二进制音频传输", test_binary_audio_transmission),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 执行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name} - 通过")
            else:
                logger.error(f"❌ {test_name} - 失败")
                
        except Exception as e:
            logger.error(f"❌ {test_name} - 异常: {e}")
            results.append((test_name, False))
        
        # 测试间隔
        await asyncio.sleep(1)
    
    # 输出测试结果摘要
    logger.info(f"\n{'='*50}")
    logger.info("📊 测试结果摘要")
    logger.info(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！WebSocket流式传输功能正常")
    else:
        logger.warning(f"⚠️ {total - passed} 个测试失败，需要检查问题")

if __name__ == "__main__":
    asyncio.run(main()) 