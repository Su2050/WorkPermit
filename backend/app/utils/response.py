"""
API响应工具
"""
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    code: int = 0
    message: str = "ok"
    data: Optional[T] = None


def success_response(data: Any = None, message: str = "ok") -> dict:
    """成功响应"""
    return {
        "code": 0,
        "message": message,
        "data": data
    }


def error_response(
    code: int, 
    message: str, 
    data: Any = None
) -> dict:
    """错误响应"""
    return {
        "code": code,
        "message": message,
        "data": data
    }


# 错误码定义
class ErrorCode:
    """错误码常量"""
    
    # 通用错误 (1xxxx)
    UNKNOWN_ERROR = 10000
    VALIDATION_ERROR = 10001
    NOT_FOUND = 10002
    PERMISSION_DENIED = 10003
    RATE_LIMIT = 10004
    
    # 认证错误 (2xxxx)
    AUTH_FAILED = 20001
    TOKEN_EXPIRED = 20002
    TOKEN_INVALID = 20003
    USER_NOT_FOUND = 20004
    PASSWORD_INCORRECT = 20005
    USER_LOCKED = 20006
    
    # 作业票错误 (3xxxx)
    TICKET_NOT_FOUND = 30001
    TICKET_CANCELLED = 30002
    TICKET_EXPIRED = 30003
    TICKET_CHANGE_FORBIDDEN = 30004
    WORKER_NOT_IN_TICKET = 30005
    AREA_NOT_IN_TICKET = 30006
    VIDEO_NOT_IN_TICKET = 30007
    
    # 培训错误 (4xxxx)
    TRAINING_NOT_STARTED = 40001
    TRAINING_ALREADY_COMPLETED = 40002
    TRAINING_FAILED = 40003
    SESSION_TOKEN_INVALID = 40004
    SESSION_EXPIRED = 40005
    FACE_VERIFY_FAILED = 40006
    RANDOM_CHECK_FAILED = 40007
    
    # 门禁错误 (5xxxx)
    ACCESS_GRANT_NOT_FOUND = 50001
    ACCESS_SYNC_FAILED = 50002
    ACCESS_REVOKED = 50003
    OUT_OF_TIME_WINDOW = 50004
    TRAINING_INCOMPLETE = 50005
    
    # 小程序错误 (6xxxx)
    WORKER_NOT_FOUND_IN_REALNAME = 60001
    WORKER_ALREADY_BOUND = 60002
    BIND_FAILED = 60003
    WECHAT_AUTH_FAILED = 60004


# 错误消息映射
ERROR_MESSAGES = {
    ErrorCode.UNKNOWN_ERROR: "未知错误",
    ErrorCode.VALIDATION_ERROR: "参数校验失败",
    ErrorCode.NOT_FOUND: "资源不存在",
    ErrorCode.PERMISSION_DENIED: "权限不足",
    ErrorCode.RATE_LIMIT: "请求过于频繁",
    
    ErrorCode.AUTH_FAILED: "认证失败",
    ErrorCode.TOKEN_EXPIRED: "令牌已过期",
    ErrorCode.TOKEN_INVALID: "令牌无效",
    ErrorCode.USER_NOT_FOUND: "用户不存在",
    ErrorCode.PASSWORD_INCORRECT: "密码错误",
    ErrorCode.USER_LOCKED: "用户已锁定",
    
    ErrorCode.TICKET_NOT_FOUND: "作业票不存在",
    ErrorCode.TICKET_CANCELLED: "作业票已取消",
    ErrorCode.TICKET_EXPIRED: "作业票已过期",
    ErrorCode.TICKET_CHANGE_FORBIDDEN: "作业票变更被禁止",
    ErrorCode.WORKER_NOT_IN_TICKET: "人员不在作业票名单中",
    ErrorCode.AREA_NOT_IN_TICKET: "区域不在作业票中",
    ErrorCode.VIDEO_NOT_IN_TICKET: "视频不在作业票中",
    
    ErrorCode.TRAINING_NOT_STARTED: "培训未开始",
    ErrorCode.TRAINING_ALREADY_COMPLETED: "培训已完成",
    ErrorCode.TRAINING_FAILED: "培训失败",
    ErrorCode.SESSION_TOKEN_INVALID: "会话Token无效",
    ErrorCode.SESSION_EXPIRED: "会话已过期",
    ErrorCode.FACE_VERIFY_FAILED: "人脸验证失败",
    ErrorCode.RANDOM_CHECK_FAILED: "随机校验失败",
    
    ErrorCode.ACCESS_GRANT_NOT_FOUND: "门禁授权不存在",
    ErrorCode.ACCESS_SYNC_FAILED: "门禁同步失败",
    ErrorCode.ACCESS_REVOKED: "门禁授权已撤销",
    ErrorCode.OUT_OF_TIME_WINDOW: "不在授权时间窗内",
    ErrorCode.TRAINING_INCOMPLETE: "培训未完成",
    
    ErrorCode.WORKER_NOT_FOUND_IN_REALNAME: "未在实名制系统中找到该人员",
    ErrorCode.WORKER_ALREADY_BOUND: "该人员已绑定其他微信账号",
    ErrorCode.BIND_FAILED: "绑定失败",
    ErrorCode.WECHAT_AUTH_FAILED: "微信认证失败",
}


def get_error_message(code: int) -> str:
    """获取错误消息"""
    return ERROR_MESSAGES.get(code, "未知错误")

