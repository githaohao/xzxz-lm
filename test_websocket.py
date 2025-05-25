import asyncio
import websockets
import json

async def test_websocket():
    try:
        uri = 'ws://localhost:8000/api/voice/ws/voice'
        print(f'尝试连接到统一语音端点: {uri}')
        
        async with websockets.connect(uri) as websocket:
            print('✅ 统一语音WebSocket连接成功!')
            
            # 发送配置
            config = {
                'type': 'config',
                'wake_words': ['小智小智', '小智'],
                'confidence_threshold': 0.6,
                'language': 'zh'
            }
            await websocket.send(json.dumps(config))
            print('📤 发送统一语音配置:', config)
            
            # 接收响应
            response = await websocket.recv()
            print('📥 收到响应:', response)
            
            # 测试心跳
            ping_msg = {'type': 'ping'}
            await websocket.send(json.dumps(ping_msg))
            print('📤 发送心跳:', ping_msg)
            
            # 接收心跳响应
            pong_response = await websocket.recv()
            print('📥 收到心跳响应:', pong_response)
            
    except Exception as e:
        print(f'❌ 连接失败: {e}')

if __name__ == "__main__":
    asyncio.run(test_websocket()) 