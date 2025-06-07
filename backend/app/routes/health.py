from fastapi import APIRouter, Response
from app.models.schemas import HealthResponse
from app.services.lm_studio_service import lm_studio_service
from app.config import settings
import logging
import time
import psutil
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """系统健康检查"""
    try:
        # 检查LM Studio服务状态
        lm_studio_status = await lm_studio_service.health_check()
        
        # 检查Nacos服务状态
        nacos_status = {}
        try:
            from app.services.nacos_service import nacos_service
            nacos_status = await nacos_service.health_check()
        except Exception as e:
            logger.warning(f"Nacos健康检查失败: {e}")
            nacos_status = {"available": False, "error": str(e)}
        
        # 检查各个服务组件
        services = {
            "lm_studio": lm_studio_status,
            "ocr": True,  # OCR服务通常总是可用的
            "tts": True,  # TTS服务通常总是可用的
            "upload": True,  # 文件上传服务总是可用的
            "nacos": nacos_status.get("service_registered", False) if settings.nacos_enabled else True
        }
        
        # 确定整体状态
        overall_status = "healthy" if all(services.values()) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            lm_studio_status=lm_studio_status,
            services=services,
            nacos_info=nacos_status if settings.nacos_enabled else None
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthResponse(
            status="unhealthy",
            lm_studio_status=False,
            services={"error": str(e)}
        ) 