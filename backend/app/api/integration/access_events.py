"""
门禁事件回调API (P1-1: 去重)
"""
from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.config import settings
from app.models import AccessEvent, Worker, WorkArea
from app.utils.response import success_response, error_response, ErrorCode

router = APIRouter()


class AccessEventData(BaseModel):
    """门禁事件数据"""
    event_id: Optional[str] = None  # 门禁侧事件ID
    device_id: str
    device_name: Optional[str] = None
    worker_external_id: Optional[str] = None  # 工人ID（本系统）
    face_id: Optional[str] = None  # 人脸ID
    id_no: Optional[str] = None  # 身份证号
    area_id: Optional[str] = None
    event_time: datetime
    direction: Optional[str] = None  # IN/OUT
    result: str  # PASS/DENY
    reason_code: Optional[str] = None
    reason_message: Optional[str] = None
    face_photo_url: Optional[str] = None
    confidence: Optional[float] = None
    site_id: str


@router.post("/callback")
async def receive_access_event(
    event: AccessEventData,
    x_api_key: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    接收门禁事件回调 (P1-1: 去重)
    
    门禁系统推送进出事件到此接口
    """
    # 验证API Key
    if x_api_key != settings.ACCESS_CONTROL_API_KEY:
        return error_response(
            code=ErrorCode.AUTH_FAILED,
            message="API Key无效"
        )
    
    # 尝试匹配工人
    worker_id = None
    if event.worker_external_id:
        try:
            worker_id = uuid.UUID(event.worker_external_id)
        except ValueError:
            pass
    elif event.face_id:
        # 通过人脸ID匹配
        result = await db.execute(
            select(Worker).where(Worker.face_id == event.face_id)
        )
        worker = result.scalar_one_or_none()
        if worker:
            worker_id = worker.worker_id
    elif event.id_no:
        # 通过身份证号匹配
        result = await db.execute(
            select(Worker).where(Worker.id_no == event.id_no)
        )
        worker = result.scalar_one_or_none()
        if worker:
            worker_id = worker.worker_id
    
    # 尝试匹配区域
    area_id = None
    if event.area_id:
        try:
            area_id = uuid.UUID(event.area_id)
        except ValueError:
            pass
    
    # P1-1: 去重 - 创建事件记录
    try:
        access_event = AccessEvent(
            vendor_event_id=event.event_id,
            device_id=event.device_id,
            device_name=event.device_name,
            worker_id=worker_id,
            area_id=area_id,
            site_id=uuid.UUID(event.site_id),
            event_time=event.event_time,
            direction=event.direction,
            result=event.result,
            reason_code=event.reason_code,
            reason_message=event.reason_message,
            face_photo_url=event.face_photo_url,
            face_id=event.face_id,
            confidence=event.confidence
        )
        
        db.add(access_event)
        await db.commit()
        
        return success_response({
            "event_id": str(access_event.event_id),
            "status": "created"
        })
        
    except IntegrityError:
        # P1-1: 唯一约束冲突 = 重复事件，直接忽略
        await db.rollback()
        return success_response({
            "status": "duplicate",
            "message": "Event already processed"
        })


@router.post("/batch-callback")
async def receive_batch_events(
    events: list[AccessEventData],
    x_api_key: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    批量接收门禁事件
    """
    if x_api_key != settings.ACCESS_CONTROL_API_KEY:
        return error_response(
            code=ErrorCode.AUTH_FAILED,
            message="API Key无效"
        )
    
    created_count = 0
    duplicate_count = 0
    error_count = 0
    
    for event in events:
        try:
            # 尝试匹配工人
            worker_id = None
            if event.worker_external_id:
                try:
                    worker_id = uuid.UUID(event.worker_external_id)
                except ValueError:
                    pass
            
            # 尝试匹配区域
            area_id = None
            if event.area_id:
                try:
                    area_id = uuid.UUID(event.area_id)
                except ValueError:
                    pass
            
            access_event = AccessEvent(
                vendor_event_id=event.event_id,
                device_id=event.device_id,
                device_name=event.device_name,
                worker_id=worker_id,
                area_id=area_id,
                site_id=uuid.UUID(event.site_id),
                event_time=event.event_time,
                direction=event.direction,
                result=event.result,
                reason_code=event.reason_code,
                reason_message=event.reason_message,
                face_photo_url=event.face_photo_url,
                face_id=event.face_id,
                confidence=event.confidence
            )
            
            db.add(access_event)
            await db.flush()
            created_count += 1
            
        except IntegrityError:
            await db.rollback()
            duplicate_count += 1
        except Exception:
            error_count += 1
    
    await db.commit()
    
    return success_response({
        "created": created_count,
        "duplicates": duplicate_count,
        "errors": error_count
    })

