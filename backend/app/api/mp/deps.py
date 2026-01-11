"""
小程序API依赖
"""
import uuid

from fastapi import Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import Worker


async def get_current_worker(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Worker:
    """
    获取当前小程序用户（工人）
    
    从请求头中获取 mp_session_token，解析并返回工人对象
    """
    # 获取Token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未认证")
    
    token = auth_header.split(" ")[1]
    
    # 解析Token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="令牌无效")
    
    # 验证是小程序Token
    if payload.get("type") != "mp_session":
        raise HTTPException(status_code=401, detail="令牌类型错误")
    
    worker_id = payload.get("sub")
    if not worker_id:
        raise HTTPException(status_code=401, detail="令牌无效")
    
    # 获取工人
    result = await db.execute(
        select(Worker).where(Worker.worker_id == uuid.UUID(worker_id))
    )
    worker = result.scalar_one_or_none()
    
    if not worker:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    if not worker.is_bound:
        raise HTTPException(status_code=401, detail="用户未绑定")
    
    if worker.status != "ACTIVE":
        raise HTTPException(status_code=401, detail="用户已禁用")
    
    # 设置到请求上下文
    request.state.user = worker
    
    return worker

