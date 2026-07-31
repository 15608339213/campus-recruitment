"""秋招爬虫入口脚本。

职责:
    1. 读取环境变量 ``DATABASE_URL`` / ``DEEPSEEK_API_KEY`` / ``GITHUB_TOKEN``。
    2. 调用各数据源适配器（GitHub 仓库 + 企业官网）抓取原始岗位。
    3. 运行数据清洗管线（:mod:`pipeline`）：清洗、解析、去重。
    4. （可选）使用 DeepSeek API 对岗位描述做标签增强。
    5. 将结果写入数据库（对齐后端 ``jobs`` / ``job_tags`` 表）；
       若未配置数据库则输出 JSON 落盘。
    6. 输出运行日志到 ``crawler/logs/``。

用法::

    # 设置环境变量后运行
    set DATABASE_URL=sqlite+aiosqlite:///./campus_recruit.db
    set DEEPSEEK_API_KEY=sk-xxxx
    python run.py

    # 也可通过命令行参数指定数据源
    python run.py --no-github --no-companies --output result.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime
from typing import Any

# 确保以脚本所在目录为包根，支持 `python run.py` 直接运行
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

from pipeline import clean_jobs, deduplicate  # noqa: E402
from sources.github_repos import DEFAULT_REPOS, GitHubRepoSource  # noqa: E402
from adapters import ALL_ADAPTERS  # noqa: E402

LOG_DIR = os.path.join(_BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("crawler")


# ====================================================================== #
# 日志配置
# ====================================================================== #
def setup_logging(verbose: bool = False) -> str:
    """配置日志，同时输出到文件与控制台，返回日志文件路径。"""
    log_file = os.path.join(LOG_DIR, f"crawler_{datetime.now():%Y%m%d}.log")
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    # 清理已存在的 handler，避免重复输出
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return log_file


# ====================================================================== #
# 数据抓取
# ====================================================================== #
async def gather_github(repos: list[str] | None = None) -> list[dict]:
    """抓取 GitHub 开源校招仓库。"""
    repos = repos or DEFAULT_REPOS
    source = GitHubRepoSource()
    all_jobs: list[dict] = []
    try:
        for repo in repos:
            try:
                jobs = await source.fetch_repo_data(repo)
                all_jobs.extend(jobs)
            except Exception as exc:  # noqa: BLE001
                logger.error("GitHub 仓库 %s 抓取失败: %s", repo, exc)
    finally:
        await source.close()
    logger.info("GitHub 数据源共抓取 %d 个岗位", len(all_jobs))
    return all_jobs


async def gather_companies() -> list[dict]:
    """抓取各企业官网校招岗位。"""
    all_jobs: list[dict] = []
    for adapter_cls in ALL_ADAPTERS:
        adapter = adapter_cls()
        try:
            async with adapter:
                jobs = await adapter.fetch_jobs()
                all_jobs.extend(jobs)
                logger.info(
                    "[%s] 抓取完成: %d 个岗位", adapter.company_name, len(jobs)
                )
        except Exception as exc:  # noqa: BLE001
            logger.error("适配器 %s 运行失败: %s", adapter_cls.__name__, exc)
    logger.info("企业官网数据源共抓取 %d 个岗位", len(all_jobs))
    return all_jobs


# ====================================================================== #
# DeepSeek 标签增强（可选）
# ====================================================================== #
async def enrich_with_llm(jobs: list[dict], api_key: str) -> list[dict]:
    """使用 DeepSeek API 为岗位补充技能标签。

    无 API Key 时直接返回原列表；调用失败时跳过该岗位，不影响整体流程。
    """
    if not api_key:
        logger.info("未配置 DEEPSEEK_API_KEY，跳过 LLM 标签增强")
        return jobs

    import httpx  # 局部导入，避免无网络环境加载失败

    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    url = f"{base_url}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    enriched = 0
    async with httpx.AsyncClient(timeout=60) as client:
        for job in jobs:
            desc = job.get("description") or job.get("requirement") or ""
            if not desc:
                continue
            try:
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "你是招聘信息分析助手。请从岗位描述中提取 3-8 个"
                                "技能或岗位标签，仅以 JSON 字符串数组形式返回，"
                                '如 ["Python","机器学习"]。'
                            ),
                        },
                        {"role": "user", "content": desc[:1500]},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 256,
                }
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                m = re.search(r"\[.*?\]", content, re.S)
                if not m:
                    continue
                new_tags = json.loads(m.group(0))
                if isinstance(new_tags, list):
                    existing = set(job.get("tags", []))
                    for t in new_tags:
                        t = str(t).strip()
                        if t and t not in existing:
                            job["tags"].append(t)
                            existing.add(t)
                    enriched += 1
            except Exception as exc:  # noqa: BLE001
                logger.debug("LLM 增强失败 [%s]: %s", job.get("title", ""), exc)
            # 礼貌限速
            await asyncio.sleep(0.4)

    logger.info("DeepSeek LLM 增强 %d 个岗位", enriched)
    return jobs


# ====================================================================== #
# 数据库写入（对齐后端 jobs / job_tags 表）
# ====================================================================== #
def _to_sync_url(db_url: str) -> str:
    """将异步 DATABASE_URL 转为同步驱动 URL，供爬虫写入使用。"""
    if "+aiosqlite" in db_url:
        return db_url.replace("+aiosqlite", "")
    if "+asyncpg" in db_url:
        return db_url.replace("+asyncpg", "+psycopg2")
    return db_url


def _build_tables(meta):
    """定义与后端一致的 jobs / job_tags 表结构（SQLAlchemy Core）。"""
    from sqlalchemy import (
        Boolean,
        Column,
        Date,
        DateTime,
        ForeignKey,
        Integer,
        String,
        Table,
        Text,
        func,
    )

    jobs = Table(
        "jobs",
        meta,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("title", String(256), nullable=False, index=True),
        Column("company", String(256), nullable=False, index=True),
        Column("company_type", String(32), nullable=True, index=True),
        Column("location", String(128), nullable=True, index=True),
        Column("salary_min", Integer, nullable=True),
        Column("salary_max", Integer, nullable=True),
        Column("salary_unit", String(16), nullable=True),
        Column("start_date", Date, nullable=True),
        Column("end_date", Date, nullable=True, index=True),
        Column("job_category", String(64), nullable=True, index=True),
        Column("job_type", String(32), nullable=True, index=True),
        Column("degree_required", String(32), nullable=True),
        Column("description_html", Text, nullable=True),
        Column("source_url", String(512), nullable=True),
        Column("source_repo", String(256), nullable=True),
        Column("raw_data_json", Text, nullable=True),
        Column("is_active", Boolean, default=True, nullable=False, index=True),
        Column("created_at", DateTime, server_default=func.now(), nullable=False),
        Column("updated_at", DateTime, server_default=func.now(), nullable=False),
    )
    job_tags = Table(
        "job_tags",
        meta,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("job_id", Integer, ForeignKey("jobs.id", ondelete="CASCADE"),
               nullable=False, index=True),
        Column("tag", String(64), nullable=False, index=True),
    )
    return jobs, job_tags


def write_to_database(jobs: list[dict], db_url: str) -> None:
    """将岗位写入数据库（按 title+company+location 做软 upsert）。

    若未安装 SQLAlchemy，则回退到 JSON 落盘。
    """
    try:
        from sqlalchemy import MetaData, and_, create_engine, delete, insert
    except ImportError:
        logger.warning("未安装 SQLAlchemy，改为输出 JSON 文件")
        write_json(jobs)
        return

    sync_url = _to_sync_url(db_url)
    logger.info("数据库写入目标: %s", _mask_url(sync_url))
    engine = create_engine(sync_url)
    meta = MetaData()
    jobs_tbl, tags_tbl = _build_tables(meta)

    with engine.begin() as conn:
        meta.create_all(conn, tables=[jobs_tbl, tags_tbl])
        inserted = 0
        updated = 0
        for job in jobs:
            title = job.get("title", "")
            company = job.get("company", "")
            location = job.get("location", "") or None
            if not title or not company:
                continue

            # 序列化字段
            raw_data_json = json.dumps(
                {
                    "tags": job.get("tags", []),
                    "raw_data": job.get("raw_data", {}),
                    "salary_raw": job.get("salary_raw", ""),
                    "deadline_raw": job.get("deadline_raw", ""),
                    "requirement": job.get("requirement", ""),
                    "job_hash": job.get("job_hash", ""),
                    "source": job.get("source", ""),
                },
                ensure_ascii=False,
            )
            end_date = _parse_date_obj(job.get("deadline", ""))

            # 查询是否已存在（按 title + company 匹配）
            # 使用 and_() 组合多条件，兼容 SQLAlchemy 1.4 与 2.0
            stmt = jobs_tbl.select().where(
                and_(
                    jobs_tbl.c.title == title,
                    jobs_tbl.c.company == company,
                )
            )
            existing_id = conn.execute(stmt).scalar()

            values = {
                "title": title,
                "company": company,
                "company_type": job.get("company_type") or None,
                "location": location,
                "salary_min": job.get("salary_min") or None,
                "salary_max": job.get("salary_max") or None,
                "salary_unit": job.get("salary_unit") or None,
                "end_date": end_date,
                "job_category": job.get("job_category") or None,
                "job_type": job.get("job_type") or "校招",
                "degree_required": job.get("education") or None,
                "description_html": job.get("description") or None,
                "source_url": job.get("url") or None,
                "source_repo": job.get("source_repo") or job.get("source") or None,
                "raw_data_json": raw_data_json,
                "is_active": True,
                "updated_at": datetime.now(),
            }

            if existing_id:
                # 更新已有记录
                conn.execute(
                    jobs_tbl.update()
                    .where(jobs_tbl.c.id == existing_id)
                    .values(**values)
                )
                job_id = existing_id
                # 清理旧标签后重建
                conn.execute(delete(tags_tbl).where(tags_tbl.c.job_id == job_id))
                updated += 1
            else:
                result = conn.execute(insert(jobs_tbl).values(**values))
                job_id = result.inserted_primary_key[0]
                inserted += 1

            # 写入标签
            for tag in job.get("tags", []):
                conn.execute(
                    insert(tags_tbl).values(job_id=job_id, tag=str(tag)[:64])
                )

    logger.info("数据库写入完成: 新增 %d, 更新 %d", inserted, updated)


def _parse_date_obj(date_str: str):
    """将 YYYY-MM-DD 字符串转为 date 对象，失败返回 None。"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _mask_url(url: str) -> str:
    """隐藏 URL 中的密码，用于日志输出。"""
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", url)


