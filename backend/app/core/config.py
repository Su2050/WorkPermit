"""
应用配置
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用信息
    APP_NAME: str = "作业票管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API配置
    API_V1_PREFIX: str = "/api"
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/work_permit",
        description="数据库连接URL"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接URL"
    )
    
    # JWT配置
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT密钥"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    
    # 微信小程序配置
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""
    
    # MinIO配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "work-permit"
    MINIO_SECURE: bool = False
    
    # 门禁系统配置
    ACCESS_CONTROL_API_URL: str = ""
    ACCESS_CONTROL_API_KEY: str = ""
    ACCESS_CONTROL_SUPPORTS_TIME_WINDOW: bool = False
    ACCESS_CONTROL_SUPPORTS_QUERY: bool = False
    
    # 人脸识别配置
    FACE_VERIFY_API_URL: str = ""
    FACE_VERIFY_API_KEY: str = ""
    FACE_VERIFY_MOCK_PASS_RATE: float = 0.95  # Mock模式通过率
    
    # 实名制系统配置
    REALNAME_API_URL: str = ""
    REALNAME_API_KEY: str = ""
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json 或 text
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # 培训配置 (P0-2: 防作弊)
    TRAINING_MAX_SKIP_PERCENT: float = 0.05  # 允许跳跃5%
    TRAINING_HEARTBEAT_TIMEOUT: int = 60  # 心跳超时60秒
    TRAINING_MAX_SUSPICIOUS_COUNT: int = 3  # 最多3次可疑事件
    TRAINING_RANDOM_CHECK_MIN_INTERVAL: int = 180  # 随机校验最小间隔3分钟
    TRAINING_RANDOM_CHECK_MAX_INTERVAL: int = 420  # 随机校验最大间隔7分钟
    TRAINING_MAX_CONSECUTIVE_CHECK_FAILURES: int = 2  # 连续校验失败次数
    TRAINING_REQUIRED_WATCH_PERCENT: float = 0.95  # 要求观看比例95%
    
    # 通知配置 (P1-2)
    NOTIFICATION_ALLOWED_HOURS_START: int = 7  # 允许发送时间段开始
    NOTIFICATION_ALLOWED_HOURS_END: int = 21  # 允许发送时间段结束
    NOTIFICATION_MAX_RETRIES: int = 5  # 最大重试次数
    
    # 门禁同步配置
    ACCESS_SYNC_RETRY_INTERVALS: List[int] = [60, 300, 1800, 7200]  # 重试间隔：1m/5m/30m/2h
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()

