"""
视频管理API
"""
import uuid
from typing import Optional
import os
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import TrainingVideo, SysUser
from app.api.admin.auth import get_current_user
from app.middleware.tenant import get_tenant_context, TenantQueryFilter
from app.utils.response import success_response, error_response, ErrorCode
from app.utils.pagination import PaginationParams, paginate

router = APIRouter()


class VideoCreate(BaseModel):
    """创建视频请求"""
    site_id: uuid.UUID = Field(...)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    file_url: str
    thumbnail_url: Optional[str] = None
    duration_sec: int
    category: Optional[str] = None
    is_shared: bool = False


class VideoUpdate(BaseModel):
    """更新视频请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    category: Optional[str] = None
    is_shared: Optional[bool] = None
    status: Optional[str] = None


class VideoQuery(PaginationParams):
    """查询视频参数"""
    keyword: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None


@router.get("")
async def list_videos(
    query: VideoQuery = Depends(),
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取视频列表"""
    ctx = get_tenant_context()
    
    stmt = select(TrainingVideo).order_by(TrainingVideo.created_at.desc())
    stmt = TenantQueryFilter.apply(stmt, ctx)
    
    if query.keyword:
        stmt = stmt.where(TrainingVideo.title.ilike(f"%{query.keyword}%"))
    
    if query.category:
        stmt = stmt.where(TrainingVideo.category == query.category)
    
    if query.status:
        stmt = stmt.where(TrainingVideo.status == query.status)
    
    result = await paginate(db, stmt, query)
    
    items = [
        {
            "video_id": str(video.video_id),
            "title": video.title,
            "description": video.description,
            "file_url": video.file_url,
            "thumbnail_url": video.thumbnail_url,
            "duration_sec": video.duration_sec,
            "category": video.category,
            "status": video.status,
            "is_shared": video.is_shared
        }
        for video in result.items
    ]
    
    return success_response({
        "items": items,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size
    })


