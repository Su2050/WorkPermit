"""
分页工具
"""
from typing import Any, Generic, List, TypeVar
from dataclasses import dataclass

from pydantic import BaseModel, Field
from sqlalchemy import Select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=1000, description="每页数量")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size


@dataclass
class PaginatedResult(Generic[T]):
    """分页结果"""
    items: List[T]
    total: int
    page: int
    page_size: int
    
    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1
    
    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
        }


async def paginate(
    db: AsyncSession,
    query: Select,
    params: PaginationParams
) -> PaginatedResult:
    """
    执行分页查询
    
    Args:
        db: 数据库会话
        query: SQLAlchemy查询
        params: 分页参数
    
    Returns:
        PaginatedResult: 分页结果
    """
    from sqlalchemy import select
    
    # 获取查询的主实体和where条件
    try:
        # 获取主实体
        entity = query.column_descriptions[0]['entity']
        
        # 构建计数查询
        count_query = select(func.count()).select_from(entity)
        
        # 复制where条件
        if hasattr(query, 'whereclause') and query.whereclause is not None:
            count_query = count_query.where(query.whereclause)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
    except Exception as e:
        # 如果出错，先获取所有数据再计算总数（性能较差，但能工作）
        all_result = await db.execute(query)
        all_items = all_result.scalars().all()
        total = len(all_items)
        
        # 手动分页
        items = all_items[params.offset:params.offset + params.limit]
        return PaginatedResult(
            items=list(items),
            total=total,
            page=params.page,
            page_size=params.page_size
        )
    
    # 获取数据
    paginated_query = query.offset(params.offset).limit(params.limit)
    result = await db.execute(paginated_query)
    items = result.scalars().all()
    
    return PaginatedResult(
        items=list(items),
        total=total,
        page=params.page,
        page_size=params.page_size
    )

