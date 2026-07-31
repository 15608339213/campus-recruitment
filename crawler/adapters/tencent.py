"""腾讯校招适配器。

官网: https://campus.tencent.com （腾讯校园招聘）

优先使用 JSON 接口抓取，接口不可用时回退到 HTML 解析。
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
class TencentAdapter(BaseCompanyAdapter):
    """腾讯校招岗位适配器。"""

    company_name: str = "腾讯"
    company_type: str = "民企"
    careers_url: str = "https://campus.tencent.com/job.html"
    base_url: str = "https://campus.tencent.com"

    # 腾讯校招岗位搜索接口（实际字段以站点为准，此处做防御式解析）
    _list_api: ClassVar[str] = "https://campus.tencent.com/tencentcareer/api/post/Query"
    _detail_api: ClassVar[str] = "https://campus.tencent.com/tencentcareer/api/post/Detail"

    async def fetch_jobs(self) -> list[dict]:
        jobs: list[dict] = []
        page_index = 1
        page_size = 20
        max_pages = 100

        while page_index <= max_pages:
            params = {
                "timestamp": "",
                "countryId": "",
                "cityId": "",
                "bgIds": "",
                "productId": "",
                "categoryId": "",
                "parentCategoryId": "",
                "attrIds": "",
                "keyword": "",
                "pageIndex": page_index,
                "pageSize": page_size,
                "language": "zh-cn",
            }
            try:
                data = await self._get_json(self._list_api, params=params)
            except Exception as exc:  # noqa: BLE001
                logger.error("[%s] 岗位列表第 %d 页获取失败: %s", self.company_name, page_index, exc)
                break

            items = self._extract_items(data)
            if not items:
                if page_index == 1:
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
            page_index += 1

        logger.info("[%s] 共抓取 %d 个岗位", self.company_name, len(jobs))
        return jobs

    async def _fetch_from_html(self) -> list[dict]:
        jobs: list[dict] = []
        try:
            soup = await self._get_soup(self.careers_url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[%s] HTML 页面获取失败: %s", self.company_name, exc)
            return jobs

        cards = soup.select(
            "[class*=job-item], [class*=position-item], [class*=job-card], "
            "li[class*=job], div[class*=job-list] > div, .correlation-degree > div"
        )
        for card in cards:
            title_el = card.select_one(
                "[class*=job-title], [class*=position-title], h3, h4, a"
            )
            loc_el = card.select_one("[class*=city], [class*=location], [class*=work-place]")
            link_el = card.select_one("a[href]")
            title = title_el.get_text(strip=True) if title_el else ""
            location = loc_el.get_text(strip=True) if loc_el else ""
            url = link_el["href"] if link_el and link_el.has_attr("href") else ""
            if title:
                jobs.append(self._build_job(title=title, location=location, url=url))
        return jobs

    # ------------------------------------------------------------------ #
    # 防御式 JSON 解析
    # ------------------------------------------------------------------ #
    def _extract_items(self, data: Any) -> list:
        if isinstance(data, dict):
            for key in ("Data", "data", "result"):
                node = data.get(key)
                if isinstance(node, list):
                    return node
                if isinstance(node, dict):
                    for k2 in ("Posts", "posts", "list", "jobList", "items"):
                        if isinstance(node.get(k2), list):
                            return node[k2]
        if isinstance(data, list):
            return data
        return []

    def _extract_total(self, data: Any) -> int:
        if isinstance(data, dict):
            for key in ("Count", "count", "total", "totalCount"):
                try:
                    return int(data.get(key))
                except (TypeError, ValueError):
                    pass
            node = data.get("Data") or data.get("data")
            if isinstance(node, dict):
                for key in ("Count", "count", "total", "totalCount"):
                    try:
                        return int(node.get(key))
                    except (TypeError, ValueError):
                        pass
        return 0

    def _parse_list_item(self, item: dict) -> dict | None:
        if not isinstance(item, dict):
            return None
        title = (
            item.get("RecruitPostName")
            or item.get("recruitPostName")
            or item.get("title")
            or item.get("name")
            or ""
        )
        location = (
            item.get("LocationName")
            or item.get("locationName")
            or item.get("city")
            or item.get("location")
            or ""
        )
        if isinstance(location, list):
            location = ",".join(str(x) for x in location)
        job_id = (
            item.get("PostId")
            or item.get("postId")
            or item.get("id")
            or item.get("jobId")
            or ""
        )
        url = (
            f"{self.base_url}/jobdesc.html?postId={job_id}"
            if job_id
            else ""
        )
        # 腾讯接口列表通常不含职责详情，CategoryName 可作为类别
        category = (
            item.get("CategoryName")
            or item.get("categoryName")
            or item.get("category")
            or ""
        )
        responsibility = (
            item.get("Responsibility")
            or item.get("responsibility")
            or ""
        )
        bg = item.get("BGName") or item.get("bgName") or ""
        return self._build_job(
            title=str(title),
            location=str(location),
            description=str(responsibility),
            url=url,
            job_category=str(category),
            business_group=str(bg),
            post_id=str(job_id),
        )

    async def parse_detail(self, url: str) -> dict:
        detail: dict[str, Any] = {"url": url, "company": self.company_name}
        match = re.search(r"postId=([^&]+)", url) or re.search(r"(\d+)", url)
        post_id = match.group(1) if match else ""

        if post_id:
            try:
                data = await self._get_json(
                    self._detail_api, params={"postId": post_id, "language": "zh-cn"}
                )
                node = data.get("Data") if isinstance(data, dict) else data
                if not isinstance(node, dict):
                    node = data if isinstance(data, dict) else {}
                detail.update(
                    {
                        "title": node.get("RecruitPostName")
                        or node.get("recruitPostName")
                        or "",
                        "location": node.get("LocationName")
                        or node.get("locationName")
                        or "",
                        "description": node.get("Responsibility")
                        or node.get("responsibility")
                        or "",
                        "requirement": node.get("Requirement")
                        or node.get("requirement")
                        or "",
                        "job_category": node.get("CategoryName")
                        or node.get("categoryName")
                        or "",
                    }
                )
                return detail
            except Exception as exc:  # noqa: BLE001
                logger.debug("[%s] 详情接口失败 %s: %s", self.company_name, url, exc)

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
