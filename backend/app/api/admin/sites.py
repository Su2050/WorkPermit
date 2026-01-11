"""
工地管理API
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Site, SysUser
from app.api.admin.auth import get_current_user
from app.middleware.tenant import require_sys_admin
from app.utils.response import success_response, error_response, ErrorCode
from app.utils.pagination import PaginationParams, paginate

router = APIRouter()


class SiteCreate(BaseModel):
    """创建工地请求"""
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=64)
    address: Optional[str] = None
    description: Optional[str] = None
    default_access_start_time: str = "06:00:00"
    default_access_end_time: str = "20:00:00"
    default_training_deadline: str = "07:30:00"


class SiteUpdate(BaseModel):
    """更新工地请求"""
    name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    default_access_start_time: Optional[str] = None
    default_access_end_time: Optional[str] = None
    default_training_deadline: Optional[str] = None
    is_active: Optional[bool] = None


class SiteQuery(PaginationParams):
    """查询工地参数"""
    keyword: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/options")
async def get_site_options(
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取工地选项（用于下拉框）"""
    stmt = select(Site).where(Site.is_active == True).order_by(Site.name)
    
    result = await db.execute(stmt)
    sites = result.scalars().all()
    
    options = [
        {
            "id": str(site.site_id),
            "name": site.name,
            "site_id": str(site.site_id),
            "code": site.code
        }
        for site in sites
    ]
    
    return success_response(options)


@router.get("")
async def list_sites(
    query: SiteQuery = Depends(),
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取工地列表"""
    stmt = select(Site).order_by(Site.name)
    
    if query.keyword:
        stmt = stmt.where(Site.name.ilike(f"%{query.keyword}%"))
    
    if query.is_active is not None:
        stmt = stmt.where(Site.is_active == query.is_active)
    
    result = await paginate(db, stmt, query)
    
    items = [
        {
            "site_id": str(site.site_id),
            "name": site.name,
            "code": site.code,
            "address": site.address,
            "is_active": site.is_active
        }
        for site in result.items
    ]
    
    return success_response({
        "items": items,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size
    })


@router.post("")
async def create_site(
    request: SiteCreate,
    current_user: SysUser = Depends(require_sys_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建工地（仅系统管理员）"""
    # 检查名称唯一性
    existing_name = await db.execute(
        select(Site).where(Site.name == request.name)
    )
    if existing_name.scalar_one_or_none():
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="该工地名称已存在"
        )
    
    # 检查编码唯一性
    existing_code = await db.execute(
        select(Site).where(Site.code == request.code)
    )
    if existing_code.scalar_one_or_none():
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="工地编码已存在"
        )
    
    site = Site(
        name=request.name,
        code=request.code,
        address=request.address,
        description=request.description,
        default_access_start_time=request.default_access_start_time,
        default_access_end_time=request.default_access_end_time,
        default_training_deadline=request.default_training_deadline,
        is_active=True
    )
    db.add(site)
    await db.commit()
    
    return success_response({
        "site_id": str(site.site_id)
    }, message="工地创建成功")


@router.get("/{site_id}")
async def get_site(
    site_id: uuid.UUID,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取工地详情"""
    result = await db.execute(
        select(Site).where(Site.site_id == site_id)
    )
    site = result.scalar_one_or_none()
    
    if not site:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="工地不存在"
        )
    
    return success_response({
        "site_id": str(site.site_id),
        "name": site.name,
        "code": site.code,
        "address": site.address,
        "description": site.description,
        "default_access_start_time": site.default_access_start_time,
        "default_access_end_time": site.default_access_end_time,
        "default_training_deadline": site.default_training_deadline,
        "is_active": site.is_active,
        "created_at": site.created_at.isoformat()
    })


@router.patch("/{site_id}")
async def update_site(
    site_id: uuid.UUID,
    request: SiteUpdate,
    current_user: SysUser = Depends(require_sys_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新工地（仅系统管理员）"""
    result = await db.execute(
        select(Site).where(Site.site_id == site_id)
    )
    site = result.scalar_one_or_none()
    
    if not site:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="工地不存在"
        )
    
    # 如果更新名称，检查名称唯一性
    if request.name is not None and request.name != site.name:
        existing_name = await db.execute(
            select(Site).where(
                Site.name == request.name,
                Site.site_id != site_id
            )
        )
        if existing_name.scalar_one_or_none():
            return error_response(
                code=ErrorCode.VALIDATION_ERROR,
                message="该工地名称已存在"
            )
        site.name = request.name
    if request.address is not None:
        site.address = request.address
    if request.description is not None:
        site.description = request.description
    if request.default_access_start_time is not None:
        site.default_access_start_time = request.default_access_start_time
    if request.default_access_end_time is not None:
        site.default_access_end_time = request.default_access_end_time
    if request.default_training_deadline is not None:
        site.default_training_deadline = request.default_training_deadline
    if request.is_active is not None:
        site.is_active = request.is_active
    
    await db.commit()
    
    return success_response({
        "site_id": str(site.site_id)
    }, message="工地更新成功")

