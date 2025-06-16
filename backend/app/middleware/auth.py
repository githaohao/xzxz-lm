from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Optional, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)

class UserAuthMiddleware(BaseHTTPMiddleware):
    """用户认证中间件 - 从若依Gateway请求头中提取用户信息"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security = HTTPBearer(auto_error=False)
        # 不需要认证的路径
        self.excluded_paths = {
            "/", "/health", "/docs", "/redoc", "/openapi.json",
            "/favicon.ico"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """中间件处理逻辑"""
        # 对于特定路径，跳过认证
        if (request.url.path in self.excluded_paths or 
            request.url.path.startswith("/uploads") or
            request.url.path.startswith("/static")):
            return await call_next(request)
        
        try:
            # 提取用户信息并添加到请求状态中
            user_info = await self._get_user_info(request)
            request.state.user = user_info
            
            logger.debug(f"用户认证成功: {user_info['username']} (ID: {user_info['user_id']})")
            
        except HTTPException as e:
            logger.warning(f"用户认证失败: {e.detail}")
            # 对于认证失败，直接抛出异常，不再设置默认用户
            raise e
            
        except Exception as e:
            logger.error(f"中间件处理异常: {e}")
            # 抛出认证失败异常
            raise HTTPException(status_code=401, detail="用户认证失败")
        
        return await call_next(request)
    
    async def _get_user_info(self, request: Request) -> Dict[str, Any]:
        """从请求头中获取当前用户信息（内部方法）"""
        try:
            # 从若依Gateway传递的请求头中获取用户信息
            user_id = request.headers.get("X-User-Id") or request.headers.get("userid")
            username = request.headers.get("X-Username") or request.headers.get("username")
            nickname = request.headers.get("X-Nickname") or request.headers.get("nickname") 
            email = request.headers.get("X-Email") or request.headers.get("email")
            avatar = request.headers.get("X-Avatar") or request.headers.get("avatar")
            
            if not user_id:
                logger.warning("请求头中缺少用户ID，认证失败")
                raise HTTPException(status_code=401, detail="用户未登录或登录已过期")
            
            try:
                user_id = int(user_id)
            except ValueError:
                logger.error(f"无效的用户ID格式: {user_id}")
                raise HTTPException(status_code=401, detail="用户ID格式无效")
            
            # 构建用户信息（仅用于请求处理，不存储到数据库）
            user_info = {
                "user_id": user_id,
                "username": username or f"user_{user_id}",
                "nickname": nickname or username or f"用户{user_id}",
                "email": email or "",
                "avatar": avatar or ""
            }
            
            return user_info
            
        except Exception as e:
            logger.error(f"用户信息提取失败: {e}")
            raise HTTPException(status_code=401, detail="用户认证失败")

# 依赖注入函数
async def get_current_user(request: Request) -> Dict[str, Any]:
    """获取当前用户的依赖注入函数"""
    # 从中间件设置的请求状态中获取用户信息
    if hasattr(request.state, 'user'):
        return request.state.user
    
    # 如果没有用户信息，抛出认证失败异常
    raise HTTPException(status_code=401, detail="用户未登录或登录已过期")

async def get_current_user_id(request: Request) -> int:
    """获取当前用户ID的依赖注入函数"""
    user_info = await get_current_user(request)
    return user_info["user_id"] 