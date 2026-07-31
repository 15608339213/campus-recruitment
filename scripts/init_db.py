"""数据库初始化脚本。

用法：
    python scripts/init_db.py

功能：
    1. 创建所有数据库表（基于 SQLAlchemy 模型）
    2. 插入管理员账号（admin@campus.com / admin123）
    3. 插入示例岗位数据
    4. 插入面试技巧初始数据

前置条件：
    - 已安装 backend/requirements.txt 中的依赖
    - 已配置数据库连接（backend/.env 或环境变量）
    - 如使用 PostgreSQL，需先通过 docker compose up -d postgres 启动数据库
"""

import asyncio
import os
import sys
from datetime import date, timedelta
from pathlib import Path

# ===== 路径与 .env 加载 =====
# 将 backend 目录加入 sys.path，以便导入 app 模块
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))


def _load_env_file(env_path: Path) -> None:
    """简单的 .env 文件加载器（不依赖 python-dotenv）。

    仅设置尚未在系统环境变量中存在的键，避免覆盖已有配置。
    """
    if not env_path.exists():
        print(f"[WARN] 未找到 .env 文件：{env_path}")
        print("       将使用 config.py 中的默认配置（SQLite）。")
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        # 跳过空行和注释
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


# 在导入 app 模块之前加载环境变量
_load_env_file(BACKEND_DIR / ".env")

# ===== 导入应用模块（此时 settings 会读取已加载的环境变量）=====
from sqlalchemy import select  # noqa: E402

from app.core.database import AsyncSessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import (  # noqa: E402
    Base,
    InterviewTip,
    Job,
    JobTag,
    User,
    UserProfile,
)

# ===== 导入所有模型，确保 create_all 能发现全部表 =====
from app.models import __all__ as _all_models  # noqa: E402, F401


