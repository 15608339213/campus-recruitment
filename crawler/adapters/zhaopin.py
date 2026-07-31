"""智联招聘适配器。

官网: https://www.zhaopin.com
校招板块: https://xiaoyuan.zhaopin.com

智联招聘是全国最大的综合性招聘平台之一，拥有大量校招和社招岗位数据。
本适配器通过站点搜索接口抓取岗位列表，回退到 HTML 解析。
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
class ZhaopinAdapter(BaseCompanyAdapter):
    """智联招聘岗位适配器。"""

    company_name: str = "智联招聘"
    company_type: str = "民企"
    careers_url: str = "https://xiaoyuan.zhaopin.com"
    base_url: str = "https://xiaoyuan.zhaopin.com"
    request_interval: float = 2.0  # 智联反爬较严，降低请求频率

    # 智联搜索接口（实际接口可能变化，此处做防御式解析）
    _search_api: ClassVar[str] = "https://fe-api.zhaopin.com/c/i/search/positions"
    _detail_api: ClassVar[str] = "https://fe-api.zhaopin.com/c/i/position/detail"

    async def fetch_jobs(self) -> list[dict]:
        """抓取智联招聘校招岗位列表。"""
        jobs: list[dict] = []

        # 尝试 JSON 接口
        try:
            jobs = await self._fetch_from_api()
        except Exception as exc:
            logger.warning("[智联招聘] API 接口获取失败: %s，尝试 HTML 解析", exc)
            jobs = await self._fetch_from_html()

        logger.info("[智联招聘] 共抓取 %d 个岗位", len(jobs))
        return jobs

    async def _fetch_from_api(self) -> list[dict]:
        """通过搜索接口获取岗位列表。"""
        jobs: list[dict] = []
        page = 1
        page_size = 30
        max_pages = 20  # 限制页数，避免被封

        # 搜索关键词列表，覆盖多个行业
        keywords = [
            "校招", "应届生", "校园招聘",
            "Java开发", "前端开发", "Python开发",
            "产品经理", "运营", "数据分析",
            "UI设计", "测试工程师", "算法工程师",
        ]

        for keyword in keywords:
            logger.debug("[智联招聘] 搜索关键词: %s", keyword)
            for page in range(1, max_pages + 1):
                params = {
                    "keyword": keyword,
                    "pageIndex": page,
                    "pageSize": page_size,
                    "city": "",
                    "salary": "",
                    "workExperience": "",
                    "education": "",
                    "companyType": "",
                    "employmentType": "",
                }
                try:
                    data = await self._get_json(self._search_api, params=params)
                except Exception:
                    break

                items = self._extract_items(data)
                if not items:
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

        return jobs

    async def _fetch_from_html(self) -> list[dict]:
        """从 HTML 页面解析岗位卡片。"""
        jobs: list[dict] = []
        try:
            soup = await self._get_soup(self.careers_url)
        except Exception as exc:
            logger.warning("[智联招聘] HTML 页面获取失败: %s", exc)
            return jobs

        # 智联招聘岗位卡片结构
        cards = soup.select(
            ".joblist-box .jobinfo, .positionList .jobinfo, "
            "[class*=job-item], [class*=position-card], "
            ".search-result .item"
        )
        for card in cards:
            title_el = card.select_one(
                ".jobname a, .position-name a, [class*=job-title], h3 a, a"
            )
            company_el = card.select_one(
                ".company_name a, .company-name a, [class*=company]"
            )
            loc_el = card.select_one(
                ".city, .location, [class*=city], [class*=location]"
            )
            salary_el = card.select_one(
                ".salary, [class*=salary], .job-saraly"
            )
            link_el = card.select_one("a[href]")

            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else ""
            location = loc_el.get_text(strip=True) if loc_el else ""
            salary = salary_el.get_text(strip=True) if salary_el else ""
            url = link_el["href"] if link_el and link_el.has_attr("href") else ""

            if title:
                job = self._build_job(
                    title=title,
                    location=location,
                    url=url,
                    salary=salary,
                )
                # 覆盖默认公司名（智联是多公司平台）
                if company:
                    job["company"] = company
                jobs.append(job)

        return jobs

    def _extract_items(self, data: Any) -> list:
        if isinstance(data, dict):
            for key in ("data", "result", "results", "list"):
                node = data.get(key)
                if isinstance(node, list):
                    return node
                if isinstance(node, dict):
                    for k2 in ("list", "items", "jobs", "positions"):
                        if isinstance(node.get(k2), list):
                            return node[k2]
        if isinstance(data, list):
            return data
        return []

    def _extract_total(self, data: Any) -> int:
        if isinstance(data, dict):
            for key in ("total", "count", "totalCount", "total_count"):
                try:
                    return int(data.get(key, 0) or 0)
                except (TypeError, ValueError):
                    pass
        return 0

    def _parse_list_item(self, item: dict) -> dict | None:
        if not isinstance(item, dict):
            return None

        title = (
            item.get("jobName")
            or item.get("job_name")
            or item.get("positionName")
            or item.get("title")
            or ""
        )
        company = (
            item.get("companyName")
            or item.get("company_name")
            or item.get("company")
            or ""
        )
        company_type = item.get("companyType") or item.get("company_type") or ""
        location = (
            item.get("city")
            or item.get("cityName")
            or item.get("workCity")
            or ""
        )
        salary = (
            item.get("salary")
            or item.get("salaryStr")
            or item.get("salary_str")
            or ""
        )
        education = item.get("education") or item.get("educationName") or ""
        description = item.get("jobDesc") or item.get("job_desc") or ""
        url = item.get("positionURL") or item.get("url") or ""
        welfare = item.get("welfare") or item.get("jobLabel") or ""

        if not title:
            return None

        job = self._build_job(
            title=str(title),
            location=str(location),
            description=str(description),
            url=str(url),
            salary=str(salary),
            education=str(education),
        )
        if company:
            job["company"] = str(company)
        if company_type:
            job["company_type"] = str(company_type)
        return job

    async def parse_detail(self, url: str) -> dict:
        """解析岗位详情页。"""
        detail: dict[str, Any] = {"url": url, "company": self.company_name}
        try:
            soup = await self._get_soup(url)
            # 智联详情页结构
            desc_el = soup.select_one(
                ".describtion, .job-description, [class*=job-detail], "
                ".responsibility, [class*=position-desc]"
            )
            if desc_el:
                detail["description"] = desc_el.get_text("\n", strip=True)

            title_el = soup.select_one("h1, .job-title, [class*=position-name]")
            if title_el:
                detail["title"] = title_el.get_text(strip=True)

            company_el = soup.select_one(".company-name a, [class*=company-name]")
            if company_el:
                detail["company"] = company_el.get_text(strip=True)
        except Exception as exc:
            logger.warning("[智联招聘] 详情页解析失败 %s: %s", url, exc)
        return detail