def write_json(jobs: list[dict], output: str | None = None) -> str:
    """将岗位以 JSON 落盘，返回文件路径。"""
    if output:
        path = output
    else:
        path = os.path.join(LOG_DIR, f"jobs_{datetime.now():%Y%m%d_%H%M%S}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(jobs, fh, ensure_ascii=False, indent=2, default=str)
    logger.info("岗位数据已写入 JSON: %s", path)
    return path


# ====================================================================== #
# 主流程
# ====================================================================== #
async def run(args: argparse.Namespace) -> int:
    log_file = setup_logging(verbose=args.verbose)
    logger.info("=" * 60)
    logger.info("秋招爬虫启动 @ %s", datetime.now().isoformat(timespec="seconds"))
    logger.info("日志文件: %s", log_file)

    db_url = os.environ.get("DATABASE_URL", "").strip()
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    logger.info(
        "配置: DATABASE_URL=%s, DEEPSEEK_API_KEY=%s",
        "已设置" if db_url else "未设置",
        "已设置" if api_key else "未设置",
    )

    # 1) 抓取
    raw_jobs: list[dict] = []
    if not args.no_github:
        raw_jobs.extend(await gather_github(args.repos or None))
    if not args.no_companies:
        raw_jobs.extend(await gather_companies())
    logger.info("原始岗位合计: %d", len(raw_jobs))

    if not raw_jobs:
        logger.warning("未抓取到任何岗位，流程结束")
        return 1

    # 2) 清洗 + 去重
    cleaned = clean_jobs(raw_jobs)
    final = deduplicate(cleaned)

    # 3) LLM 增强（可选）
    if api_key and not args.no_llm:
        final = await enrich_with_llm(final, api_key)

    # 4) 输出 / 持久化
    if db_url and not args.json_only:
        try:
            write_to_database(final, db_url)
        except Exception as exc:  # noqa: BLE001
            logger.error("数据库写入失败，回退到 JSON: %s", exc)
            write_json(final, args.output)
    else:
        write_json(final, args.output)

    # 摘要
    logger.info("-" * 60)
    logger.info("运行摘要: 原始=%d, 清洗=%d, 去重=%d", len(raw_jobs), len(cleaned), len(final))
    by_source: dict[str, int] = {}
    for j in final:
        src = j.get("source") or "未知"
        by_source[src] = by_source.get(src, 0) + 1
    for src, cnt in sorted(by_source.items(), key=lambda x: -x[1]):
        logger.info("  来源 %-24s %d 条", src, cnt)
    logger.info("爬虫运行完成")
    logger.info("=" * 60)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="秋招爬虫入口")
    parser.add_argument(
        "--no-github", action="store_true", help="跳过 GitHub 仓库数据源"
    )
    parser.add_argument(
        "--no-companies", action="store_true", help="跳过企业官网数据源"
    )
    parser.add_argument(
        "--no-llm", action="store_true", help="跳过 DeepSeek LLM 标签增强"
    )
    parser.add_argument(
        "--json-only", action="store_true", help="仅输出 JSON，不写数据库"
    )
    parser.add_argument(
        "--repos", nargs="*", help="自定义 GitHub 仓库列表（owner/repo）"
    )
    parser.add_argument(
        "--output", "-o", help="JSON 输出文件路径（默认 logs/ 目录）"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="输出 DEBUG 级别日志"
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    exit_code = asyncio.run(run(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
