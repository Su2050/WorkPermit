"""
安全相关工具
- JWT Token 生成和验证
- 密码哈希和验证
"""
from datetime import datetime, timedelta
from typing import Any, Optional
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt

from .config import settings

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        # 先尝试使用passlib验证
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, AttributeError):
        # 如果passlib失败，尝试直接使用bcrypt验证
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    try:
        return pwd_context.hash(password)
    except (ValueError, AttributeError):
        # 如果passlib失败，直接使用bcrypt生成
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')


def create_access_token(
    subject: str | uuid.UUID,
    expires_delta: Optional[timedelta] = None,
    extra_data: Optional[dict[str, Any]] = None
) -> str:
    """
    创建JWT访问令牌
    
    Args:
        subject: 令牌主题（通常是用户ID）
        expires_delta: 过期时间
        extra_data: 额外数据（如角色、权限等）
    
    Returns:
        JWT令牌字符串
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    if extra_data:
        to_encode.update(extra_data)
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    解码JWT访问令牌
    
    Args:
        token: JWT令牌字符串
    
    Returns:
        解码后的payload，如果无效返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def create_mp_session_token(openid: str, worker_id: uuid.UUID) -> str:
    """
    创建小程序会话令牌
    
    Args:
        openid: 微信openid
        worker_id: 工人ID
    
    Returns:
        JWT令牌字符串
    """
    return create_access_token(
        subject=str(worker_id),
        extra_data={
            "openid": openid,
            "type": "mp_session"
        }
    )


def generate_session_token() -> str:
    """生成学习会话Token"""
    import secrets
    return secrets.token_urlsafe(32)

