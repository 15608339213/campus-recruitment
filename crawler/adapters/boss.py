"""Boss直聘适配器。

官网: https://www.zhipin.com
校招板块: https://www.zhipin.com/campus/

Boss直聘是国内主流的互联网招聘平台，以直接与 Boss 聊天为特色。
本适配器通过站点搜索接口抓取岗位列表，回退到 HTML 解析。

注意: Boss直聘有较强的反爬机制，建议设置较长的请求间隔和合理的 User-Agent。
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
class BossAdapter(BaseCompanyAdapter):
    """Boss直聘岗位适配器。"""

    company_name: str = "Boss直聘"
    company_type: str = "民企"
    careers_url: str = "https://www.zhipin.com/campus/"
    base_url: str = "https://www.zhipin.com"
    request_interval: float = 2.5  # Boss 反爬严格，降低频率

    # Boss直聘搜索接口
    _search_api: ClassVar[str] = "https://www.zhipin.com/wapi/zpgeek/search/joblist.json"

    async def fetch_jobs(self) -> list[dict]:
        """抓取Boss直聘岗位列表。"""
        jobs: list[dict] = []

        # 尝试 HTML 解析（Boss直聘主要靠渲染页面）
        try:
            jobs = await self._fetch_from_html()
        except Exception as exc:
            logger.warning("[Boss直聘] HTML 获取失败: %s", exc)

        # 尝试 API 接口
        if not jobs:
            try:
                jobs = await self._fetch_from_api()
            except Exception as exc:
                logger.warning("[Boss直聘] API 获取失败: %s", exc)

        logger.info("[Boss直聘] 共抓取 %d 个岗位", len(jobs))
        return jobs

    async def _fetch_from_api(self) -> list[dict]:
        """通过搜索接口获取岗位列表。"""
        jobs: list[dict] = []
        page = 1
        max_pages = 15

        # 搜索关键词覆盖多个方向
        keywords = [
            "校招", "应届生", "2026校招",
            "Java", "前端", "Python", "Go",
            "产品经理", "数据分析", "运营",
            "测试", "算法", "UI设计",
        ]

        for keyword in keywords:
            for page in range(1, max_pages + 1):
                params = {
                    "query": keyword,
                    "page": page,
                    "city": "",
                    "industry": "",
                    "position": "",
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

                if len(items) < 15:
                    break

        return jobs

    async def _fetch_from_html(self) -> list[dict]:
        """从 HTML 页面解析岗位卡片。"""
        jobs: list[dict] = []

        # Boss直聘的搜索页面 URL
        search_urls = [
            f"{self.base_url}/web/geek/job?query=校招&city=",
            f"{self.base_url}/web/geek/job?query=应届生&city=",
            f"{self.base_url}/web/geek/job?query=2026校招&city=",
        ]

        for url in search_urls:
            try:
                soup = await self._get_soup(url)
            except Exception as exc:
                logger.debug("[Boss直聘] 页面获取失败 %s: %s", url, exc)
                continue

            # Boss直聘岗位卡片结构
            cards = soup.select(
                ".job-card-wrapper, .job-list li, [class*=job-card], "
                ".search-job-result .job-card"
            )
            for card in cards:
                title_el = card.select_one(
                    ".job-name a, .job-title a, [class*=job-name] a, h3 a"
                )
                company_el = card.select_one(
                    ".company-name a, .company-info a, [class*=company-name]"
                )
                loc_el = card.select_one(
                    ".job-area, .job-area-list, [class*=area], [class*=city]"
                )
                salary_el = card.select_one(
                    ".salary, .job-salary, [class*=salary]"
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
                    if company:
                        job["company"] = company
                    jobs.append(job)

        return jobs

    def _extract_items(self, data: Any) -> list:
        if isinstance(data, dict):
            for key in ("zpData", "data", "result"):
                node = data.get(key)
                if isinstance(node, dict):
                    for k2 in ("jobList", "jobs", "list", "items"):
                        if isinstance(node.get(k2), list):
                            return node[k2]
                elif isinstance(node, list):
                    return node
        if isinstance(data, list):
            return data
        return []

    def _parse_list_item(self, item: dict) -> dict | None:
        if not isinstance(item, dict):
            return None

        title = (
            item.get("jobName")
            or item.get("job_name")
            or item.get("positionName")
            or ""
        )
        company = (
            item.get("brandName")
            or item.get("companyName")
            or item.get("brand_name")
            or ""
        )
        location = (
            item.get("cityName")
            or item.get("city_name")
            or item.get("jobArea")
            or ""
        )
        salary = item.get("salaryDesc") or item.get("salary") or ""
        education = item.get("jobDegree") or item.get("education") or ""
        experience = item.get("jobExperience") or item.get("experience") or ""
        description = item.get("jobDesc") or item.get("postDescription") or ""
        url = item.get("jobHref") or item.get("url") or ""
        skills = item.get("skills") or []
        job_labels = item.get("jobLabels") or []

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
        if skills:
            job["tags"] = skills if isinstance(skills, list) else [str(skills)]
        if job_labels:
            existing_tags = job.get("tags", [])
            existing_tags.extend(job_labels if isinstance(job_labels, list) else [str(job_labels)])
            job["tags"] = existing_tags
        return job

    async def parse_detail(self, url: str) -> dict:
        """解析岗位详情页。"""
        detail: dict[str, Any] = {"url": url, "company": self.company_name}
        try:
            soup = await self._get_soup(url)
            desc_el = soup.select_one(
                ".job-sec-text, .job-detail-section, [class*=job-desc], "
                ".responsibility, .text"
            )
            if desc_el:
                detail["description"] = desc_el.get_text("\n", strip=True)

            title_el = soup.select_one(".job-banner h1, .job-name, .name")
            if title_el:
                detail["title"] = title_el.get_text(strip=True)

            company_el = soup.select_one(".company-info .name, .company-name")
            if company_el:
                detail["company"] = company_el.get_text(strip=True)

            salary_el = soup.select_one(".salary, .job-salary")
            if salary_el:
                detail["salary_raw"] = salary_el.get_text(strip=True)
        except Exception as exc:
            logger.warning("[Boss直聘] 详情页解析失败 %s: %s", url, exc)
        return detail
