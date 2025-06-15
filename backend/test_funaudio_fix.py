#!/usr/bin/env python3
"""
FunAudioLLM 服务修复验证脚本
测试所有工具类和方法是否正确导入和工作
"""

import sys
import os
import asyncio
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

async def test_imports():
    """测试所有导入"""
    try:
        logger.info("🔍 测试工具类导入...")
        
        # 测试基础工具类导入
        from app.utils import (
            DeviceManager, AudioProcessor, EmotionAnalyzer, 
            MessageProcessor, get_timestamp,
            get_cache_dir, get_model_device_config,
            extract_sensevoice_emotion_info,
            extract_sensevoice_event_info,
            clean_sensevoice_text
        )
        logger.info("✅ 所有工具类导入成功")
        
        # 测试FunAudioLLM服务导入
        from app.services.funaudio_service_real import FunAudioLLMService
        logger.info("✅ FunAudioLLMService 导入成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 导入测试失败: {e}")
        return False

async def test_device_manager():
    """测试DeviceManager功能"""
    try:
        logger.info("🔍 测试DeviceManager功能...")
        
        from app.utils import DeviceManager, get_cache_dir, get_model_device_config
        
        # 测试设备检测
        device = DeviceManager.get_optimal_device()
        logger.info(f"✅ 检测到设备: {device}")
        
        # 测试缓存目录
        cache_dir = get_cache_dir("TEST_CACHE_DIR", "./test_cache")
        logger.info(f"✅ 缓存目录: {cache_dir}")
        
        # 测试模型设备配置
        config = get_model_device_config(device, "funasr")
        logger.info(f"✅ 设备配置: {config}")
        
        # 测试设备信息
        device_info = DeviceManager.get_device_info()
        logger.info(f"✅ 设备信息: {device_info['device']}, PyTorch: {device_info['torch_version']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ DeviceManager测试失败: {e}")
        return False

async def test_emotion_analyzer():
    """测试EmotionAnalyzer功能"""
    try:
        logger.info("🔍 测试EmotionAnalyzer功能...")
        
        from app.utils import (
            extract_sensevoice_emotion_info,
            extract_sensevoice_event_info,
            clean_sensevoice_text,
            EmotionAnalyzer
        )
        
        # 测试SenseVoice文本处理
        test_text = "<|HAPPY|>你好小智<|MUSIC|>"
        
        # 测试情感提取
        emotion_info = extract_sensevoice_emotion_info(test_text)
        logger.info(f"✅ 情感信息: {emotion_info}")
        
        # 测试事件提取
        events = extract_sensevoice_event_info(test_text)
        logger.info(f"✅ 声学事件: {events}")
        
        # 测试文本清理
        clean_text = clean_sensevoice_text(test_text)
        logger.info(f"✅ 清理后文本: '{clean_text}'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ EmotionAnalyzer测试失败: {e}")
        return False

async def test_funaudio_service():
    """测试FunAudioLLM服务"""
    try:
        logger.info("🔍 测试FunAudioLLM服务...")
        
        from app.services.funaudio_service_real import FunAudioLLMService
        
        # 创建服务实例
        service = FunAudioLLMService()
        logger.info(f"✅ 服务实例创建成功，设备: {service.device}")
        
        # 测试健康检查
        health_status = await service.get_health_status()
        logger.info(f"✅ 健康检查: {health_status['message']}")
        
        # 测试内部方法
        test_text = "<|HAPPY|>你好小智<|MUSIC|>"
        
        emotion_info = service._extract_emotion_info(test_text)
        logger.info(f"✅ 内部情感提取: {emotion_info}")
        
        events = service._extract_event_info(test_text)
        logger.info(f"✅ 内部事件提取: {events}")
        
        clean_text = service._clean_text(test_text)
        logger.info(f"✅ 内部文本清理: '{clean_text}'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FunAudioLLM服务测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    logger.info("🚀 开始FunAudioLLM修复验证测试")
    
    tests = [
        ("导入测试", test_imports),
        ("DeviceManager测试", test_device_manager),
        ("EmotionAnalyzer测试", test_emotion_analyzer),
        ("FunAudioLLM服务测试", test_funaudio_service)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 运行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            if result:
                logger.info(f"✅ {test_name} 通过")
                passed += 1
            else:
                logger.error(f"❌ {test_name} 失败")
        except Exception as e:
            logger.error(f"❌ {test_name} 异常: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"📊 测试结果: {passed}/{total} 通过")
    logger.info(f"{'='*50}")
    
    if passed == total:
        logger.info("🎉 所有测试通过！FunAudioLLM修复成功！")
        return True
    else:
        logger.error(f"💥 有 {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 