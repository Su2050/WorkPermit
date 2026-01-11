# 适配器模块 - 第三方系统对接
from .realname_adapter import RealnameAdapter
from .access_control_adapter import AccessControlAdapter
from .face_verify_adapter import FaceVerifyAdapter
from .wechat_adapter import WechatAdapter

__all__ = [
    "RealnameAdapter",
    "AccessControlAdapter",
    "FaceVerifyAdapter",
    "WechatAdapter",
]

