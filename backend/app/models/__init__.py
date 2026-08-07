"""数据模型汇总导出。

导入所有模型以便 Alembic 自动检测迁移变更，并方便其他模块统一引用。
"""

from app.core.database import Base
from app.models.ai_provider import AIProviderConfig
from app.models.feedback import Feedback, VisitLog
from app.models.interview import InterviewTip, QuestionBank, QuestionSource
from app.models.job import Favorite, Job, JobTag
from app.models.resume import Resume, ResumeUpload
from app.models.resume_template import ResumeAnalysis, ResumeTemplate
from app.models.user import OAuthAccount, User, UserProfile

__all__ = [
    "Base",
    "User",
    "UserProfile",
    "OAuthAccount",
    "AIProviderConfig",
    "Job",
    "JobTag",
    "Favorite",
    "Resume",
    "ResumeUpload",
    "ResumeTemplate",
    "ResumeAnalysis",
    "InterviewTip",
    "QuestionBank",
    "Feedback",
    "VisitLog",
]
