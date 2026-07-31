"""Pydantic Schema 汇总导出。"""

from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackListResponse,
    FeedbackReply,
    FeedbackResponse,
)
from app.schemas.interview import (
    InterviewTipCreate,
    InterviewTipListResponse,
    InterviewTipResponse,
    QuestionBankCreate,
    QuestionBankListResponse,
    QuestionBankResponse,
)
from app.schemas.job import (
    FavoriteListResponse,
    FavoriteNoteUpdate,
    FavoriteResponse,
    JobCreate,
    JobFilter,
    JobListResponse,
    JobResponse,
    JobTagResponse,
)
from app.schemas.resume import (
    ResumeContent,
    ResumeGenerate,
    ResumeListResponse,
    ResumeResponse,
)
from app.schemas.user import (
    MessageResponse,
    RefreshResponse,
    Token,
    TokenData,
    UserCreate,
    UserLogin,
    UserProfileResponse,
    UserProfileUpdate,
    UserResponse,
    VerifyEmailRequest,
)

__all__ = [
    # user
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserProfileUpdate",
    "UserProfileResponse",
    "Token",
    "TokenData",
    "RefreshResponse",
    "VerifyEmailRequest",
    "MessageResponse",
    # job
    "JobResponse",
    "JobListResponse",
    "JobFilter",
    "JobCreate",
    "JobTagResponse",
    "FavoriteResponse",
    "FavoriteListResponse",
    "FavoriteNoteUpdate",
    # resume
    "ResumeGenerate",
    "ResumeResponse",
    "ResumeListResponse",
    "ResumeContent",
    # feedback
    "FeedbackCreate",
    "FeedbackResponse",
    "FeedbackListResponse",
    "FeedbackReply",
    # interview
    "InterviewTipResponse",
    "InterviewTipListResponse",
    "InterviewTipCreate",
    "QuestionBankResponse",
    "QuestionBankListResponse",
    "QuestionBankCreate",
]
