"""
小程序培训API (P0-2: 防作弊)
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import generate_session_token
from app.models import (
    DailyTicket, DailyTicketWorker, TrainingSession, 
    TrainingVideo, Worker
)
from app.api.mp.deps import get_current_worker
from app.adapters.face_verify_adapter import FaceVerifyAdapter
from app.utils.response import success_response, error_response, ErrorCode
from app.utils.progress_validator import (
    TrainingProgressValidator, RandomCheckScheduler, ProgressData
)

router = APIRouter()


class StartSessionRequest(BaseModel):
    """开始学习会话请求"""
    daily_ticket_id: uuid.UUID
    video_id: uuid.UUID
    face_photo: Optional[str] = None  # Base64编码的人脸照片


class ProgressRequest(BaseModel):
    """进度上报请求"""
    session_token: str
    position: int  # 当前播放位置(秒)
    played_seconds_delta: int  # 本次心跳新增播放秒数
    video_state: str = "playing"  # playing/paused/background
    client_ts: int  # 客户端时间戳


class FaceVerifyRequest(BaseModel):
    """人脸验证请求"""
    session_id: uuid.UUID
    action_type: str  # blink/nod/shake/mouth
    photo: str  # Base64编码的照片


class CompleteSessionRequest(BaseModel):
    """完成学习会话请求"""
    session_token: str


@router.post("/sessions/start")
async def start_session(
    request: StartSessionRequest,
    current_worker: Worker = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db)
):
    """
    开始学习会话
    
    1. 验证人脸（可选）
    2. 创建学习会话
    3. 返回session_token
    """
    # 验证日票存在且有效
    dt_result = await db.execute(
        select(DailyTicket).where(
            DailyTicket.daily_ticket_id == request.daily_ticket_id
        )
    )
    daily_ticket = dt_result.scalar_one_or_none()
    
    if not daily_ticket:
        return error_response(
            code=ErrorCode.TICKET_NOT_FOUND,
            message="任务不存在"
        )
    
    if daily_ticket.status not in ["PUBLISHED", "IN_PROGRESS"]:
        return error_response(
            code=ErrorCode.TICKET_EXPIRED,
            message="任务已过期或取消"
        )
    
    # 验证工人在名单中
    dtw_result = await db.execute(
        select(DailyTicketWorker).where(
            DailyTicketWorker.daily_ticket_id == request.daily_ticket_id,
            DailyTicketWorker.worker_id == current_worker.worker_id
        )
    )
    dtw = dtw_result.scalar_one_or_none()
    
    if not dtw:
        return error_response(
            code=ErrorCode.WORKER_NOT_IN_TICKET,
            message="您不在此作业票名单中"
        )
    
    # 验证视频存在
    video_result = await db.execute(
        select(TrainingVideo).where(
            TrainingVideo.video_id == request.video_id
        )
    )
    video = video_result.scalar_one_or_none()
    
    if not video:
        return error_response(
            code=ErrorCode.VIDEO_NOT_IN_TICKET,
            message="视频不存在"
        )
    
    # 检查是否已有会话
    existing_result = await db.execute(
        select(TrainingSession).where(
            TrainingSession.daily_ticket_id == request.daily_ticket_id,
            TrainingSession.worker_id == current_worker.worker_id,
            TrainingSession.video_id == request.video_id
        )
    )
    existing_session = existing_result.scalar_one_or_none()
    
    if existing_session:
        if existing_session.status == "COMPLETED":
            return error_response(
                code=ErrorCode.TRAINING_ALREADY_COMPLETED,
                message="该视频已学习完成"
            )
        elif existing_session.status == "FAILED":
            return error_response(
                code=ErrorCode.TRAINING_FAILED,
                message="该视频学习失败，请联系管理员"
            )
        else:
            # 返回已有会话
            return success_response({
                "session_id": str(existing_session.session_id),
                "session_token": existing_session.session_token,
                "status": existing_session.status,
                "video": {
                    "video_id": str(video.video_id),
                    "title": video.title,
                    "duration": video.duration_sec,
                    "file_url": video.file_url
                },
                "progress": {
                    "valid_watch_sec": existing_session.valid_watch_sec,
                    "last_position": existing_session.last_position
                }
            })
    
    # 人脸验证（如果提供了照片）
    if request.face_photo:
        face_adapter = FaceVerifyAdapter()
        verify_result = await face_adapter.verify_face(
            photo_base64=request.face_photo,
            id_no=current_worker.id_no,
            worker_id=current_worker.worker_id
        )
        
        if not verify_result.get("passed"):
            return error_response(
                code=ErrorCode.FACE_VERIFY_FAILED,
                message="人脸验证失败，请确保本人操作"
            )
    
    # 创建学习会话
    session_token = generate_session_token()
    
    session = TrainingSession(
        daily_ticket_id=request.daily_ticket_id,
        worker_id=current_worker.worker_id,
        video_id=request.video_id,
        site_id=current_worker.site_id,
        status="IN_LEARNING",
        session_token=session_token,
        started_at=datetime.now()
    )
    db.add(session)
    
    # 更新日票工人状态
    if dtw.training_status == "NOT_STARTED":
        dtw.training_status = "IN_LEARNING"
    
    await db.commit()
    
    return success_response({
        "session_id": str(session.session_id),
        "session_token": session_token,
        "status": session.status,
        "video": {
            "video_id": str(video.video_id),
            "title": video.title,
            "duration": video.duration_sec,
            "file_url": video.file_url
        },
        "progress": {
            "valid_watch_sec": 0,
            "last_position": 0
        }
    })


@router.post("/sessions/{session_id}/progress")
async def report_progress(
    session_id: uuid.UUID,
    request: ProgressRequest,
    current_worker: Worker = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db)
):
    """
    上报学习进度 (P0-2: 防作弊)
    
    验证规则:
    1. 检查时间倒退
    2. 检查跳跃幅度
    3. 检查播放速度异常
    4. 累积可疑事件
    """
    # 获取会话
    result = await db.execute(
        select(TrainingSession)
        .where(
            TrainingSession.session_id == session_id,
            TrainingSession.worker_id == current_worker.worker_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="会话不存在"
        )
    
    # 验证session_token
    if session.session_token != request.session_token:
        return error_response(
            code=ErrorCode.SESSION_TOKEN_INVALID,
            message="会话Token无效"
        )
    
    if session.status not in ["IN_LEARNING", "WAITING_VERIFY"]:
        return error_response(
            code=ErrorCode.SESSION_EXPIRED,
            message="会话已结束"
        )
    
    # 获取视频时长
    video_result = await db.execute(
        select(TrainingVideo).where(TrainingVideo.video_id == session.video_id)
    )
    video = video_result.scalar_one_or_none()
    
    # P0-2: 进度验证
    validator = TrainingProgressValidator()
    progress_data = ProgressData(
        session_token=request.session_token,
        position=request.position,
        played_seconds_delta=request.played_seconds_delta,
        video_state=request.video_state,
        client_ts=request.client_ts
    )
    
    validation_result = await validator.validate_progress(
        session=session,
        progress_data=progress_data,
        video_duration=video.duration_sec
    )
    
    if not validation_result.valid:
        if session.status == "FAILED":
            await db.commit()
            return error_response(
                code=ErrorCode.TRAINING_FAILED,
                message=f"学习失败: {validation_result.reason}"
            )
    
    # 检查是否需要随机校验
    check_scheduler = RandomCheckScheduler()
    need_check = check_scheduler.should_trigger_check(session)
    
    if need_check:
        session.status = "WAITING_VERIFY"
        action = FaceVerifyAdapter().get_random_action()
        instruction = FaceVerifyAdapter().get_action_instruction(action)
        
        await db.commit()
        
        return success_response({
            "valid_watch_sec": session.valid_watch_sec,
            "need_verify": True,
            "verify_action": action,
            "verify_instruction": instruction
        })
    
    # 检查是否完成
    is_complete = validator.check_completion(
        session=session,
        video_duration=video.duration_sec
    )
    
    if is_complete:
        session.status = "COMPLETED"
        session.ended_at = datetime.now()
        
        # 更新日票工人状态
        dtw_result = await db.execute(
            select(DailyTicketWorker).where(
                DailyTicketWorker.daily_ticket_id == session.daily_ticket_id,
                DailyTicketWorker.worker_id == current_worker.worker_id
            )
        )
        dtw = dtw_result.scalar_one_or_none()
        
        if dtw:
            dtw.completed_video_count += 1
            
            # 检查是否所有视频都完成
            if dtw.completed_video_count >= dtw.total_video_count:
                dtw.training_status = "COMPLETED"
                
                # 触发授权
                from app.services.access_service import AccessService
                access_service = AccessService(db)
                await access_service.create_grants_for_worker(
                    session.daily_ticket_id,
                    current_worker.worker_id
                )
                dtw.authorized = True
    
    await db.commit()
    
    return success_response({
        "valid_watch_sec": session.valid_watch_sec,
        "status": session.status,
        "need_verify": False,
        "is_complete": is_complete
    })


@router.post("/sessions/{session_id}/verify")
async def verify_face(
    session_id: uuid.UUID,
    request: FaceVerifyRequest,
    current_worker: Worker = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db)
):
    """
    随机人脸校验 (P0-2)
    """
    result = await db.execute(
        select(TrainingSession).where(
            TrainingSession.session_id == session_id,
            TrainingSession.worker_id == current_worker.worker_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="会话不存在"
        )
    
    if session.status != "WAITING_VERIFY":
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="当前不需要验证"
        )
    
    # 执行人脸活体校验
    face_adapter = FaceVerifyAdapter()
    verify_result = await face_adapter.verify_liveness(
        action_type=request.action_type,
        photo_base64=request.photo
    )
    
    passed = verify_result.get("passed", False)
    
    # P0-2: 处理校验结果
    check_scheduler = RandomCheckScheduler()
    session_failed = await check_scheduler.handle_check_result(session, passed)
    
    if session_failed:
        await db.commit()
        return error_response(
            code=ErrorCode.RANDOM_CHECK_FAILED,
            message="校验失败次数过多，学习终止"
        )
    
    # 恢复学习状态
    if passed:
        session.status = "IN_LEARNING"
    
    await db.commit()
    
    return success_response({
        "passed": passed,
        "status": session.status,
        "message": "验证通过" if passed else "验证失败，请重试"
    })


@router.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: uuid.UUID,
    request: CompleteSessionRequest,
    current_worker: Worker = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db)
):
    """
    完成学习会话
    """
    result = await db.execute(
        select(TrainingSession).where(
            TrainingSession.session_id == session_id,
            TrainingSession.worker_id == current_worker.worker_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="会话不存在"
        )
    
    if session.session_token != request.session_token:
        return error_response(
            code=ErrorCode.SESSION_TOKEN_INVALID,
            message="会话Token无效"
        )
    
    return success_response({
        "session_id": str(session.session_id),
        "status": session.status,
        "valid_watch_sec": session.valid_watch_sec
    })

