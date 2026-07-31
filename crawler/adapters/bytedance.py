"""字节跳动校招适配器。

官网: https://jobs.bytedance.com （校招板块，旧域名 job.toutiao.com）

优先使用站点 JSON 接口抓取岗位列表（httpx 异步），当接口不可用时
回退到 HTML 解析；如启用 Playwright 还可渲染详情页。
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, ClassVar

from bs4 import BeautifulSoup

from .base_adapter import BaseCompanyAdapter

logger = logging.getLogger(__name__)


@dataclass
class ByteDanceAdapter(BaseCompanyAdapter):
    """字节跳动校招岗位适配器。"""

    company_name: str = "字节跳动"
    company_type: str = "民企"
    careers_url: str = "https://jobs.bytedance.com/campus"
    base_url: str = "https://jobs.bytedance.com"

    # 站点岗位搜索接口（实际字段以站点为准，此处做防御式解析）
    _list_api: ClassVar[str] = "https://jobs.bytedance.com/api/v1/search/job/posts"
    _detail_api: ClassVar[str] = "https://jobs.bytedance.com/api/v1/job/detail"

    async def fetch_jobs(self) -> list[dict]:
        """抓取校招岗位列表。"""
        jobs: list[dict] = []
        page = 1
        page_size = 20
        max_pages = 100  # 安全上限，防止无限翻页

        while page <= max_pages:
            params = {
                "keyword": "",
                "limit": page_size,
                "offset": (page - 1) * page_size,
                "city": "",
                "category": "",
                # recruit_type=2 通常对应校招
                "recruit_type": "2",
            }
            try:
                data = await self._get_json(self._list_api, params=params)
            except Exception as exc:  # noqa: BLE001
                logger.error("[%s] 岗位列表第 %d 页获取失败: %s", self.company_name, page, exc)
                break

            items = self._extract_items(data)
            if not items:
                # 接口未返回数据，尝试 HTML 回退
                if page == 1:
                    logger.info("[%s] JSON 接口无数据，尝试 HTML 解析", self.company_name)
                    jobs.extend(await self._fetch_from_html())
                break

            for item in items:
                parsed = self._parse_list_item(item)
                if parsed:
                    jobs.append(parsed)

            total = self._extract_total(data)
            if total and len(jobs) >= total:
                break
            if len(items) < page_size:
                break
            page += 1

        logger.info("[%s] 共抓取 %d 个岗位", self.company_name, len(jobs))
        return jobs

    async def _fetch_from_html(self) -> list[dict]:
        """从校招 HTML 页面解析岗位卡片（接口不可用时的回退方案）。"""
        jobs: list[dict] = []
        try:
            soup = await self._get_soup(self.careers_url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[%s] HTML 页面获取失败: %s", self.company_name, exc)
            return jobs

        # 适配多种常见岗位卡片结构
        cards = soup.select(
            "[class*=job-item], [class*=position-item], [class*=job-card], "
            "li[class*=job], div[class*=job-list] > div"
        )
        for card in cards:
            title_el = card.select_one(
                "[class*=job-title], [class*=position-title], h3, h4, a"
            )
            loc_el = card.select_one("[class*=city], [class*=location]")
            link_el = card.select_one("a[href]")
            title = title_el.get_text(strip=True) if title_el else ""
            location = loc_el.get_text(strip=True) if loc_el else ""
            url = link_el["href"] if link_el and link_el.has_attr("href") else ""
            if title:
                jobs.append(
                    self._build_job(title=title, location=location, url=url)
                )
        return jobs

    # ------------------------------------------------------------------ #
    # 防御式 JSON 解析（兼容多种返回结构）
    # ------------------------------------------------------------------ #
    def _extract_items(self, data: Any) -> list:
        if isinstance(data, dict):
            for key in ("data", "result", "job_list", "list"):
                node = data.get(key)
                if isinstance(node, list):
                    return node
                if isinstance(node, dict):
                    for k2 in ("list", "job_list", "items", "posts", "job_post_list"):
                        if isinstance(node.get(k2), list):
                            return node[k2]
        if isinstance(data, list):
            return data
        return []

    def _extract_total(self, data: Any) -> int:
        if isinstance(data, dict):
            for key in ("total", "count", "total_count"):
                try:
                    return int(data.get(key))
                except (TypeError, ValueError):
                    pass
            node = data.get("data")
            if isinstance(node, dict):
                for key in ("total", "count", "total_count"):
                    try:
                        return int(node.get(key))
                    except (TypeError, ValueError):
                        pass
        return 0

    def _parse_list_item(self, item: dict) -> dict | None:
        if not isinstance(item, dict):
            return None
        title = item.get("title") or item.get("name") or item.get("recruit_name") or ""
        location = item.get("city") or item.get("city_info") or item.get("location") or ""
        if isinstance(location, list):
            location = ",".join(str(x) for x in location)
        job_id = item.get("id") or item.get("job_id") or item.get("code") or ""
        url = (
            f"{self.base_url}/campus/position/{job_id}/detail"
            if job_id
            else ""
        )
        description = (
            item.get("description")
            or item.get("responsibility")
            or item.get("job_responsibility")
            or ""
        )
        salary = item.get("salary_range") or item.get("salary") or ""
        category = item.get("category") or item.get("job_category") or ""
        return self._build_job(
            title=str(title),
            location=str(location),
            description=str(description),
            url=url,
            salary=str(salary),
            job_category=str(category),
            job_id=str(job_id),
            recruit_type=item.get("recruit_type", ""),
        )

    async def parse_detail(self, url: str) -> dict:
        """解析单个岗位详情。"""
        # 从 URL 中提取 job_id
        match = re.search(r"position/([^/]+)/detail", url) or re.search(r"(\d+)", url)
        job_id = match.group(1) if match else ""

        detail: dict[str, Any] = {"url": url, "company": self.company_name}
        if job_id:
            try:
                data = await self._get_json(self._detail_api, params={"job_id": job_id})
                node = data.get("data") if isinstance(data, dict) else data
                if not isinstance(node, dict):
                    node = data if isinstance(data, dict) else {}
                detail.update(
                    {
                        "title": node.get("title", ""),
                        "location": node.get("city", ""),
                        "description": node.get("description")
                        or node.get("job_responsibility")
                        or "",
                        "requirement": node.get("requirement")
                        or node.get("job_requirement")
                        or "",
                        "job_category": node.get("category", ""),
                    }
                )
                return detail
            except Exception as exc:  # noqa: BLE001
                logger.debug("[%s] 详情接口失败 %s: %s", self.company_name, url, exc)

        # 回退到 HTML / Playwright 渲染
        try:
            if self.use_playwright:
                html = await self._get_rendered_html(url)
                soup = BeautifulSoup(html, "lxml")
            else:
                soup = await self._get_soup(url)
            detail["description"] = soup.get_text("\n", strip=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[%s] 详情页解析失败 %s: %s", self.company_name, url, exc)
        return detail
