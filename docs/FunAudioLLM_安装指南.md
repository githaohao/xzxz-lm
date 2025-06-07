# 🎤 FunAudioLLM & SenseVoice 安装配置指南

## 📋 概述

FunAudioLLM 是阿里巴巴开源的高性能语音处理框架，SenseVoice 是其核心的语音识别模型，具有以下特点：

- ⚡ **超高速度**：比 Whisper-Large 快 15 倍
- 🎯 **高精度**：在多个基准测试中达到 SOTA 性能
- 🌍 **多语言**：支持 50+ 种语言
- 🎭 **情感识别**：内置情感分析和声学事件检测
- 📊 **实时处理**：支持流式语音识别

## 🛠️ 系统要求

### 硬件要求
- **CPU**: 4 核心以上（推荐 8 核心）
- **内存**: 8GB 以上（推荐 16GB）
- **GPU**: 可选，NVIDIA GPU 可显著提升性能
- **存储**: 至少 10GB 可用空间

### 软件要求
- **Python**: 3.8 - 3.11
- **PyTorch**: 1.13.0+
- **CUDA**: 11.7+ (如果使用 GPU)

## 📦 安装步骤

### 1. 环境准备

```bash
# 创建虚拟环境
conda create -n funaudio python=3.10
conda activate funaudio

# 或使用 venv
python -m venv funaudio_env
source funaudio_env/bin/activate  # Linux/Mac
# funaudio_env\Scripts\activate  # Windows
```

### 2. 安装 PyTorch

```bash
# CPU 版本
pip install torch torchvision torchaudio

# GPU 版本 (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# GPU 版本 (CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3. 安装 FunASR

```bash
# 安装 FunASR 核心库
pip install funasr

# 安装额外依赖
pip install modelscope
pip install soundfile
pip install librosa
```

### 4. 安装其他依赖

```bash
# 音频处理
pip install ffmpeg-python
pip install webrtcvad

# 模型加载
pip install transformers
pip install accelerate

# 可选：性能优化
pip install onnxruntime  # CPU 推理优化
pip install onnxruntime-gpu  # GPU 推理优化
```

## 🔧 配置 SenseVoice 模型

### 1. 更新后端服务

编辑 `backend/app/services/funaudio_service.py`：

```python
import logging
import torch
import numpy as np
from typing import Optional, Dict, Any, List
from io import BytesIO
import tempfile
import os
import asyncio
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

logger = logging.getLogger(__name__)

class FunAudioLLMService:
    """
    基于阿里FunAudioLLM的语音服务
    集成SenseVoice进行高性能语音识别、情感分析和声学事件检测
    """
    
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
        self.max_history_length = 20
        
        logger.info(f"🎤 初始化FunAudioLLM服务，设备: {self.device}")
        
    async def initialize(self):
        """初始化SenseVoice模型"""
        try:
            logger.info("📥 加载SenseVoice模型...")
            
            # 加载SenseVoice模型
            self.model = AutoModel(
                model="iic/SenseVoiceSmall",  # 或 "iic/SenseVoiceLarge"
                trust_remote_code=True,
                vad_model="fsmn-vad",
                vad_kwargs={"max_single_segment_time": 30000},
                device=self.device,
            )
            
            logger.info("✅ FunAudioLLM SenseVoice模型加载成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ FunAudioLLM模型加载失败: {e}")
            return False
    
    async def voice_recognition(self, audio_data: bytes, language: str = "auto") -> Dict[str, Any]:
        """
        高性能语音识别，支持情感分析和声学事件检测
        """
        try:
            if not self.model:
                await self.initialize()
            
            logger.info("🎯 开始FunAudioLLM语音识别...")
            
            # 保存音频到临时文件
            temp_audio_path = self._save_audio_temp(audio_data)
            
            try:
                # 使用SenseVoice进行识别
                result = self.model.generate(
                    input=temp_audio_path,
                    cache={},
                    language=language,  # "auto", "zh", "en", "yue", "ja", "ko"
                    use_itn=True,
                    batch_size_s=60,
                    merge_vad=True,
                    merge_length_s=15,
                )
                
                # 处理识别结果
                raw_text = result[0]["text"]
                processed_text = rich_transcription_postprocess(raw_text)
                
                # 解析情感和事件信息
                emotion_info = self._extract_emotion_info(processed_text)
                event_info = self._extract_event_info(processed_text)
                clean_text = self._clean_text(processed_text)
                
                logger.info(f"✅ 语音识别成功: {clean_text[:50]}...")
                
                return {
                    "success": True,
                    "recognized_text": clean_text,
                    "raw_text": raw_text,
                    "processed_text": processed_text,
                    "emotion": emotion_info,
                    "events": event_info,
                    "language": language,
                    "engine": "FunAudioLLM-SenseVoice",
                    "confidence": result[0].get("confidence", 1.0)
                }
                
            finally:
                # 清理临时文件
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
            
        except Exception as e:
            logger.error(f"❌ FunAudioLLM语音识别失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "engine": "FunAudioLLM-SenseVoice",
                "recognized_text": ""
            }
    
    def _save_audio_temp(self, audio_data: bytes) -> str:
        """保存音频数据到临时文件"""
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_file.write(audio_data)
            temp_file.close()
            return temp_file.name
        except Exception as e:
            logger.error(f"❌ 保存临时音频文件失败: {e}")
            raise
    
    # ... 其他方法保持不变
