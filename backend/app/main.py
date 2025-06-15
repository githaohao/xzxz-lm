import os

# 设置 tokenizers 环境变量，避免并行处理警告
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
import sys
import traceback

from .config import settings
from .routes import chat, health, voice, chat_history, rag
from .database import Database
from .middleware.auth import UserAuthMiddleware

# 配置详细的日志系统
def setup_logging():
    """设置详细的日志配置"""
    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 清除默认处理器
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 创建详细的格式器
    formatter = logging.Formatter(
        '%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到根日志器
    root_logger.addHandler(console_handler)
    
    # 设置特定模块的日志级别
    logging.getLogger("app.routes.chat").setLevel(logging.INFO)
    logging.getLogger("app.services.rag_service").setLevel(logging.INFO)
    logging.getLogger("app.services.lm_studio_service").setLevel(logging.INFO)
    logging.getLogger("app.services.ocr_service").setLevel(logging.INFO)
    
    # 禁用一些过于冗长的第三方库日志
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# 设置日志
logger = setup_logging()

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

# 添加用户认证中间件
app.add_middleware(UserAuthMiddleware)

# 静态文件服务
if os.path.exists(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# 注册路由
app.include_router(chat.router)
app.include_router(health.router)
app.include_router(voice.router)
app.include_router(chat_history.router)
app.include_router(rag.router)


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

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("=" * 80)
    logger.info(f"🚀 {settings.app_name} v{settings.app_version} 启动成功")
    logger.info(f"📂 上传目录: {settings.upload_dir}")
    logger.info(f"🤖 LM Studio URL: {settings.lm_studio_base_url}")
    logger.info(f"🔧 调试模式: {'开启' if settings.debug else '关闭'}")
    logger.info(f"🌐 Nacos功能: {'开启' if settings.nacos_enabled else '关闭'}")
    logger.info("=" * 80)
    
    # 初始化数据库
    try:
        logger.info("🗄️ 初始化数据库...")
        db = Database()
        await db.initialize()
        logger.info("✅ 数据库初始化成功")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise e
    
    # 初始化和注册Nacos服务
    if settings.nacos_enabled:
        try:
            from app.services.nacos_service import nacos_service
            
            logger.info("🔗 初始化Nacos服务...")
            if await nacos_service.initialize():
                logger.info("🚀 正在注册服务到Nacos...")
                if await nacos_service.register_service():
                    logger.info("✅ Nacos服务注册成功")
                else:
                    logger.error("❌ Nacos服务注册失败")
            else:
                logger.error("❌ Nacos初始化失败")
        except Exception as e:
            logger.error(f"❌ Nacos服务配置失败: {e}")
    
    # 检查FunAudioLLM语音引擎状态
    try:
        from app.services.funaudio_service_real import funaudio_service
        
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
    logger.info("✅ 应用启动完成，准备接收请求...")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("👋 应用正在关闭...")
    
    # 注销Nacos服务
    if settings.nacos_enabled:
        try:
            from app.services.nacos_service import nacos_service
            logger.info("🔗 正在注销Nacos服务...")
            if await nacos_service.deregister_service():
                logger.info("✅ Nacos服务注销成功")
            else:
                logger.warning("⚠️ Nacos服务注销失败")
        except Exception as e:
            logger.error(f"❌ Nacos服务注销异常: {e}")
    
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
    logger.info("收到根路径访问请求")
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
            "engine_status": "/voice/engine",
            "chat": "/voice/chat",
            "recognize": "/voice/recognize",
            "analyze": "/voice/analyze",
            "conversation": "/voice/conversation/{session_id}"
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
        access_log=True,
        use_colors=True,
        timeout_keep_alive=300,  # 增加keep-alive超时到5分钟
        timeout_graceful_shutdown=30  # 优雅关闭超时30秒
    ) 