from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
import traceback
import os

from .config import settings
from .routes import chat, health, voice

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于FunAudioLLM的高性能语音对话系统，支持语音识别、情感分析和对话",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
if os.path.exists(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# 注册路由
app.include_router(chat.router)
app.include_router(health.router)
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"全局异常: {exc}")
    logger.error(f"请求URL: {request.url}")
    logger.error(f"异常详情: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "error": str(exc) if settings.debug else "Internal server error"
        }
    )

async def startup_event():
    """应用启动事件"""
    logger.info(f"🚀 {settings.app_name} v{settings.app_version} 启动成功")
    logger.info(f"📂 上传目录: {settings.upload_dir}")
    logger.info(f"🤖 LM Studio URL: {settings.lm_studio_base_url}")
    logger.info(f"🔧 调试模式: {'开启' if settings.debug else '关闭'}")
    
    # 检查FunAudioLLM语音引擎状态
    try:
        from app.services import funaudio_service
        
        logger.info("🎤 检查FunAudioLLM语音引擎状态...")
        
        # 检查FunAudioLLM
        funaudio_status = await funaudio_service.health_check()
        logger.info(f"🔗 FunAudioLLM状态: {'✅ 正常' if funaudio_status.get('available') else '❌ 异常'}")
        
        if funaudio_status.get('available'):
            logger.info("🌟 FunAudioLLM功能:")
            for feature in funaudio_status.get('features', []):
                logger.info(f"   • {feature}")
        
    except Exception as e:
        logger.warning(f"FunAudioLLM语音引擎连接检查失败: {e}")

async def shutdown_event():
    """应用关闭事件"""
    logger.info("👋 应用正在关闭...")
    
    # 清理临时文件
    try:
        from app.services.tts_service import tts_service
        cleaned_count = tts_service.clean_old_files(days=1)
        logger.info(f"🧹 清理了 {cleaned_count} 个临时音频文件")
    except Exception as e:
        logger.error(f"清理临时文件失败: {e}")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用小智小智高性能语音对话系统",
        "version": settings.app_version,
        "engine": "FunAudioLLM",
        "features": [
            "高性能语音识别 (比Whisper快15倍)",
            "情感识别和声学事件检测",
            "50+语言支持",
            "连续语音对话",
            "多会话管理"
        ],
        "docs": "/docs" if settings.debug else "文档已禁用",
        "api_endpoints": {
            "engine_status": "/api/voice/engine",
            "chat": "/api/voice/chat",
            "recognize": "/api/voice/recognize",
            "analyze": "/api/voice/analyze",
            "conversation": "/api/voice/conversation/{session_id}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print(f"🚀 启动 {settings.app_name} v{settings.app_version}")
    print(f"📂 上传目录: {settings.upload_dir}")
    print(f"🎤 语音引擎: FunAudioLLM (SenseVoice)")
    print(f"🌟 特性: 高性能识别、情感分析、50+语言支持")
    print(f"🔧 调试模式: {'开启' if settings.debug else '关闭'}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
        timeout_keep_alive=300,  # 增加keep-alive超时到5分钟
        timeout_graceful_shutdown=30  # 优雅关闭超时30秒
    ) 