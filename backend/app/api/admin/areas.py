"""
区域管理API
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import WorkArea, SysUser
from app.api.admin.auth import get_current_user
from app.middleware.tenant import get_tenant_context, TenantQueryFilter
from app.utils.response import success_response, error_response, ErrorCode
from app.utils.pagination import PaginationParams, paginate

router = APIRouter()


class AreaCreate(BaseModel):
    """创建区域请求"""
    site_id: uuid.UUID = Field(..., description="工地ID")
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=64)
    description: Optional[str] = None
    access_group_id: Optional[str] = None
    access_group_name: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None


class AreaUpdate(BaseModel):
    """更新区域请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    access_group_id: Optional[str] = None
    access_group_name: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    is_active: Optional[bool] = None


class AreaQuery(PaginationParams):
    """查询区域参数"""
    keyword: Optional[str] = None
    is_active: Optional[bool] = None
    building: Optional[str] = None


@router.get("")
async def list_areas(
    query: AreaQuery = Depends(),
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取区域列表"""
    ctx = get_tenant_context()
    
    stmt = select(WorkArea).order_by(WorkArea.name)
    stmt = TenantQueryFilter.apply(stmt, ctx)
    
    if query.keyword:
        stmt = stmt.where(WorkArea.name.ilike(f"%{query.keyword}%"))
    
    if query.is_active is not None:
        stmt = stmt.where(WorkArea.is_active == query.is_active)
    
    if query.building:
        stmt = stmt.where(WorkArea.building == query.building)
    
    result = await paginate(db, stmt, query)
    
    items = [
        {
            "area_id": str(area.area_id),
            "name": area.name,
            "code": area.code,
            "description": area.description,
            "access_group_id": area.access_group_id,
            "building": area.building,
            "floor": area.floor,
            "is_active": area.is_active
        }
        for area in result.items
    ]
    
    return success_response({
        "items": items,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size
    })


@router.get("/options")
async def get_area_options(
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取区域选项（用于下拉框）"""
    ctx = get_tenant_context()
    
    stmt = select(WorkArea).where(WorkArea.is_active == True).order_by(WorkArea.name)
    stmt = TenantQueryFilter.apply(stmt, ctx)
    
    result = await db.execute(stmt)
    areas = result.scalars().all()
    
    options = [
        {
            "id": str(area.area_id),
            "name": area.name,
            "area_id": str(area.area_id),
            "device_count": 0  # 暂时设为0，后续可以从关联表查询
        }
        for area in areas
    ]
    
    return success_response(options)


@router.post("")
async def create_area(
    request: AreaCreate,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建区域"""
    ctx = get_tenant_context()
    
    # 验证用户是否有权访问该工地
    if not ctx.is_sys_admin:
        if not ctx.accessible_sites or request.site_id not in ctx.accessible_sites:
            return error_response(
                code=ErrorCode.FORBIDDEN,
                message="无权在该工地创建区域"
            )
    
    # 使用请求中的 site_id
    site_id = request.site_id
    
    # 检查名称唯一性
    existing_name = await db.execute(
        select(WorkArea).where(
            WorkArea.site_id == site_id,
            WorkArea.name == request.name
        )
    )
    if existing_name.scalar_one_or_none():
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="该区域名称已存在"
        )
    
    # 检查编码唯一性
    existing_code = await db.execute(
        select(WorkArea).where(
            WorkArea.site_id == site_id,
            WorkArea.code == request.code
        )
    )
    if existing_code.scalar_one_or_none():
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="区域编码已存在"
        )
    
    area = WorkArea(
        site_id=site_id,
        name=request.name,
        code=request.code,
        description=request.description,
        access_group_id=request.access_group_id,
        access_group_name=request.access_group_name,
        building=request.building,
        floor=request.floor,
        is_active=True
    )
    db.add(area)
    await db.commit()
    
    return success_response({
        "area_id": str(area.area_id)
    }, message="区域创建成功")


@router.get("/{area_id}")
async def get_area(
    area_id: uuid.UUID,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取区域详情"""
    result = await db.execute(
        select(WorkArea).where(WorkArea.area_id == area_id)
    )
    area = result.scalar_one_or_none()
    
    if not area:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="区域不存在"
        )
    
    return success_response({
        "area_id": str(area.area_id),
        "name": area.name,
        "code": area.code,
        "description": area.description,
        "access_group_id": area.access_group_id,
        "access_group_name": area.access_group_name,
        "building": area.building,
        "floor": area.floor,
        "is_active": area.is_active,
        "created_at": area.created_at.isoformat()
    })


@router.patch("/{area_id}")
async def update_area(
    area_id: uuid.UUID,
    request: AreaUpdate,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新区域"""
    result = await db.execute(
        select(WorkArea).where(WorkArea.area_id == area_id)
    )
    area = result.scalar_one_or_none()
    
    if not area:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="区域不存在"
        )
    
    # 如果更新名称，检查名称唯一性
    if request.name is not None and request.name != area.name:
        existing_name = await db.execute(
            select(WorkArea).where(
                WorkArea.site_id == area.site_id,
                WorkArea.name == request.name,
                WorkArea.area_id != area_id
            )
        )
        if existing_name.scalar_one_or_none():
            return error_response(
                code=ErrorCode.VALIDATION_ERROR,
                message="该区域名称已存在"
            )
        area.name = request.name
    if request.description is not None:
        area.description = request.description
    if request.access_group_id is not None:
        area.access_group_id = request.access_group_id
    if request.access_group_name is not None:
        area.access_group_name = request.access_group_name
    if request.building is not None:
        area.building = request.building
    if request.floor is not None:
        area.floor = request.floor
    if request.is_active is not None:
        area.is_active = request.is_active
    
    await db.commit()
    
    return success_response({
        "area_id": str(area.area_id)
    }, message="区域更新成功")


@router.delete("/{area_id}")
async def delete_area(
    area_id: uuid.UUID,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除区域（软删除）"""
    result = await db.execute(
        select(WorkArea).where(WorkArea.area_id == area_id)
    )
    area = result.scalar_one_or_none()
    
    if not area:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="区域不存在"
        )
    
    area.is_active = False
    await db.commit()
    
    return success_response(message="区域删除成功")

