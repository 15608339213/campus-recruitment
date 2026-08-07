from __future__ import annotations
from typing import Optional, List
"""面试技巧与题库相关的 Pydantic Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InterviewTipResponse(BaseModel):
    """面试技巧响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_category: str
    content_markdown: str
    updated_at: datetime


class InterviewTipListResponse(BaseModel):
    """面试技巧列表响应。"""

    items: List[InterviewTipResponse]
    total: int


class QuestionBankResponse(BaseModel):
    """题库题目响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_category: str
    question: str
    answer: Optional[str] = None
    question_type: Optional[str] = None
    difficulty: Optional[str] = None
    source: Optional[str] = None
    updated_at: datetime


class QuestionBankListResponse(BaseModel):
    """题库列表分页响应。"""

    items: List[QuestionBankResponse]
    total: int
    skip: int
    limit: int


class QuestionBankCreate(BaseModel):
    """创建题目请求（管理员）。"""

    job_category: str
    question: str
    answer: Optional[str] = None
    question_type: Optional[str] = None
    difficulty: Optional[str] = None
    source: Optional[str] = None


class QuestionBankUpdate(BaseModel):
    """更新题目请求（管理员），所有字段可选。"""

    job_category: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    question_type: Optional[str] = None
    difficulty: Optional[str] = None
    source: Optional[str] = None


class QuestionBankBatchCreate(BaseModel):
    """批量导入题目请求（管理员）。"""

    items: List[QuestionBankCreate]


class InterviewTipCreate(BaseModel):
    """创建/更新面试技巧请求（管理员）。"""

    job_category: str
    content_markdown: str
