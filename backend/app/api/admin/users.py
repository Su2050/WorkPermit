"""
用户管理API
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import SysUser, Contractor
from app.api.admin.auth import get_current_user
from app.middleware.tenant import require_sys_admin, get_tenant_context, TenantQueryFilter
from app.utils.response import success_response, error_response, ErrorCode
from app.utils.pagination import PaginationParams, paginate

router = APIRouter()


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(..., max_length=64)
    password: str = Field(..., min_length=6, max_length=72)
    name: str = Field(..., max_length=64)
    email: Optional[str] = Field(None, max_length=128)
    phone: Optional[str] = Field(None, max_length=32)
    role: str = Field(..., pattern="^(SysAdmin|ContractorAdmin)$")
    contractor_id: Optional[uuid.UUID] = None
    is_active: bool = True


class UserUpdate(BaseModel):
    """更新用户请求"""
    name: Optional[str] = Field(None, max_length=64)
    email: Optional[str] = Field(None, max_length=128)
    phone: Optional[str] = Field(None, max_length=32)
    role: Optional[str] = Field(None, pattern="^(SysAdmin|ContractorAdmin)$")
    contractor_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class UserQuery(PaginationParams):
    """查询用户参数"""
    keyword: Optional[str] = None
    role: Optional[str] = None
    contractor_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_users(
    query: UserQuery = Depends(),
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表"""
    ctx = get_tenant_context()
    
    stmt = select(SysUser).order_by(SysUser.created_at.desc())
    
    # 多租户过滤
    stmt = TenantQueryFilter.apply(stmt, ctx)
    
    if query.keyword:
        stmt = stmt.where(
            (SysUser.username.ilike(f"%{query.keyword}%")) |
            (SysUser.name.ilike(f"%{query.keyword}%"))
        )
    
    if query.role:
        stmt = stmt.where(SysUser.role == query.role)
    
    if query.contractor_id:
        stmt = stmt.where(SysUser.contractor_id == query.contractor_id)
    
    if query.is_active is not None:
        stmt = stmt.where(SysUser.is_active == query.is_active)
    
    result = await paginate(db, stmt, query)
    
    # 加载关联数据
    items = []
    for user in result.items:
        contractor_name = None
        if user.contractor_id:
            contractor_result = await db.execute(
                select(Contractor).where(Contractor.contractor_id == user.contractor_id)
            )
            contractor = contractor_result.scalar_one_or_none()
            contractor_name = contractor.name if contractor else None
        
        items.append({
            "user_id": str(user.user_id),
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "contractor_id": str(user.contractor_id) if user.contractor_id else None,
            "contractor_name": contractor_name,
            "is_active": user.is_active,
            "is_locked": user.is_locked,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat()
        })
    
    return success_response({
        "items": items,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size
    })


