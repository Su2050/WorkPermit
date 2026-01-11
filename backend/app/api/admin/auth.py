"""
认证API
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models import SysUser
from app.utils.response import success_response, error_response, ErrorCode

router = APIRouter()


# 依赖注入：获取当前用户
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> SysUser:
    """
    从请求中获取当前用户
    """
    from app.core.security import decode_access_token
    
    # 获取Token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未认证")
    
    token = auth_header.split(" ")[1]
    
    # 解析Token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="令牌无效")
    
    # 获取用户
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="令牌无效")
    
    result = await db.execute(
        select(SysUser).where(SysUser.user_id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="用户已禁用")
    
    # 设置到请求上下文
    request.state.user = user
    
    return user


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


@router.post("/login")
async def login(
    request: LoginRequest,
    req: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    返回JWT令牌
    """
    # 查询用户
    result = await db.execute(
        select(SysUser).where(SysUser.username == request.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return error_response(
            code=ErrorCode.USER_NOT_FOUND,
            message="用户不存在"
        )
    
    # 检查用户状态
    if not user.is_active:
        return error_response(
            code=ErrorCode.USER_LOCKED,
            message="用户已禁用"
        )
    
    if user.is_locked:
        return error_response(
            code=ErrorCode.USER_LOCKED,
            message="用户已锁定"
        )
    
    # 验证密码
    if not verify_password(request.password, user.password_hash):
        # 增加失败次数
        user.login_fail_count += 1
        if user.login_fail_count >= 5:
            user.is_locked = True
        await db.commit()
        
        return error_response(
            code=ErrorCode.PASSWORD_INCORRECT,
            message="密码错误"
        )
    
    # 重置失败次数
    user.login_fail_count = 0
    user.last_login_at = datetime.now()
    user.last_login_ip = req.client.host
    await db.commit()
    
    # 生成Token
    token = create_access_token(
        subject=user.user_id,
        extra_data={
            "role": user.role,
            "contractor_id": str(user.contractor_id) if user.contractor_id else None
        }
    )
    
    return success_response({
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": str(user.user_id),
            "username": user.username,
            "name": user.name,
            "role": user.role,
            "contractor_id": str(user.contractor_id) if user.contractor_id else None
        }
    })


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(request.old_password, current_user.password_hash):
        return error_response(
            code=ErrorCode.PASSWORD_INCORRECT,
            message="原密码错误"
        )
    
    # 更新密码
    current_user.password_hash = get_password_hash(request.new_password)
    await db.commit()
    
    return success_response(message="密码修改成功")


@router.get("/me")
async def get_current_user_info(
    current_user: SysUser = Depends(get_current_user)
):
    """获取当前用户信息"""
    return success_response({
        "user_id": str(current_user.user_id),
        "username": current_user.username,
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role,
        "contractor_id": str(current_user.contractor_id) if current_user.contractor_id else None
    })

