"""
设备检测和优化工具模块
提供设备检测、Apple Silicon MPS优化、内存管理等功能
"""

import os
import torch
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DeviceManager:
    """设备管理工具类"""
    
    @staticmethod
    def get_optimal_device() -> str:
        """
        获取最优计算设备
        
        Returns:
            str: 设备类型 ("cuda", "mps", "cpu")
        """
        try:
            if torch.cuda.is_available():
                device = "cuda"
                logger.info("🚀 检测到 CUDA，使用 GPU 加速")
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = "mps"
                logger.info("🍎 检测到 Apple Silicon，使用 MPS 加速")
            else:
                device = "cpu"
                logger.info("🔧 使用 CPU 模式")
            
            return device
            
        except Exception as e:
            logger.error(f"❌ 设备检测失败: {e}")
            return "cpu"
    
    @staticmethod
    def setup_mps_optimization() -> Dict[str, Any]:
        """
        设置 Apple Silicon MPS 优化
        
        Returns:
            Dict[str, Any]: 优化配置结果
        """
        try:
            if not (hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()):
                return {
                    "enabled": False,
                    "reason": "MPS 不可用",
                    "device": "cpu"
                }
            
            # 启用 MPS 回退机制
            os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
            
            # 设置内存使用比例
            try:
                torch.mps.set_per_process_memory_fraction(0.8)
            except Exception as e:
                logger.warning(f"⚠️ 设置MPS内存比例失败: {e}")
            
            # 启用 TF32 优化（如果支持）
            try:
                torch.backends.mps.allow_tf32 = True
            except Exception as e:
                logger.warning(f"⚠️ 启用TF32优化失败: {e}")
            
            logger.info("✅ Apple Silicon MPS 优化已启用")
            
            return {
                "enabled": True,
                "device": "mps",
                "optimizations": [
                    "MPS回退机制",
                    "内存使用比例限制(80%)",
                    "TF32优化"
                ],
                "memory_fraction": 0.8
            }
            
        except Exception as e:
            logger.error(f"❌ MPS优化设置失败: {e}")
            return {
                "enabled": False,
                "error": str(e),
                "device": "cpu"
            }
    
    @staticmethod
    def setup_device_optimization(device: str) -> Dict[str, Any]:
        """
        根据设备类型设置优化配置
        
        Args:
            device: 设备类型
            
        Returns:
            Dict[str, Any]: 优化配置结果
        """
        try:
            optimizations = []
            
            if device == "mps":
                # Apple Silicon MPS 优化
                mps_config = DeviceManager.setup_mps_optimization()
                optimizations.extend(mps_config.get("optimizations", []))
                
            elif device == "cuda":
                # CUDA 优化
                try:
                    torch.backends.cudnn.benchmark = True
                    torch.backends.cudnn.deterministic = False
                    optimizations.append("CUDNN基准测试优化")
                    optimizations.append("CUDNN非确定性优化")
                except Exception as e:
                    logger.warning(f"⚠️ CUDA优化设置失败: {e}")
                
            elif device == "cpu":
                # CPU 优化
                try:
                    torch.set_num_threads(torch.get_num_threads())
                    optimizations.append(f"CPU线程数: {torch.get_num_threads()}")
                except Exception as e:
                    logger.warning(f"⚠️ CPU优化设置失败: {e}")
            
            logger.info(f"✅ {device.upper()} 设备优化配置完成")
            
            return {
                "device": device,
                "optimizations": optimizations,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"❌ 设备优化配置失败: {e}")
            return {
                "device": device,
                "optimizations": [],
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_memory_usage(device: str = None) -> str:
        """
        获取设备内存使用情况
        
        Args:
            device: 设备类型，如果为None则自动检测
            
        Returns:
            str: 内存使用情况描述
        """
        try:
            if device is None:
                device = DeviceManager.get_optimal_device()
            
            if device == "mps":
                try:
                    allocated = torch.mps.current_allocated_memory() / 1024 / 1024  # MB
                    return f"{allocated:.1f} MB (MPS)"
                except Exception:
                    return "MPS 内存信息不可用"
                    
            elif device == "cuda":
                try:
                    allocated = torch.cuda.memory_allocated() / 1024 / 1024  # MB
                    cached = torch.cuda.memory_reserved() / 1024 / 1024  # MB
                    return f"已分配: {allocated:.1f} MB, 已缓存: {cached:.1f} MB (CUDA)"
                except Exception:
                    return "CUDA 内存信息不可用"
                    
            else:
                return "CPU 模式"
                
        except Exception as e:
            logger.error(f"❌ 获取内存使用情况失败: {e}")
            return "内存信息不可用"
    
    @staticmethod
    def clear_device_cache(device: str = None) -> bool:
        """
        清理设备缓存
        
        Args:
            device: 设备类型，如果为None则自动检测
            
        Returns:
            bool: 清理是否成功
        """
        try:
            if device is None:
                device = DeviceManager.get_optimal_device()
            
            if device == "mps":
                torch.mps.empty_cache()
                logger.info("🧹 MPS 缓存已清理")
                
            elif device == "cuda":
                torch.cuda.empty_cache()
                logger.info("🧹 CUDA 缓存已清理")
                
            else:
                logger.info("ℹ️ CPU 模式无需清理缓存")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 清理设备缓存失败: {e}")
            return False
    
    @staticmethod
    def get_device_info(device: str = None) -> Dict[str, Any]:
        """
        获取设备详细信息
        
        Args:
            device: 设备类型，如果为None则自动检测
            
        Returns:
            Dict[str, Any]: 设备信息
        """
        try:
            if device is None:
                device = DeviceManager.get_optimal_device()
            
            info = {
                "device": device,
                "torch_version": torch.__version__,
                "memory_usage": DeviceManager.get_memory_usage(device)
            }
            
            if device == "cuda":
                info.update({
                    "cuda_available": torch.cuda.is_available(),
                    "cuda_device_count": torch.cuda.device_count(),
                    "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                    "cudnn_version": torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else None
                })
                
            elif device == "mps":
                info.update({
                    "mps_available": torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False,
                    "acceleration": "Apple Silicon MPS"
                })
                
            else:
                info.update({
                    "cpu_count": torch.get_num_threads(),
                    "acceleration": "CPU"
                })
            
            return info
            
        except Exception as e:
            logger.error(f"❌ 获取设备信息失败: {e}")
            return {
                "device": "unknown",
                "error": str(e)
            }

# 便利函数
def get_optimal_device() -> str:
    """获取最优设备便利函数"""
    return DeviceManager.get_optimal_device()

def setup_mps_optimization() -> Dict[str, Any]:
    """设置MPS优化便利函数"""
    return DeviceManager.setup_mps_optimization()

def setup_device_optimization(device: str) -> Dict[str, Any]:
    """设置设备优化便利函数"""
    return DeviceManager.setup_device_optimization(device)

def get_memory_usage(device: str = None) -> str:
    """获取内存使用情况便利函数"""
    return DeviceManager.get_memory_usage(device)

def clear_device_cache(device: str = None) -> bool:
    """清理设备缓存便利函数"""
    return DeviceManager.clear_device_cache(device)

def get_device_info(device: str = None) -> Dict[str, Any]:
    """获取设备信息便利函数"""
    return DeviceManager.get_device_info(device) 