import os
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # 应用基础配置
    app_name: str = "小智小智 多模态聊天系统"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # LM Studio API 配置
    lm_studio_base_url: str = "http://127.0.0.1:1234/v1"
    lm_studio_model: str = "deepseek-r1-0528-qwen3-8b-mlx@8bit"
    lm_studio_api_key: str = "not-needed"  # LM Studio 通常不需要 API key
    
    # 文件上传配置
    upload_dir: str = "uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: str = ".pdf,.png,.jpg,.jpeg,.wav,.mp3,.txt,.doc,.docx"  # 改为字符串格式
    
    # OCR 配置
    tesseract_path: str = "/usr/local/bin/tesseract"  # macOS 默认路径
    ocr_languages: str = "chi_sim+eng"  # 中文简体 + 英文
    
    # OCR 引擎配置 - Apple Silicon 优化
    ocr_engine: str = "paddleocr"  # paddleocr, tesseract, auto
    paddleocr_use_gpu: bool = True  # 使用GPU加速
    paddleocr_use_angle_cls: bool = True  # 文字方向分类
    paddleocr_lang: str = "ch"  # ch, en, japan, korean等
    paddleocr_det_model_dir: Optional[str] = None  # 自定义检测模型路径
    paddleocr_rec_model_dir: Optional[str] = None  # 自定义识别模型路径
    paddleocr_cls_model_dir: Optional[str] = None  # 自定义分类模型路径
    
    # OCR 图像预处理配置
    ocr_image_dpi: int = 300  # PDF转图片DPI
    ocr_image_enhance: bool = True  # 图像增强 - 启用以提升准确率
    ocr_parallel_pages: int = 4  # 并行处理页数
    ocr_cache_enabled: bool = True  # 启用结果缓存
    ocr_cache_ttl: int = 3600  # 缓存时间（秒）
    
    # TTS 配置
    tts_voice: str = "zh-CN-XiaoxiaoNeural"  # Edge TTS 中文女声
    
    # RAG 配置
    embedding_model: str = "moka-ai/m3e-base"  # 中文友好的嵌入模型，支持多语言
    # 其他可选模型:
    # - "GanymedeNil/text2vec-large-chinese" (中文专用，较大)
    # - "shibing624/text2vec-base-chinese" (中文专用，中等)
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_default_top_k: int = 5
    rag_default_min_similarity: float = 0.355  # 精确调优的阈值，确保姓名查询通过
    rag_enable_cache: bool = True  # 启用RAG缓存
    rag_cache_ttl: int = 3600  # RAG缓存时间（秒）
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
    
    # Nacos 服务发现配置
    nacos_enabled: bool = True  # 是否启用Nacos
    nacos_server_addresses: str = "nacos:8848"  # Nacos服务器地址
    nacos_namespace: str = ""  # 命名空间ID，默认为public
    nacos_group: str = "DEFAULT_GROUP"  # 服务分组
    nacos_cluster_name: str = "DEFAULT"  # 集群名称
    nacos_service_name: str = "xzxz-lm-service"  # 服务名称
    nacos_weight: float = 1.0  # 服务权重
    nacos_metadata: dict = {
        "version": "1.0.0",
        "service_type": "ai_chat",
        "framework": "fastapi",
        "features": "multimodal,voice,ocr"
    }
    
    # 服务实例配置
    service_ip: str = "0.0.0.0"  # 服务IP，注册到Nacos时使用
    service_port: int = 8000  # 服务端口
    service_health_check_url: str = "/health"  # 健康检查路径
    
    # 若依Gateway适配配置
    gateway_context_path: str = "/lm"  # Gateway中的服务路径前缀
    gateway_service_id: str = "xzxz-lm-service"  # Gateway中的服务ID
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    @property
    def allowed_file_types_list(self) -> List[str]:
        """获取允许的文件类型列表"""
        return [ext.strip() for ext in self.allowed_file_types.split(',')]

# 创建全局设置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.upload_dir, exist_ok=True) 