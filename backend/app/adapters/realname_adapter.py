"""
实名制系统适配器 (Mock实现)
- 查询人员清单
- 获取人员信息
"""
import uuid
from dataclasses import dataclass
from typing import Optional, List
import logging
import random

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RealnameWorker:
    """实名制系统人员信息"""
    id_no: str  # 身份证号
    name: str
    phone: str
    contractor_name: Optional[str] = None
    job_type: Optional[str] = None
    team_name: Optional[str] = None
    face_id: Optional[str] = None
    photo_url: Optional[str] = None


class RealnameAdapter:
    """
    实名制系统适配器
    
    Mock实现：返回测试数据
    真实实现：调用实名制系统API
    """
    
    # Mock数据
    MOCK_WORKERS = [
        RealnameWorker(
            id_no="330102199001011234",
            name="张三",
            phone="13800138001",
            contractor_name="中建一局",
            job_type="钢筋工",
            team_name="钢筋班组1",
            face_id="face_001"
        ),
        RealnameWorker(
            id_no="330102199002021235",
            name="李四",
            phone="13800138002",
            contractor_name="中建一局",
            job_type="木工",
            team_name="木工班组1",
            face_id="face_002"
        ),
        RealnameWorker(
            id_no="330102199003031236",
            name="王五",
            phone="13800138003",
            contractor_name="中建二局",
            job_type="电工",
            team_name="电工班组1",
            face_id="face_003"
        ),
        RealnameWorker(
            id_no="330102199004041237",
            name="赵六",
            phone="13800138004",
            contractor_name="中建二局",
            job_type="焊工",
            team_name="焊接班组1",
            face_id="face_004"
        ),
        RealnameWorker(
            id_no="330102199005051238",
            name="钱七",
            phone="13800138005",
            contractor_name="中建三局",
            job_type="架子工",
            team_name="脚手架班组1",
            face_id="face_005"
        ),
    ]
    
    def __init__(self):
        self.api_url = settings.REALNAME_API_URL
        self.api_key = settings.REALNAME_API_KEY
        self.is_mock = not bool(self.api_url)
    
    async def search_workers(
        self,
        keyword: str = None,
        contractor_name: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """
        查询人员列表
        
        Args:
            keyword: 搜索关键词（姓名/手机号/身份证）
            contractor_name: 施工单位名称
            page: 页码
            page_size: 每页数量
        
        Returns:
            dict: {"items": [...], "total": int}
        """
        if self.is_mock:
            return await self._mock_search_workers(
                keyword, contractor_name, page, page_size
            )
        
        # 真实实现
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/workers",
                params={
                    "keyword": keyword,
                    "contractor_name": contractor_name,
                    "page": page,
                    "page_size": page_size
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Realname API error: {response.status_code}")
                raise Exception(f"Realname API error: {response.status_code}")
    
    async def get_worker_by_id_no(self, id_no: str) -> Optional[RealnameWorker]:
        """
        根据身份证号查询人员
        
        Args:
            id_no: 身份证号
        
        Returns:
            RealnameWorker: 人员信息，未找到返回None
        """
        if self.is_mock:
            return await self._mock_get_worker_by_id_no(id_no)
        
        # 真实实现
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/workers/{id_no}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return RealnameWorker(**data)
            elif response.status_code == 404:
                return None
            else:
                logger.error(f"Realname API error: {response.status_code}")
                raise Exception(f"Realname API error: {response.status_code}")
    
    async def match_worker(
        self,
        id_no: str,
        phone: str = None,
        name: str = None
    ) -> Optional[RealnameWorker]:
        """
        匹配人员（用于小程序绑定）
        
        规则：
        1. 身份证号全匹配优先
        2. 姓名+手机号辅助匹配
        
        Args:
            id_no: 身份证号
            phone: 手机号
            name: 姓名
        
        Returns:
            RealnameWorker: 匹配到的人员，未找到返回None
        """
        # 优先身份证号匹配
        worker = await self.get_worker_by_id_no(id_no)
        if worker:
            return worker
        
        # 辅助匹配（姓名+手机号）
        if name and phone:
            result = await self.search_workers(keyword=phone)
            for w in result.get("items", []):
                if w.name == name and w.phone == phone:
                    return w
        
        return None
    
    # Mock实现方法
    async def _mock_search_workers(
        self,
        keyword: str = None,
        contractor_name: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """Mock搜索人员"""
        filtered = self.MOCK_WORKERS.copy()
        
        if keyword:
            keyword = keyword.lower()
            filtered = [
                w for w in filtered
                if keyword in w.name.lower()
                or keyword in w.phone
                or keyword in w.id_no
            ]
        
        if contractor_name:
            filtered = [
                w for w in filtered
                if w.contractor_name == contractor_name
            ]
        
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        items = filtered[start:end]
        
        return {
            "items": [w.__dict__ for w in items],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    async def _mock_get_worker_by_id_no(self, id_no: str) -> Optional[RealnameWorker]:
        """Mock根据身份证号查询"""
        for worker in self.MOCK_WORKERS:
            if worker.id_no == id_no:
                return worker
        return None

