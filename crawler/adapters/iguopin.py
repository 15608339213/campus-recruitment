"""国聘 (iguopin) 适配器。

官网: https://www.iguopin.com
校招板块: https://www.iguopin.com/campus

国聘是国务院国资委主管的国家级招聘平台，汇聚大量国企和央企岗位，
是国企招聘信息的权威来源。
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
class IguopinAdapter(BaseCompanyAdapter):
    """国聘 (iguopin) 岗位适配器。"""

    company_name: str = "国聘"
    company_type: str = "国企"
    careers_url: str = "https://www.iguopin.com/campus"
    base_url: str = "https://www.iguopin.com"
    request_interval: float = 1.5

    # 国聘 API 接口
    _list_api: ClassVar[str] = "https://www.iguopin.com/api/job/list"
    _detail_api: ClassVar[str] = "https://www.iguopin.com/api/job/detail"

    async def fetch_jobs(self) -> list[dict]:
        """抓取国聘平台岗位列表。"""
        jobs: list[dict] = []

        # 尝试 JSON 接口
        try:
            jobs = await self._fetch_from_api()
        except Exception as exc:
            logger.warning("[国聘] API 接口获取失败: %s，尝试 HTML 解析", exc)
            jobs = await self._fetch_from_html()

        logger.info("[国聘] 共抓取 %d 个岗位", len(jobs))
        return jobs

    async def _fetch_from_api(self) -> list[dict]:
        """通过 API 接口获取岗位列表。"""
        jobs: list[dict] = []
        page = 1
        page_size = 20
        max_pages = 30

        while page <= max_pages:
            params = {
                "page": page,
                "page_size": page_size,
                "type": "campus",  # 校招
                "keyword": "",
                "city": "",
                "industry": "",
                "salary": "",
                "education": "",
                "experience": "",
            }
            try:
                data = await self._get_json(self._list_api, params=params)
            except Exception as exc:
                logger.error("[国聘] 第 %d 页获取失败: %s", page, exc)
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
            page += 1

        return jobs

    async def _fetch_from_html(self) -> list[dict]:
        """从 HTML 页面解析岗位卡片。"""
        jobs: list[dict] = []
        try:
            soup = await self._get_soup(self.careers_url)
        except Exception as exc:
            logger.warning("[国聘] HTML 页面获取失败: %s", exc)
            return jobs

        cards = soup.select(
            ".job-list .job-item, .position-list .item, "
            "[class*=job-card], [class*=position-card], "
            ".list-content .job-card"
        )
        for card in cards:
            title_el = card.select_one(
                ".job-title a, .position-title a, [class*=job-name], h3 a"
            )
            company_el = card.select_one(
                ".company-name a, .company a, [class*=company]"
            )
            loc_el = card.select_one(
                ".city, .location, [class*=city], [class*=location]"
            )
            salary_el = card.select_one(
                ".salary, [class*=salary], .job-salary"
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
            for key in ("data", "result", "list", "items"):
                node = data.get(key)
                if isinstance(node, list):
                    return node
                if isinstance(node, dict):
                    for k2 in ("list", "items", "jobs", "records"):
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
            node = data.get("data")
            if isinstance(node, dict):
                for key in ("total", "count", "totalCount"):
                    try:
                        return int(node.get(key, 0) or 0)
                    except (TypeError, ValueError):
                        pass
        return 0

    def _parse_list_item(self, item: dict) -> dict | None:
        if not isinstance(item, dict):
            return None

        title = (
            item.get("jobTitle")
            or item.get("job_title")
            or item.get("positionName")
            or item.get("name")
            or ""
        )
        company = (
            item.get("companyName")
            or item.get("company_name")
            or item.get("enterpriseName")
            or ""
        )
        company_type = item.get("companyType") or item.get("enterpriseType") or ""
        location = (
            item.get("workCity")
            or item.get("city")
            or item.get("cityName")
            or item.get("workPlace")
            or ""
        )
        salary = item.get("salary") or item.get("salaryRange") or ""
        education = item.get("education") or item.get("degree") or ""
        experience = item.get("experience") or item.get("workExperience") or ""
        description = item.get("jobDescription") or item.get("description") or ""
        url = item.get("detailUrl") or item.get("url") or ""
        job_id = item.get("id") or item.get("jobId") or ""
        welfare = item.get("welfare") or item.get("jobWelfare") or ""

        if not title:
            return None

        if not url and job_id:
            url = f"{self.base_url}/job/detail/{job_id}"

        job = self._build_job(
            title=str(title),
            location=str(location),
            description=str(description),
            url=str(url),
            salary=str(salary),
            education=str(education),
            job_category="",
        )
        if company:
            job["company"] = str(company)
        if company_type:
            job["company_type"] = str(company_type)
        if welfare:
            if isinstance(welfare, list):
                job["tags"] = welfare
            else:
                job["tags"] = [str(w)]
        return job

    async def parse_detail(self, url: str) -> dict:
        """解析岗位详情页。"""
        detail: dict[str, Any] = {"url": url, "company": self.company_name}

        # 尝试从 URL 提取 job_id
        match = re.search(r"detail/(\d+)", url) or re.search(r"(\d+)", url)
        job_id = match.group(1) if match else ""

        if job_id:
            try:
                data = await self._get_json(
                    self._detail_api, params={"id": job_id}
                )
                node = data.get("data") if isinstance(data, dict) else data
                if not isinstance(node, dict):
                    node = data if isinstance(data, dict) else {}

                detail.update(
                    {
                        "title": node.get("jobTitle") or node.get("title") or "",
                        "company": node.get("companyName") or node.get("company") or "",
                        "location": node.get("workCity") or node.get("city") or "",
                        "description": node.get("jobDescription")
                        or node.get("description")
                        or "",
                        "salary_raw": node.get("salary") or node.get("salaryRange") or "",
                    }
                )
                return detail
            except Exception as exc:
                logger.debug("[国聘] 详情接口失败 %s: %s", url, exc)

        # 回退到 HTML
        try:
            soup = await self._get_soup(url)
            desc_el = soup.select_one(
                ".job-detail, .job-description, [class*=job-desc], "
                ".responsibility, .detail-content"
            )
            if desc_el:
                detail["description"] = desc_el.get_text("\n", strip=True)

            title_el = soup.select_one("h1, .job-title, [class*=job-name]")
            if title_el:
                detail["title"] = title_el.get_text(strip=True)

            company_el = soup.select_one(".company-name a, [class*=company-name]")
            if company_el:
                detail["company"] = company_el.get_text(strip=True)
        except Exception as exc:
            logger.warning("[国聘] 详情页解析失败 %s: %s", url, exc)

        return detail