@router.post("")
async def create_user(
    request: UserCreate,
    current_user: SysUser = Depends(require_sys_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建用户（仅系统管理员）"""
    # 检查用户名唯一性
    existing = await db.execute(
        select(SysUser).where(SysUser.username == request.username)
    )
    if existing.scalar_one_or_none():
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="用户名已存在"
        )
    
    # 验证角色和施工单位关联
    if request.role == "ContractorAdmin":
        if not request.contractor_id:
            return error_response(
                code=ErrorCode.VALIDATION_ERROR,
                message="施工单位管理员必须关联施工单位"
            )
        # 验证施工单位存在
        contractor_result = await db.execute(
            select(Contractor).where(Contractor.contractor_id == request.contractor_id)
        )
        if not contractor_result.scalar_one_or_none():
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="施工单位不存在"
            )
    elif request.role == "SysAdmin":
        # 系统管理员不能关联施工单位
        request.contractor_id = None
    
    # 创建用户
    user = SysUser(
        username=request.username,
        password_hash=get_password_hash(request.password),
        name=request.name,
        email=request.email,
        phone=request.phone,
        role=request.role,
        contractor_id=request.contractor_id,
        is_active=request.is_active
    )
    db.add(user)
    await db.commit()
    
    return success_response({
        "user_id": str(user.user_id),
        "username": user.username
    }, message="用户创建成功")


@router.get("/{user_id}")
async def get_user(
    user_id: uuid.UUID,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户详情"""
    result = await db.execute(
        select(SysUser).where(SysUser.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="用户不存在"
        )
    
    contractor_name = None
    if user.contractor_id:
        contractor_result = await db.execute(
            select(Contractor).where(Contractor.contractor_id == user.contractor_id)
        )
        contractor = contractor_result.scalar_one_or_none()
        contractor_name = contractor.name if contractor else None
    
    return success_response({
        "user_id": str(user.user_id),
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "contractor_id": str(user.contractor_id) if user.contractor_id else None,
        "contractor_name": contractor_name,
        "is_active": user.is_active,
        "is_locked": user.is_locked,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat()
    })


@router.patch("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    request: UserUpdate,
    current_user: SysUser = Depends(require_sys_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新用户（仅系统管理员）"""
    result = await db.execute(
        select(SysUser).where(SysUser.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="用户不存在"
        )
    
    # 更新字段
    if request.name is not None:
        user.name = request.name
    if request.email is not None:
        user.email = request.email
    if request.phone is not None:
        user.phone = request.phone
    if request.role is not None:
        # 验证角色和施工单位关联
        if request.role == "ContractorAdmin":
            contractor_id = request.contractor_id if request.contractor_id is not None else user.contractor_id
            if not contractor_id:
                return error_response(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="施工单位管理员必须关联施工单位"
                )
            # 验证施工单位存在
            contractor_result = await db.execute(
                select(Contractor).where(Contractor.contractor_id == contractor_id)
            )
            if not contractor_result.scalar_one_or_none():
                return error_response(
                    code=ErrorCode.NOT_FOUND,
                    message="施工单位不存在"
                )
            user.contractor_id = contractor_id
        elif request.role == "SysAdmin":
            user.contractor_id = None
        user.role = request.role
    
    if request.contractor_id is not None:
        if request.contractor_id:
            # 验证施工单位存在
            contractor_result = await db.execute(
                select(Contractor).where(Contractor.contractor_id == request.contractor_id)
            )
            if not contractor_result.scalar_one_or_none():
                return error_response(
                    code=ErrorCode.NOT_FOUND,
                    message="施工单位不存在"
                )
        user.contractor_id = request.contractor_id
    
    if request.is_active is not None:
        user.is_active = request.is_active
    
    await db.commit()
    
    return success_response({
        "user_id": str(user.user_id)
    }, message="用户更新成功")


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    new_password: str = Field(..., min_length=6, max_length=72)


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: uuid.UUID,
    request: ResetPasswordRequest,
    current_user: SysUser = Depends(require_sys_admin),
    db: AsyncSession = Depends(get_db)
):
    """重置用户密码（仅系统管理员）"""
    result = await db.execute(
        select(SysUser).where(SysUser.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="用户不存在"
        )
    
    user.password_hash = get_password_hash(request.new_password)
    user.login_fail_count = 0
    user.is_locked = False
    await db.commit()
    
    return success_response(message="密码重置成功")


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: SysUser = Depends(require_sys_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除用户（仅系统管理员）"""
    # 不允许删除自己
    if user_id == current_user.user_id:
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="不能删除自己的账号"
        )
    
    result = await db.execute(
        select(SysUser).where(SysUser.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="用户不存在"
        )
    
    # 不允许删除其他系统管理员
    if user.role == "SysAdmin" and user.user_id != current_user.user_id:
        return error_response(
            code=ErrorCode.FORBIDDEN,
            message="不能删除其他系统管理员"
        )
    
    await db.delete(user)
    await db.commit()
    
    return success_response(message="用户删除成功")

