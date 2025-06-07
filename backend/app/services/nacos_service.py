import logging
import json
import asyncio
import socket
from typing import Optional, Dict, Any
from nacos import NacosClient
import psutil
import time

from ..config import settings

logger = logging.getLogger(__name__)

class NacosService:
    """Nacos服务注册和发现管理器"""
    
    def __init__(self):
        self.client: Optional[NacosClient] = None
        self.service_instance_id: Optional[str] = None
        self.is_registered = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> bool:
        """初始化Nacos客户端"""
        if not settings.nacos_enabled:
            logger.info("Nacos功能未启用")
            return False
            
        try:
            self.client = NacosClient(
                server_addresses=settings.nacos_server_addresses,
                namespace=settings.nacos_namespace,
                username=getattr(settings, 'nacos_username', None),
                password=getattr(settings, 'nacos_password', None)
            )
            
            # 测试连接
            await self._test_connection()
            logger.info(f"✅ Nacos客户端初始化成功: {settings.nacos_server_addresses}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Nacos客户端初始化失败: {e}")
            return False
    
    async def _test_connection(self):
        """测试Nacos连接"""
        try:
            # 尝试获取服务列表来测试连接
            self.client.list_naming_instance(
                service_name="test",
                group_name=settings.nacos_group,
                healthy_only=False
            )
        except Exception as e:
            raise Exception(f"Nacos连接测试失败: {e}")
    
    def _get_local_ip(self) -> str:
        """获取本机IP地址"""
        try:
            # 如果配置了特定IP，优先使用
            if settings.service_ip and settings.service_ip != "0.0.0.0":
                return settings.service_ip
            
            # 自动获取本机IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                logger.info(f"🔍 自动检测到本机IP: {ip}")
                return ip
        except Exception as e:
            logger.warning(f"获取本机IP失败: {e}, 使用localhost")
            return "127.0.0.1"
    
    def _generate_instance_id(self) -> str:
        """生成服务实例ID"""
        ip = self._get_local_ip()
        port = settings.service_port
        timestamp = int(time.time())
        return f"{settings.nacos_service_name}#{ip}#{port}#{timestamp}"
    
    def _get_instance_metadata(self) -> Dict[str, Any]:
        """获取服务实例元数据"""
        metadata = settings.nacos_metadata.copy()
        
        # 添加运行时信息
        metadata.update({
            "startup_time": str(int(time.time())),
            "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}",
            "cpu_count": str(psutil.cpu_count()),
            "memory_gb": str(round(psutil.virtual_memory().total / 1024**3, 1)),
            "health_check_url": settings.service_health_check_url,
            "context_path": settings.gateway_context_path,
            "service_id": settings.gateway_service_id
        })
        
        return metadata
    
    async def register_service(self) -> bool:
        """注册服务到Nacos"""
        if not self.client:
            logger.error("Nacos客户端未初始化")
            return False
        
        try:
            ip = self._get_local_ip()
            port = settings.service_port
            self.service_instance_id = self._generate_instance_id()
            
            # 注册服务实例
            success = self.client.add_naming_instance(
                service_name=settings.nacos_service_name,
                ip=ip,
                port=port,
                cluster_name=settings.nacos_cluster_name,
                weight=settings.nacos_weight,
                group_name=settings.nacos_group,
                metadata=self._get_instance_metadata(),
                enable=True,
                healthy=True,
                ephemeral=True  # 临时实例，自动清理
            )
            
            if success:
                self.is_registered = True
                logger.info(f"🚀 服务注册成功:")
                logger.info(f"   服务名: {settings.nacos_service_name}")
                logger.info(f"   实例ID: {self.service_instance_id}")
                logger.info(f"   地址: {ip}:{port}")
                logger.info(f"   分组: {settings.nacos_group}")
                logger.info(f"   集群: {settings.nacos_cluster_name}")
                
                # 启动心跳检测
                await self._start_heartbeat()
                return True
            else:
                logger.error("❌ 服务注册失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 服务注册异常: {e}")
            return False
    
    async def deregister_service(self) -> bool:
        """注销服务"""
        if not self.client or not self.is_registered:
            return True
        
        try:
            # 停止心跳
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                
            ip = self._get_local_ip()
            port = settings.service_port
            
            success = self.client.remove_naming_instance(
                service_name=settings.nacos_service_name,
                ip=ip,
                port=port,
                cluster_name=settings.nacos_cluster_name,
                group_name=settings.nacos_group
            )
            
            if success:
                self.is_registered = False
                logger.info(f"👋 服务注销成功: {settings.nacos_service_name}")
                return True
            else:
                logger.error("❌ 服务注销失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 服务注销异常: {e}")
            return False
    
    async def _start_heartbeat(self):
        """启动心跳检测"""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.is_registered:
            try:
                await asyncio.sleep(30)  # 每30秒发送一次心跳
                
                if self.client and self.is_registered:
                    ip = self._get_local_ip()
                    port = settings.service_port
                    
                    # 发送心跳
                    self.client.send_heartbeat(
                        service_name=settings.nacos_service_name,
                        ip=ip,
                        port=port,
                        cluster_name=settings.nacos_cluster_name,
                        group_name=settings.nacos_group
                    )
                    
                    logger.debug(f"💓 心跳发送成功: {settings.nacos_service_name}")
                    
            except asyncio.CancelledError:
                logger.info("心跳任务被取消")
                break
            except Exception as e:
                logger.error(f"心跳发送失败: {e}")
                # 心跳失败，尝试重新注册
                await asyncio.sleep(10)
                await self.register_service()
    
    async def get_service_instances(self, service_name: str) -> list:
        """获取服务实例列表"""
        if not self.client:
            return []
        
        try:
            instances = self.client.list_naming_instance(
                service_name=service_name,
                group_name=settings.nacos_group,
                healthy_only=True
            )
            return instances.get('hosts', [])
        except Exception as e:
            logger.error(f"获取服务实例失败: {e}")
            return []
    
    async def get_config(self, data_id: str, group: str = None) -> Optional[str]:
        """获取配置"""
        if not self.client:
            return None
        
        try:
            group = group or settings.nacos_group
            config = self.client.get_config(data_id, group)
            return config
        except Exception as e:
            logger.error(f"获取配置失败: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {
            "nacos_enabled": settings.nacos_enabled,
            "nacos_connected": self.client is not None,
            "service_registered": self.is_registered,
            "service_name": settings.nacos_service_name,
            "instance_id": self.service_instance_id
        }
        
        if self.client and self.is_registered:
            try:
                # 检查服务状态
                ip = self._get_local_ip()
                instances = await self.get_service_instances(settings.nacos_service_name)
                current_instance = next(
                    (inst for inst in instances if inst['ip'] == ip and inst['port'] == settings.service_port),
                    None
                )
                status["instance_healthy"] = current_instance is not None if current_instance else False
                status["instance_weight"] = current_instance.get('weight', 0) if current_instance else 0
            except Exception as e:
                status["health_check_error"] = str(e)
        
        return status

# 全局Nacos服务实例
nacos_service = NacosService() 