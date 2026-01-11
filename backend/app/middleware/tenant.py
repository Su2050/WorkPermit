"""
多租户隔离中间件 (P0-7)
- 租户 = 工地项目（site）
- 所有业务表带 site_id
- 自动注入 site_id 过滤
"""
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Any
from contextvars import ContextVar
import logging

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import Select

logger = logging.getLogger(__name__)

# 租户上下文变量（线程/协程安全）
_tenant_context: ContextVar[Optional["TenantContext"]] = ContextVar(
    "tenant_context", 
    default=None
)


@dataclass
class TenantContext:
    """
    租户上下文（请求级别）
    
    P0-7: 多租户隔离
    - SysAdmin 可访问所有 site
    - ContractorAdmin 可访问其绑定的 site
    - Worker 只能访问其所在 site
    """
    user_id: Optional[uuid.UUID] = None
    user_role: Optional[str] = None  # SysAdmin / ContractorAdmin / Worker
    site_id: Optional[uuid.UUID] = None  # 当前操作的site（如果明确指定）
    contractor_id: Optional[uuid.UUID] = None
    accessible_sites: List[uuid.UUID] = field(default_factory=list)
    
    def can_access_site(self, site_id: uuid.UUID) -> bool:
        """检查是否可以访问指定site"""
        if self.user_role == "SysAdmin":
            return True
        return site_id in self.accessible_sites
    
    def get_site_filter(self) -> List[uuid.UUID]:
        """获取site过滤列表"""
        if self.user_role == "SysAdmin":
            return []  # 空列表表示不过滤
        return self.accessible_sites
    
    @property
    def is_sys_admin(self) -> bool:
        return self.user_role == "SysAdmin"
    
    @property
    def is_contractor_admin(self) -> bool:
        return self.user_role == "ContractorAdmin"
    
    @property
    def is_worker(self) -> bool:
        return self.user_role == "Worker"


def get_tenant_context() -> Optional[TenantContext]:
    """获取当前请求的租户上下文"""
    return _tenant_context.get()