@router.get("/options")
async def get_video_options(
    keyword: Optional[str] = None,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取视频选项（用于下拉框）"""
    ctx = get_tenant_context()
    
    # 查询活跃或已发布的视频，如果status为NULL也包含
    stmt = select(TrainingVideo).where(
        (TrainingVideo.status == "ACTIVE") | 
        (TrainingVideo.status == "PUBLISHED") |
        (TrainingVideo.status.is_(None))
    ).order_by(TrainingVideo.title)
    stmt = TenantQueryFilter.apply(stmt, ctx)
    
    if keyword:
        stmt = stmt.where(TrainingVideo.title.ilike(f"%{keyword}%"))
    
    result = await db.execute(stmt)
    videos = result.scalars().all()
    
    options = [
        {
            "id": str(video.video_id),
            "title": video.title,
            "video_id": str(video.video_id),
            "duration_sec": video.duration_sec
        }
        for video in videos
    ]
    
    return success_response(options)


@router.post("")
async def create_video(
    request: VideoCreate,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建视频"""
    ctx = get_tenant_context()
    
    # 验证用户是否有权访问该工地
    if not ctx.is_sys_admin and request.site_id not in ctx.accessible_sites:
        return error_response(
            code=ErrorCode.FORBIDDEN,
            message="无权在该工地创建视频"
        )
    
    video = TrainingVideo(
        site_id=request.site_id,
        title=request.title,
        description=request.description,
        file_url=request.file_url,
        thumbnail_url=request.thumbnail_url,
        duration_sec=request.duration_sec,
        category=request.category,
        is_shared=request.is_shared,
        status="ACTIVE"
    )
    db.add(video)
    await db.commit()
    
    return success_response({
        "video_id": str(video.video_id)
    }, message="视频创建成功")


@router.get("/{video_id}")
async def get_video(
    video_id: uuid.UUID,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取视频详情"""
    result = await db.execute(
        select(TrainingVideo).where(TrainingVideo.video_id == video_id)
    )
    video = result.scalar_one_or_none()
    
    if not video:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="视频不存在"
        )
    
    return success_response({
        "video_id": str(video.video_id),
        "title": video.title,
        "description": video.description,
        "file_url": video.file_url,
        "thumbnail_url": video.thumbnail_url,
        "duration_sec": video.duration_sec,
        "category": video.category,
        "status": video.status,
        "is_shared": video.is_shared,
        "created_at": video.created_at.isoformat()
    })


@router.patch("/{video_id}")
async def update_video(
    video_id: uuid.UUID,
    request: VideoUpdate,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新视频"""
    result = await db.execute(
        select(TrainingVideo).where(TrainingVideo.video_id == video_id)
    )
    video = result.scalar_one_or_none()
    
    if not video:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="视频不存在"
        )
    
    if request.title is not None:
        video.title = request.title
    if request.description is not None:
        video.description = request.description
    if request.thumbnail_url is not None:
        video.thumbnail_url = request.thumbnail_url
    if request.category is not None:
        video.category = request.category
    if request.is_shared is not None:
        video.is_shared = request.is_shared
    if request.status is not None:
        video.status = request.status
    
    await db.commit()
    
    return success_response({
        "video_id": str(video.video_id)
    }, message="视频更新成功")


@router.delete("/{video_id}")
async def delete_video(
    video_id: uuid.UUID,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除视频（归档）"""
    result = await db.execute(
        select(TrainingVideo).where(TrainingVideo.video_id == video_id)
    )
    video = result.scalar_one_or_none()
    
    if not video:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="视频不存在"
        )
    
    video.status = "ARCHIVED"
    await db.commit()
    
    return success_response(message="视频删除成功")


@router.get("/categories/list")
async def list_categories(
    current_user: SysUser = Depends(get_current_user)
):
    """获取视频分类列表"""
    categories = [
        {"value": "high_work", "label": "高处作业安全"},
        {"value": "electrical", "label": "用电安全"},
        {"value": "fire", "label": "消防安全"},
        {"value": "mechanical", "label": "机械设备安全"},
        {"value": "lifting", "label": "起重吊装安全"},
        {"value": "confined_space", "label": "有限空间作业"},
        {"value": "welding", "label": "动火作业安全"},
        {"value": "general", "label": "通用安全"}
    ]
    return success_response(categories)


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    is_shared: bool = Form(False),
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传培训视频 (P1-5)
    
    1. 验证文件格式和大小
    2. 保存文件到存储系统（本地/MinIO/OSS）
    3. 提取视频元数据（时长、分辨率等）
    4. 创建视频记录
    
    支持的视频格式：mp4, avi, mov, wmv, flv, mkv
    最大文件大小：500MB
    """
    ctx = get_tenant_context()
    
    # 验证文件格式
    allowed_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"不支持的视频格式，请上传以下格式之一：{', '.join(allowed_extensions)}"
        )
    
    # 验证文件大小（500MB）
    MAX_FILE_SIZE = 500 * 1024 * 1024
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > MAX_FILE_SIZE:
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="文件大小超过限制（最大500MB）"
        )
    
    try:
        # 生成唯一文件名
        file_id = uuid.uuid4()
        safe_filename = f"{file_id}{file_ext}"
        
        # 保存文件到本地存储（生产环境应使用MinIO/OSS）
        upload_dir = "uploads/videos"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, safe_filename)
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # 提取视频元数据（使用 ffprobe）
        duration_sec = 0
        width = 0
        height = 0
        
        try:
            import subprocess
            import json
            
            # 使用 ffprobe 获取视频信息
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                
                # 获取时长
                if 'format' in info and 'duration' in info['format']:
                    duration_sec = int(float(info['format']['duration']))
                
                # 获取分辨率
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        width = stream.get('width', 0)
                        height = stream.get('height', 0)
                        break
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to extract video metadata: {e}")
            # 如果无法提取元数据，使用默认值
            duration_sec = 300  # 默认5分钟
        
        # 生成缩略图（可选）
        thumbnail_url = None
        try:
            thumbnail_filename = f"{file_id}_thumb.jpg"
            thumbnail_path = os.path.join(upload_dir, thumbnail_filename)
            
            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-ss', '00:00:01',
                '-vframes', '1',
                '-vf', 'scale=320:-1',
                thumbnail_path
            ]
            
            subprocess.run(cmd, capture_output=True, timeout=10)
            
            if os.path.exists(thumbnail_path):
                thumbnail_url = f"/uploads/videos/{thumbnail_filename}"
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to generate thumbnail: {e}")
        
        # 创建视频记录
        video = TrainingVideo(
            site_id=ctx.site_id,
            title=title,
            description=description,
            file_url=f"/uploads/videos/{safe_filename}",
            thumbnail_url=thumbnail_url,
            duration_sec=duration_sec,
            file_size=file_size,
            category=category,
            is_shared=is_shared,
            status="ACTIVE",
            created_by=current_user.user_id
        )
        
        # 如果有分辨率信息，保存到备注中
        if width and height:
            video.description = f"{description or ''}\n分辨率: {width}x{height}".strip()
        
        db.add(video)
        await db.commit()
        await db.refresh(video)
        
        return success_response({
            "video_id": str(video.video_id),
            "title": video.title,
            "file_url": video.file_url,
            "thumbnail_url": video.thumbnail_url,
            "duration_sec": video.duration_sec,
            "file_size": video.file_size,
            "resolution": f"{width}x{height}" if width and height else None
        }, message="视频上传成功")
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"上传视频失败: {e}")
        
        # 清理已上传的文件
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        
        await db.rollback()
        return error_response(
            code=ErrorCode.UNKNOWN_ERROR,
            message=f"上传失败: {str(e)}"
        )

