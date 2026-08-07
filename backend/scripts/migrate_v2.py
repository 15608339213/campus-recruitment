"""v2.1 数据库迁移脚本。

幂等执行，可安全重复运行：
1. 用 create_all 创建所有缺失的表（不会影响已存在的表）
2. 给 jobs 表追加 v2.1 新增字段（ALTER TABLE ADD COLUMN IF NOT EXISTS）
3. 给 question_bank 表追加新字段
4. 创建相关索引

运行方式：从 backend 目录执行
    python scripts/migrate_v2.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def migrate():
    from app.core.database import engine, Base
    # 导入所有模型，确保 Base.metadata 包含全部表定义
    from app.models import *  # noqa: F401, F403
    from sqlalchemy import text

    # ---- 1. 创建缺失的表 ----
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[1/4] 缺失的表已创建（已存在的表不受影响）")

    # ---- 2. jobs 表新增字段 ----
    alter_jobs = [
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS apply_url VARCHAR(512)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS apply_email VARCHAR(256)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS poster_url VARCHAR(512)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_verified BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_platform VARCHAR(64)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS view_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS apply_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS raw_data_json TEXT",
    ]

    # ---- 3. question_bank 表新增字段 ----
    alter_questions = [
        "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS question_type VARCHAR(32)",
        "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS difficulty VARCHAR(16)",
        "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS company VARCHAR(64)",
    ]

    async with engine.begin() as conn:
        for sql in alter_jobs:
            await conn.execute(text(sql))
        for sql in alter_questions:
            await conn.execute(text(sql))
    print("[2/4] jobs / question_bank 表新字段已就绪")

    # ---- 4. 索引 ----
    indexes = [
        "CREATE INDEX IF NOT EXISTS ix_jobs_source_verified ON jobs (source_verified)",
        "CREATE INDEX IF NOT EXISTS ix_jobs_view_count ON jobs (view_count)",
        "CREATE INDEX IF NOT EXISTS ix_question_bank_question_type ON question_bank (question_type)",
        "CREATE INDEX IF NOT EXISTS ix_question_bank_company ON question_bank (company)",
    ]
    async with engine.begin() as conn:
        for sql in indexes:
            await conn.execute(text(sql))
    print("[3/4] 索引已创建")

    # ---- 检查表数量 ----
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
            )
        )
        tables = [row[0] for row in result]
    print(f"[4/4] 当前数据库表：{', '.join(tables)}")

    print("\n迁移完成！可以继续运行 seed_templates.py 和 update_jobs_with_real_data.py")


if __name__ == "__main__":
    asyncio.run(migrate())