def set_tenant_context(ctx: TenantContext) -> None:
    """设置当前请求的租户上下文"""
    _tenant_context.set(ctx)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    多租户隔离中间件
    
    从JWT中解析用户信息，构建租户上下文
    """
    
    # 不需要租户过滤的路径
    EXCLUDED_PATHS = [
        "/api/health",
        "/api/docs",
        "/api/openapi.json",
        "/api/auth/login",
        "/api/mp/bind",
    ]
    
    async def dispatch(self, request: Request, call_next):
        # 跳过不需要过滤的路径
        if any(request.url.path.startswith(p) for p in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # 尝试从JWT中解析用户信息
        user_info = await self._get_user_from_token(request)
        
        if user_info:
            ctx = await self._build_tenant_context_from_info(user_info, request)
            set_tenant_context(ctx)
            logger.debug(
                f"Tenant context set: user={ctx.user_id}, "
                f"role={ctx.user_role}, sites={ctx.accessible_sites}"
            )
        else:
            # 未认证请求，设置空上下文（依赖注入会处理认证）
            set_tenant_context(TenantContext())
        
        try:
            response = await call_next(request)
            return response
        finally:
            # 清理上下文
            _tenant_context.set(None)
    
    async def _get_user_from_token(self, request: Request) -> Optional[dict]:
        """从JWT Token中解析用户信息"""
        from app.core.security import decode_access_token
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)
        
        if not payload:
            return None
        
        return {
            "user_id": payload.get("sub"),
            "role": payload.get("role"),
            "contractor_id": payload.get("contractor_id")
        }
    
    async def _build_tenant_context(
        self, 
        user: Any, 
        request: Request
    ) -> TenantContext:
        """构建租户上下文（从用户对象）"""
        ctx = TenantContext(
            user_id=user.user_id if hasattr(user, 'user_id') else user.worker_id,
            user_role=user.role if hasattr(user, 'role') else "Worker",
        )
        
        if ctx.user_role == "SysAdmin":
            # 系统管理员可访问所有 site
            ctx.accessible_sites = await self._get_all_site_ids(request)
        elif ctx.user_role == "ContractorAdmin":
            # 施工单位管理员可访问其绑定的 site
            ctx.contractor_id = user.contractor_id if hasattr(user, 'contractor_id') else None
            if ctx.contractor_id:
                ctx.accessible_sites = await self._get_contractor_sites(
                    request, ctx.contractor_id
                )
        elif ctx.user_role == "Worker":
            # 作业人员只能访问其所在 site
            ctx.site_id = user.site_id if hasattr(user, 'site_id') else None
            ctx.accessible_sites = [ctx.site_id] if ctx.site_id else []
        
        return ctx
    
    async def _build_tenant_context_from_info(
        self, 
        user_info: dict, 
        request: Request
    ) -> TenantContext:
        """构建租户上下文（从用户信息字典）"""
        import uuid
        
        ctx = TenantContext(
            user_id=uuid.UUID(user_info["user_id"]) if user_info.get("user_id") else None,
            user_role=user_info.get("role"),
        )
        
        if ctx.user_role == "SysAdmin":
            # 系统管理员可访问所有 site（不过滤）
            ctx.accessible_sites = []
        elif ctx.user_role == "ContractorAdmin":
            # 施工单位管理员可访问其绑定的 site
            contractor_id = uuid.UUID(user_info["contractor_id"]) if user_info.get("contractor_id") else None
            ctx.contractor_id = contractor_id
            if contractor_id:
                ctx.accessible_sites = await self._get_contractor_sites(
                    request, contractor_id
                )
        
        return ctx
    
    async def _get_all_site_ids(self, request: Request) -> List[uuid.UUID]:
        """获取所有site ID（用于SysAdmin）"""
        # 这里需要从数据库获取，但为了避免循环依赖，
        # 实际实现中应该通过依赖注入或缓存获取
        # 暂时返回空列表，表示不过滤
        return []
    
    async def _get_contractor_sites(
        self, 
        request: Request, 
        contractor_id: uuid.UUID
    ) -> List[uuid.UUID]:
        """获取施工单位绑定的site ID"""
        # 同上，实际实现需要从数据库获取
        # 这里返回空列表作为占位
        return []


# 创建中间件实例
tenant_middleware = TenantMiddleware


class TenantQueryFilter:
    """
    租户查询过滤器
    
    自动为查询注入 site_id 过滤条件
    """
    
    @staticmethod
    def apply(query: Select, tenant_ctx: Optional[TenantContext] = None) -> Select:
        """
        自动注入 site_id 过滤
        
        Args:
            query: SQLAlchemy查询
            tenant_ctx: 租户上下文（默认从ContextVar获取）
        
        Returns:
            添加了过滤条件的查询
        """
        if tenant_ctx is None:
            tenant_ctx = get_tenant_context()
        
        if tenant_ctx is None:
            logger.warning("No tenant context found, skipping filter")
            return query
        
        # SysAdmin 不过滤
        if tenant_ctx.is_sys_admin:
            return query
        
        # 获取可访问的site列表
        accessible_sites = tenant_ctx.get_site_filter()
        
        if not accessible_sites:
            logger.warning(
                f"No accessible sites for user {tenant_ctx.user_id}, "
                "query may return empty results"
            )
            return query
        
        # 尝试获取查询的主实体
        try:
            # 获取查询中的第一个实体
            entity = query.column_descriptions[0]['entity']
            
            # 检查实体是否有 site_id 字段
            if hasattr(entity, 'site_id'):
                return query.where(entity.site_id.in_(accessible_sites))
            else:
                logger.debug(
                    f"Entity {entity.__name__} has no site_id field, "
                    "skipping tenant filter"
                )
                return query
        except (IndexError, KeyError, AttributeError) as e:
            logger.warning(f"Failed to apply tenant filter: {e}")
            return query
    
    @staticmethod
    def check_access(site_id: uuid.UUID) -> bool:
        """
        检查当前用户是否可以访问指定site
        
        Args:
            site_id: 要检查的site ID
        
        Returns:
            bool: 是否有权限
        
        Raises:
            HTTPException: 如果没有权限
        """
        ctx = get_tenant_context()
        
        if ctx is None:
            raise HTTPException(status_code=401, detail="未认证")
        
        if not ctx.can_access_site(site_id):
            raise HTTPException(status_code=403, detail="无权访问该工地")
        
        return True


# 依赖注入函数
async def require_site_access(site_id: uuid.UUID) -> TenantContext:
    """
    FastAPI依赖：要求有指定site的访问权限
    
    Usage:
        @app.get("/sites/{site_id}/tickets")
        async def get_tickets(
            site_id: uuid.UUID,
            ctx: TenantContext = Depends(require_site_access)
        ):
            ...
    """
    ctx = get_tenant_context()
    
    if ctx is None:
        raise HTTPException(status_code=401, detail="未认证")
    
    if not ctx.can_access_site(site_id):
        raise HTTPException(status_code=403, detail="无权访问该工地")
    
    return ctx


async def require_sys_admin() -> TenantContext:
    """
    FastAPI依赖：要求系统管理员权限
    """
    ctx = get_tenant_context()
    
    if ctx is None:
        raise HTTPException(status_code=401, detail="未认证")
    
    if not ctx.is_sys_admin:
        raise HTTPException(status_code=403, detail="需要系统管理员权限")
    
    return ctx


async def require_contractor_admin() -> TenantContext:
    """
    FastAPI依赖：要求施工单位管理员或更高权限
    """
    ctx = get_tenant_context()
    
    if ctx is None:
        raise HTTPException(status_code=401, detail="未认证")
    
    if not (ctx.is_sys_admin or ctx.is_contractor_admin):
        raise HTTPException(status_code=403, detail="需要施工单位管理员权限")
    
    return ctx

