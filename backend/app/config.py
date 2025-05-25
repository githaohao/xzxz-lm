import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # 应用基础配置
    app_name: str = "TZ-LM 多模态聊天系统"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # LM Studio API 配置
    lm_studio_base_url: str = "http://127.0.0.1:1234/v1"
    lm_studio_model: str = "qwen3-14b-mlx"
    lm_studio_api_key: str = "not-needed"  # LM Studio 通常不需要 API key
    
    # 文件上传配置
    upload_dir: str = "uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: List[str] = [".pdf", ".png", ".jpg", ".jpeg", ".wav", ".mp3"]
    
    # OCR 配置
    tesseract_path: str = "/usr/local/bin/tesseract"  # macOS 默认路径
    ocr_languages: str = "chi_sim+eng"  # 中文简体 + 英文
    use_paddleocr: bool = True  # 优先使用 PaddleOCR
    
    # TTS 配置
    tts_voice: str = "zh-CN-XiaoxiaoNeural"  # Edge TTS 中文女声
    tts_rate: str = "+0%"
    tts_volume: str = "+0%"
    
    # 语音识别配置
    stt_model: str = "whisper-1"
    whisper_model_size: str = "base"
    
    # FunAudioLLM 配置 - Apple Silicon 优化
    funaudio_model_path: str = "iic/SenseVoiceSmall"
    funaudio_device: str = "auto"
    funaudio_cache_dir: str = "./models/cache"
    
    # 硬件加速配置
    use_mps: bool = True
    use_cuda: bool = False
    device_type: str = "auto"
    
    # 模型下载配置
    hf_endpoint: str = "https://hf-mirror.com"
    modelscope_cache: str = "./models/modelscope"
    
    # Apple Silicon 性能优化
    pytorch_enable_mps_fallback: str = "1"
    mps_memory_fraction: str = "0.8"
    omp_num_threads: str = "8"
    
    # CORS 配置
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 创建全局设置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.upload_dir, exist_ok=True) 