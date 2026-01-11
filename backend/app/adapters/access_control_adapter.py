"""
门禁系统适配器 (Mock实现)
- 推送授权 (P1-1: 幂等)
- 撤销授权
- 查询有效权限 (P0-6: 对账)
"""
import uuid
from datetime import datetime
from typing import Optional, List, Any
import logging
import asyncio
import random

from app.core.config import settings

logger = logging.getLogger(__name__)


class AccessControlAdapter:
    """
    门禁系统适配器
    
    Mock实现：记录日志，模拟延迟，返回成功
    真实实现：调用门禁系统API
    
    P1-1: 使用 grant_id 作为幂等键
    P0-4: 支持时间窗降级策略
    """
    
    # Mock存储（模拟门禁系统状态）
    _mock_grants: dict = {}
    
    def __init__(self):
        self.api_url = settings.ACCESS_CONTROL_API_URL
        self.api_key = settings.ACCESS_CONTROL_API_KEY
        self.is_mock = not bool(self.api_url)
        self.supports_time_window = settings.ACCESS_CONTROL_SUPPORTS_TIME_WINDOW
        self.supports_query = settings.ACCESS_CONTROL_SUPPORTS_QUERY
    
    async def push_grant(self, grant: Any) -> dict:
        """
        推送授权到门禁系统 (P1-1: 幂等)
        
        Args:
            grant: AccessGrant对象
        
        Returns:
            dict: {"success": bool, "vendor_ref": str, "error": str}
        """
        if self.is_mock:
            return await self._mock_push_grant(grant)
        
        # 真实实现
        import httpx
        
        # P1-1: 使用 grant_id 作为幂等键
        idempotency_key = str(grant.grant_id)
        
        payload = {
            "idempotency_key": idempotency_key,
            "worker": {
                "external_id": str(grant.worker_id),
                "face_id": grant.worker.face_id if hasattr(grant, 'worker') else None,
            },
            "area": {
                "access_group_id": grant.area.access_group_id if hasattr(grant, 'area') else None,
            },
            "valid_from": grant.valid_from.isoformat(),
            "valid_to": grant.valid_to.isoformat(),
            "action": "GRANT"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/grants",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Idempotency-Key": idempotency_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "vendor_ref": data.get("grant_ref")
                    }
                elif response.status_code == 409:
                    # 幂等：已存在，视为成功
                    logger.info(f"Grant already exists (idempotent): {idempotency_key}")
                    return {
                        "success": True,
                        "vendor_ref": idempotency_key
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to push grant: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def revoke_grant(self, grant: Any) -> dict:
        """
        撤销授权
        
        Args:
            grant: AccessGrant对象
        
        Returns:
            dict: {"success": bool, "error": str}
        """
        if self.is_mock:
            return await self._mock_revoke_grant(grant)
        
        # 真实实现
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.api_url}/grants/{grant.vendor_ref}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code in [200, 204, 404]:
                    # 404也视为成功（幂等：已不存在）
                    return {"success": True}
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to revoke grant: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def query_effective_grants(self, site_id: uuid.UUID) -> List[dict]:
        """
        查询有效权限 (P0-6: 用于二级对账)
        
        Args:
            site_id: 工地ID
        
        Returns:
            List[dict]: [{"worker_id": str, "area_id": str, "vendor_ref": str}, ...]
        """
        if not self.supports_query:
            logger.warning("Access control system does not support query grants")
            return []
        
        if self.is_mock:
            return await self._mock_query_effective_grants(site_id)
        
        # 真实实现
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.api_url}/grants/effective",
                    params={"site_id": str(site_id)},
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    return response.json().get("grants", [])
                else:
                    logger.error(f"Failed to query grants: HTTP {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to query grants: {e}")
            return []
    
    # Mock实现方法
    async def _mock_push_grant(self, grant: Any) -> dict:
        """Mock推送授权"""
        # 模拟网络延迟
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # 模拟偶尔失败（5%概率）
        if random.random() < 0.05:
            logger.warning(f"Mock: Simulated push failure for grant {grant.grant_id}")
            return {
                "success": False,
                "error": "Mock simulated failure"
            }
        
        # P1-1: 幂等 - 检查是否已存在
        grant_key = str(grant.grant_id)
        if grant_key in self._mock_grants:
            logger.info(f"Mock: Grant already exists (idempotent): {grant_key}")
        
        # 存储授权
        self._mock_grants[grant_key] = {
            "grant_id": grant_key,
            "worker_id": str(grant.worker_id),
            "area_id": str(grant.area_id),
            "valid_from": grant.valid_from.isoformat(),
            "valid_to": grant.valid_to.isoformat(),
            "vendor_ref": f"mock_ref_{grant_key[:8]}"
        }
        
        logger.info(
            f"Mock: Grant pushed successfully: "
            f"grant={grant_key}, worker={grant.worker_id}, area={grant.area_id}"
        )
        
        return {
            "success": True,
            "vendor_ref": self._mock_grants[grant_key]["vendor_ref"]
        }
    
    async def _mock_revoke_grant(self, grant: Any) -> dict:
        """Mock撤销授权"""
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        grant_key = str(grant.grant_id)
        if grant_key in self._mock_grants:
            del self._mock_grants[grant_key]
            logger.info(f"Mock: Grant revoked: {grant_key}")
        else:
            logger.info(f"Mock: Grant not found (already revoked): {grant_key}")
        
        return {"success": True}
    
    async def _mock_query_effective_grants(self, site_id: uuid.UUID) -> List[dict]:
        """Mock查询有效权限"""
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        now = datetime.now()
        effective = []
        
        for grant_data in self._mock_grants.values():
            valid_from = datetime.fromisoformat(grant_data["valid_from"])
            valid_to = datetime.fromisoformat(grant_data["valid_to"])
            
            if valid_from <= now <= valid_to:
                effective.append({
                    "worker_id": grant_data["worker_id"],
                    "area_id": grant_data["area_id"],
                    "vendor_ref": grant_data["vendor_ref"]
                })
        
        logger.info(f"Mock: Query effective grants: site={site_id}, count={len(effective)}")
        return effective

