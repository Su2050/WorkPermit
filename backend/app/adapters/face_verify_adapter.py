"""
人脸识别适配器 (Mock实现)
- 人脸验证（活体+比对）
- 随机活体校验
"""
import uuid
from typing import Optional
import logging
import asyncio
import random

from app.core.config import settings

logger = logging.getLogger(__name__)


class FaceVerifyAdapter:
    """
    人脸识别适配器
    
    Mock实现：随机通过/失败（可配置通过率）
    真实实现：调用人脸识别服务API
    """
    
    def __init__(self):
        self.api_url = settings.FACE_VERIFY_API_URL
        self.api_key = settings.FACE_VERIFY_API_KEY
        self.is_mock = not bool(self.api_url)
        self.mock_pass_rate = settings.FACE_VERIFY_MOCK_PASS_RATE
    
    async def verify_face(
        self,
        photo_base64: str,
        id_no: str,
        worker_id: uuid.UUID = None
    ) -> dict:
        """
        人脸验证（活体+比对）
        
        用于学习前验证本人
        
        Args:
            photo_base64: 人脸照片的Base64编码
            id_no: 身份证号（用于比对）
            worker_id: 工人ID（可选）
        
        Returns:
            dict: {
                "success": bool,
                "passed": bool,
                "confidence": float,
                "liveness_passed": bool,
                "error": str
            }
        """
        if self.is_mock:
            return await self._mock_verify_face(photo_base64, id_no, worker_id)
        
        # 真实实现
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/verify",
                    json={
                        "photo": photo_base64,
                        "id_no": id_no,
                        "worker_id": str(worker_id) if worker_id else None
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "passed": data.get("passed", False),
                        "confidence": data.get("confidence", 0),
                        "liveness_passed": data.get("liveness_passed", False)
                    }
                else:
                    return {
                        "success": False,
                        "passed": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"Face verify failed: {e}")
            return {
                "success": False,
                "passed": False,
                "error": str(e)
            }
    
    async def verify_liveness(
        self,
        action_type: str = "blink",
        photo_base64: str = None,
        video_base64: str = None
    ) -> dict:
        """
        随机活体校验 (P0-2)
        
        用于学习过程中的随机校验
        
        Args:
            action_type: 动作类型 (blink/nod/shake/mouth)
            photo_base64: 照片Base64（静态校验）
            video_base64: 视频Base64（动态校验）
        
        Returns:
            dict: {
                "success": bool,
                "passed": bool,
                "confidence": float,
                "error": str
            }
        """
        if self.is_mock:
            return await self._mock_verify_liveness(action_type)
        
        # 真实实现
        import httpx
        
        try:
            payload = {"action_type": action_type}
            if photo_base64:
                payload["photo"] = photo_base64
            if video_base64:
                payload["video"] = video_base64
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/liveness",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "passed": data.get("passed", False),
                        "confidence": data.get("confidence", 0)
                    }
                else:
                    return {
                        "success": False,
                        "passed": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"Liveness verify failed: {e}")
            return {
                "success": False,
                "passed": False,
                "error": str(e)
            }
    
    def get_random_action(self) -> str:
        """
        获取随机活体校验动作
        
        Returns:
            str: 动作类型
        """
        actions = ["blink", "nod", "shake", "mouth"]
        return random.choice(actions)
    
    def get_action_instruction(self, action_type: str) -> str:
        """
        获取动作指示文案
        
        Args:
            action_type: 动作类型
        
        Returns:
            str: 指示文案
        """
        instructions = {
            "blink": "请眨眨眼",
            "nod": "请点点头",
            "shake": "请左右摇头",
            "mouth": "请张张嘴"
        }
        return instructions.get(action_type, "请正对摄像头")
    
    # Mock实现方法
    async def _mock_verify_face(
        self,
        photo_base64: str,
        id_no: str,
        worker_id: uuid.UUID
    ) -> dict:
        """Mock人脸验证"""
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # 根据配置的通过率决定结果
        passed = random.random() < self.mock_pass_rate
        confidence = random.uniform(0.8, 0.99) if passed else random.uniform(0.3, 0.7)
        
        logger.info(
            f"Mock: Face verify - id_no={id_no}, "
            f"passed={passed}, confidence={confidence:.2f}"
        )
        
        return {
            "success": True,
            "passed": passed,
            "confidence": confidence,
            "liveness_passed": passed
        }
    
    async def _mock_verify_liveness(self, action_type: str) -> dict:
        """Mock活体校验"""
        await asyncio.sleep(random.uniform(0.3, 1.0))
        
        # 根据配置的通过率决定结果
        passed = random.random() < self.mock_pass_rate
        confidence = random.uniform(0.85, 0.99) if passed else random.uniform(0.4, 0.8)
        
        logger.info(
            f"Mock: Liveness verify - action={action_type}, "
            f"passed={passed}, confidence={confidence:.2f}"
        )
        
        return {
            "success": True,
            "passed": passed,
            "confidence": confidence
        }