```

### 2. 更新服务配置

编辑 `backend/app/services/__init__.py`：

```python
# 选择使用真实服务还是模拟服务
USE_REAL_FUNAUDIO = True  # 设置为 True 使用真实服务

if USE_REAL_FUNAUDIO:
    from .funaudio_service import funaudio_service
else:
    from .funaudio_service_mock import funaudio_service
```

### 3. 安装音频处理依赖

```bash
# 进入后端目录
cd backend

# 安装音频处理库
pip install pydub
pip install scipy
pip install numpy

# 系统级音频工具 (Ubuntu/Debian)
sudo apt-get install ffmpeg libsndfile1

# macOS
brew install ffmpeg libsndfile

# Windows
# 下载 ffmpeg 并添加到 PATH
```

## 🚀 启动配置

### 1. 更新 requirements.txt

```txt
# 在 backend/requirements.txt 中添加
funasr>=1.0.0
modelscope>=1.9.0
soundfile>=0.12.1
librosa>=0.10.0
torch>=1.13.0
transformers>=4.30.0
accelerate>=0.20.0
```

### 2. 环境变量配置

创建 `backend/.env` 文件：

```env
# FunAudioLLM 配置
FUNAUDIO_MODEL_PATH=iic/SenseVoiceSmall
FUNAUDIO_DEVICE=auto  # auto, cpu, cuda
FUNAUDIO_CACHE_DIR=./models/cache

# 模型下载配置
HF_ENDPOINT=https://hf-mirror.com  # 中国用户加速
MODELSCOPE_CACHE=./models/modelscope
```

### 3. 启动服务

```bash
# 启动后端服务
cd backend
python -m uvicorn app.main:app --reload --port 8000

# 启动前端服务
cd frontend
pnpm dev
```

## 🔍 验证安装

### 1. 检查模型加载

访问：`http://localhost:8000/voice/engine`

应该看到：
```json
{
  "success": true,
  "engine": {
    "name": "FunAudioLLM",
    "status": {
      "available": true,
      "model_name": "FunAudioLLM-SenseVoice",
      "device": "cuda",
      "features": [
        "高性能语音识别 (比Whisper快15倍)",
        "情感识别",
        "声学事件检测",
        "50+语言支持"
      ]
    }
  }
}
```

### 2. 测试语音识别

访问：`http://localhost:3000/voice-funaudio`

现在应该能看到真实的语音识别结果！

## ⚡ 性能优化

### 1. GPU 加速

```python
# 确保 CUDA 可用
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device count: {torch.cuda.device_count()}")
```

### 2. 模型量化

```python
# 在模型初始化时启用量化
self.model = AutoModel(
    model="iic/SenseVoiceSmall",
    trust_remote_code=True,
    device=self.device,
    # 启用量化以减少内存使用
    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
)
```

### 3. 批处理优化

```python
# 批量处理多个音频文件
results = self.model.generate(
    input=[audio_path1, audio_path2, audio_path3],
    batch_size_s=60,
    # 其他参数...
)
```

## 🐛 常见问题

### 1. 模型下载失败

```bash
# 使用镜像源
export HF_ENDPOINT=https://hf-mirror.com
pip install funasr
```

### 2. CUDA 内存不足

```python
# 减少批处理大小
batch_size_s=30  # 默认 60

# 使用 CPU
device="cpu"
```

### 3. 音频格式不支持

```python
# 安装额外的音频编解码器
pip install ffmpeg-python
sudo apt-get install libavcodec-extra
```

### 4. 权限问题

```bash
# 确保临时目录可写
chmod 755 /tmp
```

## 📊 模型选择

### SenseVoice 模型对比

| 模型 | 大小 | 速度 | 精度 | 推荐场景 |
|------|------|------|------|----------|
| SenseVoiceSmall | ~500MB | 极快 | 高 | 实时应用 |
| SenseVoiceLarge | ~1.5GB | 快 | 极高 | 离线处理 |

### 语言支持

- **中文**: zh (普通话)
- **英文**: en
- **粤语**: yue
- **日语**: ja
- **韩语**: ko
- **自动检测**: auto (推荐)

## 🎉 完成！

现在你已经成功安装和配置了真正的 FunAudioLLM 和 SenseVoice 模型！

访问 `http://localhost:3000/voice-funaudio` 体验真实的高性能语音识别功能。

## 📞 技术支持

如果遇到问题：

1. 查看后端日志：`tail -f backend/logs/app.log`
2. 检查模型状态：`GET /api/voice/engine`
3. 验证环境：`python -c "import funasr; print('FunASR installed successfully')"`

享受 15 倍于 Whisper 的语音识别速度吧！🚀 