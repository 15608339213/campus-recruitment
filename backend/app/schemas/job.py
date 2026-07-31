from __future__ import annotations
"""岗位相关的 Pydantic Schema。"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any, Any

from pydantic import BaseModel, ConfigDict, Field


class JobTagResponse(BaseModel):
    """岗位标签响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tag: str


class JobBase(BaseModel):
    """岗位基础字段。"""

    title: str
    company: str
    company_type: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_unit: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    job_category: Optional[str] = None
    job_type: Optional[str] = None
    degree_required: Optional[str] = None
    description_html: Optional[str] = None
    source_url: Optional[str] = None
    source_repo: Optional[str] = None


class JobCreate(JobBase):
    """创建岗位请求（爬虫 / 管理员手动添加）。"""

    raw_data_json: Optional[Any] = None
    tags: List[str] = Field(default_factory=list, description="岗位标签列表")


class JobResponse(JobBase):
    """岗位详情响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    tags: List[JobTagResponse] = Field(default_factory=list)
    is_favorited: bool = Field(False, description="当前用户是否已收藏")


class JobFilter(BaseModel):
    """岗位筛选条件（查询参数）。所有字段可选。"""

    keyword: Optional[str] = Field(None, description="搜索关键词（标题/公司）")
    company_type: Optional[str] = None
    location: Optional[str] = None
    job_category: Optional[str] = None
    job_type: Optional[str] = None
    degree_required: Optional[str] = None
    salary_min: Optional[int] = Field(None, ge=0, description="薪资下限")
    salary_max: Optional[int] = Field(None, ge=0, description="薪资上限")
    tag: Optional[str] = Field(None, description="标签筛选")
    is_active: Optional[bool] = True
    # 排序：latest / salary_desc / end_date_asc / deadline
    sort_by: str = Field("latest", description="排序方式")
    skip: int = Field(0, ge=0, description="分页偏移量")
    limit: int = Field(20, ge=1, le=100, description="每页数量")


class JobListResponse(BaseModel):
    """岗位列表分页响应。"""

    items: List[JobResponse]
    total: int
    skip: int
    limit: int


class FavoriteResponse(BaseModel):
    """收藏响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    note: Optional[str] = None
    created_at: datetime
    job: Optional[JobResponse] = None


class FavoriteListResponse(BaseModel):
    """收藏列表分页响应。"""

    items: List[FavoriteResponse]
    total: int
    skip: int
    limit: int


class FavoriteNoteUpdate(BaseModel):
    """更新收藏备注。"""

    note: Optional[str] = Field(None, max_length=500)
