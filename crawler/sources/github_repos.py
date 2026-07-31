"""GitHub 开源校招仓库数据源。

从社区维护的校招信息仓库抓取招聘信息，支持 Markdown（README 表格/列表）
与 JSON 两种格式。使用 GitHub REST API（api.github.com）获取仓库内容，
并对 API 速率限制做礼貌处理。

支持的仓库示例:
    - NowPull/CampusRecruitment
    - wfcnhr/2024-campus
    - Internship52/CampusRecruitment
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
GITHUB_TOKEN_ENV = "GITHUB_TOKEN"

#: 默认抓取的校招仓库（社区维护的校招信息汇总仓库）
DEFAULT_REPOS: list[str] = [
    # 原有仓库
    "NowPull/CampusRecruitment",
    "wfcnhr/2024-campus",
    "Internship52/CampusRecruitment",
    # 新增社区校招仓库
    "ShameCom/339.349",
    "forthespada/InterviewGuide",
    "doocs/coding-interview",
    "CyC2018/CS-Notes",
    "qaz2291818/Campus-Recruitment",
    "rongweihe/Campus_Recruitment",
    "Wsl1527329541/Campus-recruitment",
    "virgithub/CampusRecruitment",
    "dyc87112/CampusRecruitment",
    "jobbole/awesome-programming-books",
]


@dataclass
class GitHubRepoSource:
    """GitHub 仓库数据源（dataclass 定义数据结构）。

    Attributes:
        token: GitHub Personal Access Token，提升 API 速率限制额度。
            未提供时自动读取环境变量 ``GITHUB_TOKEN``。
        request_interval: 两次 API 请求的最小间隔（秒）。
        timeout: 单次请求超时（秒）。
        max_subdir_depth: 扫描 JSON 文件时递归子目录的最大深度。
    """

    token: Optional[str] = None
    request_interval: float = 1.0
    timeout: float = 30.0
    max_subdir_depth: int = 1
    user_agent: str = "QiuZhaoBot/1.0 (AutumnRecruitmentCrawler)"

    def __post_init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_ts: float = 0.0

    # ------------------------------------------------------------------ #
    # 客户端与速率限制
    # ------------------------------------------------------------------ #
    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            token = self.token or os.environ.get(GITHUB_TOKEN_ENV)
            if token:
                headers["Authorization"] = f"Bearer {token}"
            self._client = httpx.AsyncClient(
                headers=headers, timeout=self.timeout, follow_redirects=True
            )
        return self._client

    async def _rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_ts
        if elapsed < self.request_interval:
            await asyncio.sleep(self.request_interval - elapsed)
        self._last_request_ts = time.monotonic()

    async def _api_get(self, path: str, **kwargs: Any) -> httpx.Response:
        """带速率限制与 403 rate-limit 处理的 GitHub API GET。"""
        await self._rate_limit()
        client = await self._ensure_client()
        url = path if path.startswith("http") else f"{GITHUB_API}{path}"

        for attempt in range(2):
            resp = await client.get(url, **kwargs)
            # 处理二级速率限制（403 + rate limit remaining=0）
            if resp.status_code == 403:
                remaining = resp.headers.get("X-RateLimit-Remaining")
                reset_ts = resp.headers.get("X-RateLimit-Reset")
                if remaining == "0" and reset_ts:
                    wait = max(int(reset_ts) - int(time.time()), 1)
                    wait = min(wait, 60)  # 最多等 60 秒，避免长时间阻塞
                    logger.warning(
                        "GitHub API 速率限制触发，等待 %d 秒后重试", wait
                    )
                    await asyncio.sleep(wait)
                    continue
            resp.raise_for_status()
            return resp
        resp.raise_for_status()
        return resp

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    # ------------------------------------------------------------------ #
    # 公开接口
    # ------------------------------------------------------------------ #
    async def fetch_repo_data(self, repo_url: str) -> list[dict]:
        """获取指定仓库的校招数据。

        Args:
            repo_url: 仓库标识，支持 ``owner/repo`` 或完整 HTTPS URL。

        Returns:
            原始 job dict 列表。
        """
        owner, repo = self._parse_repo(repo_url)
        logger.info("开始抓取 GitHub 仓库 %s/%s", owner, repo)
        jobs: list[dict] = []
        source_tag = f"github:{owner}/{repo}"

        # 1) 从 README（Markdown）抓取
        try:
            readme_jobs = await self._fetch_from_readme(owner, repo, source_tag)
            jobs.extend(readme_jobs)
            logger.info("  README 解析得到 %d 条", len(readme_jobs))
        except Exception as exc:  # noqa: BLE001
            logger.warning("读取 %s/%s README 失败: %s", owner, repo, exc)

        # 2) 扫描仓库内 JSON 文件抓取
        try:
            json_jobs = await self._fetch_from_json_files(owner, repo, source_tag)
            jobs.extend(json_jobs)
            logger.info("  JSON 文件解析得到 %d 条", len(json_jobs))
        except Exception as exc:  # noqa: BLE001
            logger.warning("扫描 %s/%s JSON 文件失败: %s", owner, repo, exc)

        logger.info("GitHub %s/%s 共抓取 %d 条", owner, repo, len(jobs))
        return jobs

    async def fetch_all(self, repos: Optional[list[str]] = None) -> list[dict]:
        """批量抓取多个仓库的数据。"""
        repos = repos or DEFAULT_REPOS
        all_jobs: list[dict] = []
        for repo in repos:
            try:
                all_jobs.extend(await self.fetch_repo_data(repo))
            except Exception as exc:  # noqa: BLE001
                logger.error("仓库 %s 抓取失败: %s", repo, exc)
        return all_jobs

    # ------------------------------------------------------------------ #
    # 仓库标识解析
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_repo(repo_url: str) -> tuple[str, str]:
        repo_url = repo_url.strip().rstrip("/")
        if repo_url.startswith("http"):
            parts = [p for p in repo_url.split("/") if p]
            # https://github.com/owner/repo -> ... ['github.com','owner','repo']
            if len(parts) >= 3:
                return parts[-2], parts[-1]
            raise ValueError(f"无法解析仓库 URL: {repo_url}")
        if "/" in repo_url:
            owner, repo = repo_url.split("/", 1)
            return owner.strip(), repo.strip()
        raise ValueError(f"无法解析仓库标识: {repo_url}")

    # ------------------------------------------------------------------ #
    # README / Markdown 解析
    # ------------------------------------------------------------------ #
    async def _fetch_from_readme(
        self, owner: str, repo: str, source: str
    ) -> list[dict]:
        resp = await self._api_get(f"/repos/{owner}/{repo}/readme")
        data = resp.json()
        content_b64 = data.get("content", "")
        encoding = data.get("encoding", "base64")
        if encoding == "base64" and content_b64:
            content = base64.b64decode(content_b64).decode("utf-8", errors="ignore")
        else:
            content = content_b64

        # 优先使用 markdown 库转 HTML 再用 BS 解析，失败则直接按文本解析
        try:
            import markdown as md  # type: ignore

            html = md.markdown(content, extensions=["tables", "fenced_code"])
            soup = BeautifulSoup(html, "lxml")
            return self._parse_markdown_soup(soup, content, source)
        except ImportError:
            logger.debug("未安装 markdown 库，使用纯文本/BS 解析 README")
            soup = BeautifulSoup(content, "lxml")
            return self._parse_markdown_soup(soup, content, source)

    def _parse_markdown_soup(
        self, soup: BeautifulSoup, raw_text: str, source: str
    ) -> list[dict]:
        jobs: list[dict] = []

        # (a) Markdown 表格 -> HTML <table>
        for table in soup.find_all("table"):
            jobs.extend(self._parse_table(table, source))
        if jobs:
            return jobs

        # (b) 列表项 <li>，常见格式: - 公司 | 岗位 | 地点 | 链接
        for li in soup.find_all("li"):
            text = li.get_text(" ", strip=True)
            if not text:
                continue
            job = self._parse_line(text, source)
            if job:
                a = li.find("a", href=True)
                if a and not job["url"]:
                    job["url"] = a["href"]
                jobs.append(job)
        if jobs:
            return jobs

        # (c) 逐行解析原始 Markdown 文本
        for line in raw_text.splitlines():
            job = self._parse_line(line, source)
            if job:
                jobs.append(job)
        return jobs

    def _parse_table(self, table, source: str) -> list[dict]:
        jobs: list[dict] = []
        rows = table.find_all("tr")
        if not rows:
            return jobs
        header_cells = [
            c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])
        ]
        col_map = self._build_col_map(header_cells)
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            values = [c.get_text(" ", strip=True) for c in cells]
            link = ""
            a = row.find("a", href=True)
            if a:
                link = a["href"]
            job = self._row_to_job(values, col_map, header_cells, source, link)
            if job:
                jobs.append(job)
        return jobs

    @staticmethod
    def _build_col_map(headers: list[str]) -> dict[str, int]:
        col_map: dict[str, int] = {}
        for i, h in enumerate(headers):
            hl = h.lower()
            if any(k in hl for k in ("公司", "企业", "company", "单位")):
                col_map["company"] = i
            elif any(k in hl for k in ("岗位", "职位", "position", "job", "名称")):
                col_map["title"] = i
            elif any(k in hl for k in ("地点", "城市", "location", "city", "工作地")):
                col_map["location"] = i
            elif any(k in hl for k in ("薪资", "salary", "待遇")):
                col_map["salary"] = i
            elif any(k in hl for k in ("链接", "网址", "url", "link", "投递", "详情")):
                col_map["url"] = i
            elif any(k in hl for k in ("截止", "deadline", "时间", "日期")):
                col_map["deadline"] = i
            elif any(k in hl for k in ("学历", "education", "degree")):
                col_map["education"] = i
            elif any(k in hl for k in ("类型", "category", "方向", "类别")):
                col_map["category"] = i
            elif any(k in hl for k in ("要求", "描述", "desc", "detail", "备注")):
                col_map["description"] = i
        return col_map

    def _row_to_job(
        self,
        values: list[str],
        col_map: dict[str, int],
        headers: list[str],
        source: str,
        link: str,
    ) -> dict | None:
        def get(key: str) -> str:
            idx = col_map.get(key)
            if idx is None or idx >= len(values):
                return ""
            return values[idx]

        company = get("company")
        title = get("title")
        if not company and not title:
            return None

        return {
            "title": title or "校招岗位",
            "company": company,
            "company_type": "",
            "location": get("location"),
            "salary_raw": get("salary"),
            "description": get("description"),
            "deadline": get("deadline"),
            "education": get("education"),
            "job_category": get("category"),
            "url": link or get("url"),
            "source": source,
            "source_repo": source,
            "raw_data": {"headers": headers, "values": values},
        }

    def _parse_line(self, text: str, source: str) -> dict | None:
        """解析单行文本，启发式提取公司/岗位/地点。

        支持用 ``|`` ``-`` ``—`` ``–`` ``/`` ``\t`` 分隔的多列格式。
        """
        text = text.strip()
        if not text:
            return None
        # 跳过 Markdown 标题、分隔线、空表头
        if text.startswith("#"):
            return None
        if re.match(r"^[\|\-\s:]+$", text):  # 表格分隔行 |---|---|
            return None

        # 去掉 Markdown 列表前缀
        text = re.sub(r"^[-*+]\s+", "", text)
        text = re.sub(r"^\d+\.\s+", "", text)

        # 用竖线或制表符分隔（表格行），或用破折号分隔
        if "|" in text:
            parts = [p.strip() for p in text.split("|") if p.strip()]
        elif "\t" in text:
            parts = [p.strip() for p in text.split("\t") if p.strip()]
        elif re.search(r"\s[-–—]\s", text):
            parts = [p.strip() for p in re.split(r"\s[-–—]\s", text) if p.strip()]
        else:
            parts = [p.strip() for p in re.split(r"\s{2,}", text) if p.strip()]

        if len(parts) < 2:
            return None

        # 启发式：第一列多为公司，第二列为岗位，第三列为地点
        company = parts[0]
        title = parts[1] if len(parts) > 1 else ""
        location = parts[2] if len(parts) > 2 else ""

        # 提取行内链接 [text](url)
        url = ""
        m = re.search(r"\[([^\]]*)\]\((https?://[^\s)]+)\)", text)
        if m:
            url = m.group(2)

        return {
            "title": title or "校招岗位",
            "company": company,
            "company_type": "",
            "location": location,
            "salary_raw": "",
            "description": text,
            "deadline": "",
            "education": "",
            "job_category": "",
            "url": url,
            "source": source,
            "source_repo": source,
            "raw_data": {"line": text},
        }

    # ------------------------------------------------------------------ #
    # JSON 文件扫描与解析
    # ------------------------------------------------------------------ #
    async def _fetch_from_json_files(
        self, owner: str, repo: str, source: str
    ) -> list[dict]:
        jobs: list[dict] = []
        resp = await self._api_get(f"/repos/{owner}/{repo}/contents")
        items = resp.json()
        if not isinstance(items, list):
            return jobs

        json_paths = await self._find_json_files(owner, repo, items, depth=0)
        logger.debug("在 %s/%s 找到 %d 个 JSON 文件", owner, repo, len(json_paths))

        for path in json_paths:
            try:
                raw_resp = await self._api_get(
                    f"/repos/{owner}/{repo}/contents/{path}"
                )
                file_data = raw_resp.json()
                content_b64 = file_data.get("content", "")
                content = base64.b64decode(content_b64).decode(
                    "utf-8", errors="ignore"
                )
                parsed = json.loads(content)
                jobs.extend(
                    self._parse_json(parsed, source=f"{source}/{path}")
                )
            except json.JSONDecodeError as exc:
                logger.debug("JSON 解析失败 %s: %s", path, exc)
            except Exception as exc:  # noqa: BLE001
                logger.debug("读取 JSON 文件 %s 失败: %s", path, exc)
        return jobs

    async def _find_json_files(
        self,
        owner: str,
        repo: str,
        items: list[dict],
        depth: int,
    ) -> list[str]:
        """递归查找仓库中的 JSON 文件路径。"""
        paths: list[str] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            it_type = it.get("type")
            name = it.get("name", "")
            if it_type == "file" and name.lower().endswith(".json"):
                # 跳过 package.json / lock 等非数据文件
                if name.lower() in {
                    "package.json",
                    "package-lock.json",
                    "tsconfig.json",
                    "composer.json",
                }:
                    continue
                paths.append(it["path"])
            elif it_type == "dir" and depth < self.max_subdir_depth:
                try:
                    sub_resp = await self._api_get(
                        f"/repos/{owner}/{repo}/contents/{it['path']}"
                    )
                    sub_items = sub_resp.json()
                    if isinstance(sub_items, list):
                        paths.extend(
                            await self._find_json_files(
                                owner, repo, sub_items, depth + 1
                            )
                        )
                except Exception as exc:  # noqa: BLE001
                    logger.debug("无法进入子目录 %s: %s", it.get("path"), exc)
        return paths

    def _parse_json(self, data: Any, source: str) -> list[dict]:
        """解析 JSON 数据为 job dict 列表，兼容数组与多种包装结构。"""
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = None
            for k in ("jobs", "list", "data", "items", "positions", "records"):
                if isinstance(data.get(k), list):
                    items = data[k]
                    break
            if items is None:
                # 可能是单个对象
                items = [data]
        else:
            return []

        jobs: list[dict] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            title = (
                it.get("title")
                or it.get("position")
                or it.get("name")
                or it.get("job_name")
                or ""
            )
            company = (
                it.get("company")
                or it.get("company_name")
                or it.get("employer")
                or ""
            )
            if not title and not company:
                continue
            job = {
                "title": str(title),
                "company": str(company),
                "company_type": it.get("company_type", ""),
                "location": str(
                    it.get("location")
                    or it.get("city")
                    or it.get("work_location")
                    or ""
                ),
                "salary_raw": str(
                    it.get("salary") or it.get("salary_range") or ""
                ),
                "description": str(
                    it.get("description")
                    or it.get("detail")
                    or it.get("requirement")
                    or ""
                ),
                "deadline": str(it.get("deadline") or it.get("end_date") or ""),
                "education": str(it.get("education") or it.get("degree") or ""),
                "job_category": str(it.get("category") or it.get("job_category") or ""),
                "url": str(it.get("url") or it.get("link") or it.get("apply_url") or ""),
                "source": source,
                "source_repo": source,
                "raw_data": it,
            }
            jobs.append(job)
        return jobs