async def create_tables() -> None:
    """创建所有数据库表。"""
    print("[1/4] 正在创建数据库表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("      数据库表创建完成。")


async def create_admin_user() -> User:
    """创建管理员账号。

    默认账号：admin@campus.com
    默认密码：admin123
    如已存在则跳过。
    """
    print("[2/4] 正在创建管理员账号...")
    async with AsyncSessionLocal() as session:
        # 检查是否已存在管理员
        result = await session.execute(
            select(User).where(User.email == "admin@campus.com")
        )
        existing = result.scalar_one_or_none()
        if existing:
            print("      管理员账号已存在，跳过创建。")
            return existing

        admin = User(
            email="admin@campus.com",
            password_hash=hash_password("admin123"),
            nickname="系统管理员",
            role="admin",
            is_active=True,
            is_verified=True,
        )
        session.add(admin)
        await session.flush()  # 获取 admin.id

        # 创建管理员档案
        profile = UserProfile(
            user_id=admin.id,
            school="管理员",
            bio="系统管理员账号",
        )
        session.add(profile)
        await session.commit()
        print("      管理员账号创建成功：admin@campus.com / admin123")
        return admin


async def create_sample_jobs() -> None:
    """插入示例岗位数据。"""
    print("[3/4] 正在插入示例岗位数据...")
    async with AsyncSessionLocal() as session:
        # 检查是否已有岗位数据
        result = await session.execute(select(Job).limit(1))
        if result.scalar_one_or_none():
            print("      已有岗位数据，跳过示例插入。")
            return

        today = date.today()
        sample_jobs = [
            {
                "title": "前端开发工程师（校招）",
                "company": "字节跳动",
                "company_type": "民企",
                "location": "北京",
                "salary_min": 18000,
                "salary_max": 35000,
                "salary_unit": "元/月",
                "start_date": today - timedelta(days=10),
                "end_date": today + timedelta(days=60),
                "job_category": "技术",
                "job_type": "校招",
                "degree_required": "本科",
                "description_html": "<p>负责公司核心产品的前端开发，使用 Vue/React 技术栈。</p>",
                "source_url": "https://example.com/job/1",
                "source_repo": "campus/jobs",
                "tags": ["六险一金", "免费三餐", "弹性工作", "补充医疗"],
            },
            {
                "title": "后端开发工程师（校招）",
                "company": "腾讯",
                "company_type": "民企",
                "location": "深圳",
                "salary_min": 20000,
                "salary_max": 40000,
                "salary_unit": "元/月",
                "start_date": today - timedelta(days=5),
                "end_date": today + timedelta(days=90),
                "job_category": "技术",
                "job_type": "校招",
                "degree_required": "本科",
                "description_html": "<p>负责后端服务设计与开发，使用 Go/Python 技术栈。</p>",
                "source_url": "https://example.com/job/2",
                "source_repo": "campus/jobs",
                "tags": ["六险一金", "年终奖", "股票期权", "免费班车"],
            },
            {
                "title": "产品经理（校招）",
                "company": "阿里巴巴",
                "company_type": "民企",
                "location": "杭州",
                "salary_min": 15000,
                "salary_max": 30000,
                "salary_unit": "元/月",
                "start_date": today - timedelta(days=15),
                "end_date": today + timedelta(days=45),
                "job_category": "产品",
                "job_type": "校招",
                "degree_required": "本科",
                "description_html": "<p>负责产品规划与需求分析，推动产品迭代优化。</p>",
                "source_url": "https://example.com/job/3",
                "source_repo": "campus/jobs",
                "tags": ["六险一金", "弹性工作", "年度体检"],
            },
            {
                "title": "算法工程师（校招）",
                "company": "百度",
                "company_type": "民企",
                "location": "北京",
                "salary_min": 25000,
                "salary_max": 45000,
                "salary_unit": "元/月",
                "start_date": today - timedelta(days=7),
                "end_date": today + timedelta(days=75),
                "job_category": "技术",
                "job_type": "校招",
                "degree_required": "硕士",
                "description_html": "<p>负责搜索/推荐/NLP 算法研发与优化。</p>",
                "source_url": "https://example.com/job/4",
                "source_repo": "campus/jobs",
                "tags": ["六险一金", "补充公积金", "科研经费"],
            },
            {
                "title": "运营专员（校招）",
                "company": "美团",
                "company_type": "民企",
                "location": "上海",
                "salary_min": 10000,
                "salary_max": 18000,
                "salary_unit": "元/月",
                "start_date": today - timedelta(days=3),
                "end_date": today + timedelta(days=50),
                "job_category": "运营",
                "job_type": "校招",
                "degree_required": "本科",
                "description_html": "<p>负责平台用户运营与活动策划。</p>",
                "source_url": "https://example.com/job/5",
                "source_repo": "campus/jobs",
                "tags": ["五险一金", "节日福利", "带薪年假"],
            },
        ]

        for job_data in sample_jobs:
            tags = job_data.pop("tags", [])
            job = Job(**job_data)
            session.add(job)
            await session.flush()
            for tag_name in tags:
                session.add(JobTag(job_id=job.id, tag=tag_name))

        await session.commit()
        print(f"      已插入 {len(sample_jobs)} 条示例岗位数据。")


async def create_interview_tips() -> None:
    """插入面试技巧初始数据。"""
    print("[4/4] 正在插入面试技巧数据...")
    async with AsyncSessionLocal() as session:
        # 检查是否已有技巧数据
        result = await session.execute(select(InterviewTip).limit(1))
        if result.scalar_one_or_none():
            print("      已有面试技巧数据，跳过插入。")
            return

        tips = [
            {
                "job_category": "技术",
                "content_markdown": (
                    "## 技术岗面试技巧\n\n"
                    "1. **扎实的基础知识**：数据结构与算法是重中之重，"
                    "建议刷 LeetCode 中等难度 100 题以上。\n"
                    "2. **项目经验**：准备 2-3 个有深度的项目，"
                    "能说清楚技术选型、难点与解决方案。\n"
                    "3. **系统设计**：了解常见架构模式，"
                    "如微服务、缓存策略、消息队列等。\n"
                    "4. **编码规范**：面试中注意代码可读性，"
                    "变量命名规范，边界条件处理。\n"
                    "5. **沟通表达**：遇到不会的问题不要慌，"
                    "说出思路比沉默更好。"
                ),
            },
            {
                "job_category": "产品",
                "content_markdown": (
                    "## 产品岗面试技巧\n\n"
                    "1. **产品思维**：理解用户需求，"
                    "能从用户场景出发分析问题。\n"
                    "2. **数据分析**：掌握基本的数据分析方法，"
                    "能通过数据论证产品决策。\n"
                    "3. **竞品分析**：了解目标公司的主要产品，"
                    "能说出优缺点和改进方向。\n"
                    "4. **项目经验**：准备有完整闭环的产品案例，"
                    "从调研到上线到迭代。\n"
                    "5. **逻辑表达**：回答问题要有条理，"
                    "使用 STAR 法则组织回答。"
                ),
            },
            {
                "job_category": "运营",
                "content_markdown": (
                    "## 运营岗面试技巧\n\n"
                    "1. **用户洞察**：了解目标用户群体特征，"
                    "能提出有效的运营策略。\n"
                    "2. **活动策划**：准备 1-2 个活动策划方案，"
                    "包含目标、流程、预算和预期效果。\n"
                    "3. **数据驱动**：关注核心指标（DAU、留存率、转化率），"
                    "用数据指导运营决策。\n"
                    "4. **内容能力**：具备文案撰写和内容策划能力。\n"
                    "5. **执行力**：运营是细节活，"
                    "面试中展示你的执行力和责任心。"
                ),
            },
            {
                "job_category": "金融",
                "content_markdown": (
                    "## 金融岗面试技巧\n\n"
                    "1. **专业知识**：掌握财务分析、估值模型、"
                    "行业研究等核心技能。\n"
                    "2. **市场认知**：关注宏观经济和行业动态，"
                    "能对热点事件进行深度分析。\n"
                    "3. **案例分析**：练习 case interview，"
                    "提升结构化思维能力。\n"
                    "4. **实习经历**：相关实习经历是重要加分项，"
                    "重点准备经历中的关键贡献。\n"
                    "5. **职业规划**：清晰的职业发展路径，"
                    "展示对行业的长期热情。"
                ),
            },
        ]

        for tip_data in tips:
            session.add(InterviewTip(**tip_data))

        await session.commit()
        print(f"      已插入 {len(tips)} 条面试技巧数据。")


async def main() -> None:
    """初始化数据库主流程。"""
    print("=" * 60)
    print("  秋招助手 - 数据库初始化脚本")
    print("=" * 60)

    try:
        await create_tables()
        await create_admin_user()
        await create_sample_jobs()
        await create_interview_tips()
        print("\n[完成] 数据库初始化成功！")
        print("  管理员账号：admin@campus.com")
        print("  管理员密码：admin123")
        print("  （请及时修改默认密码）")
    except Exception as e:
        print(f"\n[错误] 初始化失败：{e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()
        print("\n数据库连接已关闭。")


if __name__ == "__main__":
    asyncio.run(main())
