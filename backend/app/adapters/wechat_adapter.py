"""
微信小程序适配器
- 登录（code换session）
- 发送订阅消息
"""
import uuid
from typing import Optional, Any
import logging
import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)


class WechatAdapter:
    """
    微信小程序适配器
    
    功能：
    - code2session: 登录凭证校验
    - send_subscribe_message: 发送订阅消息
    """
    
    def __init__(self):
        self.appid = settings.WECHAT_APPID
        self.secret = settings.WECHAT_SECRET
        self.is_mock = not bool(self.appid)
    
    async def code2session(self, code: str) -> dict:
        """
        登录凭证校验
        
        Args:
            code: 微信登录code
        
        Returns:
            dict: {
                "success": bool,
                "openid": str,
                "unionid": str,
                "session_key": str,
                "error": str
            }
        """
        if self.is_mock:
            return await self._mock_code2session(code)
        
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.weixin.qq.com/sns/jscode2session",
                    params={
                        "appid": self.appid,
                        "secret": self.secret,
                        "js_code": code,
                        "grant_type": "authorization_code"
                    }
                )
                
                data = response.json()
                
                if "errcode" in data and data["errcode"] != 0:
                    return {
                        "success": False,
                        "error": data.get("errmsg", "Unknown error")
                    }
                
                return {
                    "success": True,
                    "openid": data.get("openid"),
                    "unionid": data.get("unionid"),
                    "session_key": data.get("session_key")
                }
                
        except Exception as e:
            logger.error(f"code2session failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_phone_number(
        self,
        code: str,
        openid: str
    ) -> dict:
        """
        获取手机号（通过 getPhoneNumber 按钮）
        
        Args:
            code: getPhoneNumber 返回的 code
            openid: 用户openid
        
        Returns:
            dict: {
                "success": bool,
                "phone": str,
                "error": str
            }
        """
        if self.is_mock:
            return await self._mock_get_phone_number(code)
        
        import httpx
        
        try:
            # 获取 access_token
            access_token = await self._get_access_token()
            if not access_token:
                return {"success": False, "error": "Failed to get access token"}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={access_token}",
                    json={"code": code}
                )
                
                data = response.json()
                
                if data.get("errcode") != 0:
                    return {
                        "success": False,
                        "error": data.get("errmsg", "Unknown error")
                    }
                
                phone_info = data.get("phone_info", {})
                return {
                    "success": True,
                    "phone": phone_info.get("purePhoneNumber")
                }
                
        except Exception as e:
            logger.error(f"getPhoneNumber failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_subscribe_message(
        self,
        worker_id: uuid.UUID,
        notification_type: str,
        data: dict
    ) -> dict:
        """
        发送订阅消息
        
        Args:
            worker_id: 工人ID
            notification_type: 通知类型
            data: 通知数据
        
        Returns:
            dict: {"success": bool, "error": str}
        """
        if self.is_mock:
            return await self._mock_send_subscribe_message(
                worker_id, notification_type, data
            )
        
        # 获取工人的openid
        from app.core.database import SessionLocal
        from app.models import Worker
        from sqlalchemy import select
        
        async with SessionLocal() as db:
            result = await db.execute(
                select(Worker).where(Worker.worker_id == worker_id)
            )
            worker = result.scalar_one_or_none()
            
            if not worker or not worker.wechat_openid:
                return {
                    "success": False,
                    "error": "Worker not bound to WeChat"
                }
            
            openid = worker.wechat_openid
        
        # 发送消息
        import httpx
        
        try:
            access_token = await self._get_access_token()
            if not access_token:
                return {"success": False, "error": "Failed to get access token"}
            
            # 根据通知类型选择模板
            template_id = self._get_template_id(notification_type)
            template_data = self._format_template_data(notification_type, data)
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}",
                    json={
                        "touser": openid,
                        "template_id": template_id,
                        "page": "pages/index/index",
                        "data": template_data,
                        "miniprogram_state": "formal",
                        "lang": "zh_CN"
                    }
                )
                
                result = response.json()
                
                if result.get("errcode") == 0:
                    return {"success": True}
                else:
                    return {
                        "success": False,
                        "error": result.get("errmsg", "Unknown error")
                    }
                    
        except Exception as e:
            logger.error(f"send_subscribe_message failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_access_token(self) -> Optional[str]:
        """获取 access_token（带缓存）"""
        # TODO: 实现 access_token 缓存
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.weixin.qq.com/cgi-bin/token",
                    params={
                        "grant_type": "client_credential",
                        "appid": self.appid,
                        "secret": self.secret
                    }
                )
                
                data = response.json()
                return data.get("access_token")
                
        except Exception as e:
            logger.error(f"get_access_token failed: {e}")
            return None
    
    def _get_template_id(self, notification_type: str) -> str:
        """根据通知类型获取模板ID"""
        # TODO: 从配置中读取模板ID
        templates = {
            "TICKET_PUBLISHED": "template_id_1",
            "DAILY_REMINDER": "template_id_2",
            "DEADLINE_SOON": "template_id_3",
            "BIND_REQUIRED": "template_id_4"
        }
        return templates.get(notification_type, "template_id_default")
    
    def _format_template_data(
        self,
        notification_type: str,
        data: dict
    ) -> dict:
        """格式化模板数据"""
        # 根据不同通知类型格式化数据
        if notification_type == "DAILY_REMINDER":
            return {
                "thing1": {"value": data.get("ticket_title", "培训任务")[:20]},
                "time2": {"value": data.get("deadline", "07:30")},
                "number3": {"value": str(data.get("remaining_videos", 0))}
            }
        elif notification_type == "DEADLINE_SOON":
            return {
                "thing1": {"value": data.get("ticket_title", "培训任务")[:20]},
                "time2": {"value": data.get("deadline", "07:30")},
                "thing3": {"value": "即将截止，请尽快完成"}
            }
        else:
            return {
                "thing1": {"value": data.get("title", "通知")[:20]}
            }
    
    # Mock实现方法
    async def _mock_code2session(self, code: str) -> dict:
        """Mock code2session"""
        await asyncio.sleep(0.2)
        
        # 生成模拟的openid
        mock_openid = f"mock_openid_{code[:8]}"
        mock_unionid = f"mock_unionid_{code[:8]}"
        
        logger.info(f"Mock: code2session - code={code[:8]}..., openid={mock_openid}")
        
        return {
            "success": True,
            "openid": mock_openid,
            "unionid": mock_unionid,
            "session_key": f"mock_session_{code[:8]}"
        }
    
    async def _mock_get_phone_number(self, code: str) -> dict:
        """Mock getPhoneNumber"""
        await asyncio.sleep(0.2)
        
        # 返回模拟手机号
        mock_phone = f"138{code[:8].ljust(8, '0')}"
        
        logger.info(f"Mock: getPhoneNumber - phone={mock_phone}")
        
        return {
            "success": True,
            "phone": mock_phone
        }
    
    async def _mock_send_subscribe_message(
        self,
        worker_id: uuid.UUID,
        notification_type: str,
        data: dict
    ) -> dict:
        """Mock发送订阅消息"""
        await asyncio.sleep(0.3)
        
        logger.info(
            f"Mock: send_subscribe_message - "
            f"worker={worker_id}, type={notification_type}, data={data}"
        )
        
        return {"success": True}

