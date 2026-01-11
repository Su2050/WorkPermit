"""
小程序认证API
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_mp_session_token
from app.models import Worker
from app.adapters.wechat_adapter import WechatAdapter
from app.adapters.realname_adapter import RealnameAdapter
from app.utils.response import success_response, error_response, ErrorCode

router = APIRouter()


class WechatLoginRequest(BaseModel):
    """微信登录请求"""
    code: str


class BindRequest(BaseModel):
    """绑定请求"""
    openid: str
    id_no: str
    name: str
    phone: str
    phone_code: Optional[str] = None  # 微信获取手机号的code


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str


@router.post("/wechat-login")
async def wechat_login(
    request: WechatLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    微信登录
    
    步骤：
    1. code换取openid/unionid
    2. 查询是否已绑定工人
    3. 返回绑定状态和session_token
    """
    adapter = WechatAdapter()
    
    # 1. code换session
    result = await adapter.code2session(request.code)
    
    if not result.get("success"):
        return error_response(
            code=ErrorCode.WECHAT_AUTH_FAILED,
            message=result.get("error", "微信认证失败")
        )
    
    openid = result.get("openid")
    unionid = result.get("unionid")
    
    # 2. 查询是否已绑定
    stmt = select(Worker).where(Worker.wechat_openid == openid)
    if unionid:
        stmt = stmt.union(select(Worker).where(Worker.wechat_unionid == unionid))
    
    worker_result = await db.execute(stmt)
    worker = worker_result.scalar_one_or_none()
    
    if worker:
        # 已绑定，生成session_token
        token = create_mp_session_token(openid, worker.worker_id)
        return success_response({
            "is_bound": True,
            "session_token": token,
            "worker": {
                "worker_id": str(worker.worker_id),
                "name": worker.name,
                "phone": worker.phone[-4:] if worker.phone else None
            }
        })
    else:
        # 未绑定，返回openid供后续绑定使用
        return success_response({
            "is_bound": False,
            "openid": openid,
            "unionid": unionid
        })


@router.post("/bind")
async def bind_worker(
    request: BindRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    绑定工人身份
    
    步骤：
    1. 验证身份证号/姓名在实名制系统中存在
    2. 检查是否已被其他微信绑定
    3. 更新工人的微信绑定信息
    4. 返回session_token
    """
    # 1. 从实名制系统验证身份
    realname_adapter = RealnameAdapter()
    realname_worker = await realname_adapter.match_worker(
        id_no=request.id_no,
        name=request.name,
        phone=request.phone
    )
    
    if not realname_worker:
        return error_response(
            code=ErrorCode.WORKER_NOT_FOUND_IN_REALNAME,
            message="未在实名制系统中找到该人员，请确认身份信息"
        )
    
    # 2. 查找本地工人记录
    worker_result = await db.execute(
        select(Worker).where(Worker.id_no == request.id_no)
    )
    worker = worker_result.scalar_one_or_none()
    
    if not worker:
        return error_response(
            code=ErrorCode.WORKER_NOT_FOUND_IN_REALNAME,
            message="人员未同步到系统，请联系管理员"
        )
    
    # 3. 检查是否已绑定其他微信
    if worker.is_bound and worker.wechat_openid != request.openid:
        return error_response(
            code=ErrorCode.WORKER_ALREADY_BOUND,
            message="该身份已绑定其他微信账号"
        )
    
    # 4. 更新绑定信息
    worker.wechat_openid = request.openid
    worker.is_bound = True
    
    await db.commit()
    
    # 5. 生成session_token
    token = create_mp_session_token(request.openid, worker.worker_id)
    
    return success_response({
        "session_token": token,
        "worker": {
            "worker_id": str(worker.worker_id),
            "name": worker.name,
            "phone": worker.phone[-4:] if worker.phone else None
        }
    }, message="绑定成功")


@router.post("/refresh-token")
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """刷新session_token"""
    from app.core.security import decode_access_token
    
    # 解析旧token
    payload = decode_access_token(request.refresh_token)
    if not payload:
        return error_response(
            code=ErrorCode.TOKEN_INVALID,
            message="Token无效"
        )
    
    worker_id = payload.get("sub")
    openid = payload.get("openid")
    
    if not worker_id or not openid:
        return error_response(
            code=ErrorCode.TOKEN_INVALID,
            message="Token无效"
        )
    
    # 验证工人存在
    result = await db.execute(
        select(Worker).where(Worker.worker_id == uuid.UUID(worker_id))
    )
    worker = result.scalar_one_or_none()
    
    if not worker:
        return error_response(
            code=ErrorCode.USER_NOT_FOUND,
            message="用户不存在"
        )
    
    # 生成新token
    new_token = create_mp_session_token(openid, worker.worker_id)
    
    return success_response({
        "session_token": new_token
    })

