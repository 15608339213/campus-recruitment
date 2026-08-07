"""国家大学生就业服务平台 (ncss.cn) 爬虫适配器。

采集校招/实习岗位数据，存入本地数据库。
"""
from __future__ import annotations

import asyncio
import re
from datetime import date, datetime
from typing import Any, Dict, List

import httpx


NCSS_BASE = "https://www.ncss.cn"
NCSS_API = "https://www.ncss.cn/api"
# 校园招聘搜索
SEARCH_URL = f"{NCSS_API}/job/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.ncss.cn/student/jobs/",
    "Accept": "application/json",
}


async def search_ncss_jobs(
    keyword: str = "",
    page: int = 1,
    limit: int = 50,
) -> Dict[str, Any]:
    """搜索国家大学生就业服务平台岗位。

    Args:
        keyword: 搜索关键词
        page: 页码
        limit: 每页数量

    Returns:
        {"total": int, "items": [...]}
    """
    async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
        params = {
            "key": keyword,
            "page_index": page,
            "page_size": limit,
            "work_city_name": "",
            "job_type": "",  # 全职/实习
        }
        try:
            resp = await client.get(SEARCH_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[NCSS] 请求失败: {e}")
            return {"total": 0, "items": []}

    items = []
    for job in data.get("data", {}).get("list", []):
        salary_min, salary_max = _parse_salary(job.get("salary", ""))
        items.append({
            "title": job.get("job_name", ""),
            "company": job.get("company_name", ""),
            "company_type": _guess_company_type(job.get("company_property", "")),
            "location": _clean_city(job.get("work_city_name", "")),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_unit": "元/月",
            "job_category": _map_category(job.get("job_category", "")),
            "job_type": "校招",
            "degree_required": job.get("education", "本科"),
            "description_html": job.get("job_desc", ""),
            "source_url": f"https://www.ncss.cn/student/jobs/{job.get('id', '')}",
            "source_repo": "ncss",
            "tags": _extract_tags(job),
        })

    total = data.get("data", {}).get("total", 0)
    return {"total": total, "items": items}


def _parse_salary(raw: str) -> tuple:
    """解析薪资字符串 → (min, max)。"""
    if not raw:
        return (0, 0)
    numbers = re.findall(r"(\d[\d.]*)\s*[kK千]?", raw)
    if not numbers:
        numbers = re.findall(r"\d[\d.]*", raw)
    if len(numbers) >= 2:
        return (int(float(numbers[0]) * 1000), int(float(numbers[1]) * 1000))
    if len(numbers) == 1:
        val = int(float(numbers[0]) * 1000)
        return (val, val)
    return (0, 0)


def _clean_city(raw: str) -> str:
    """清理城市名。"""
    for suffix in ["市", "省", "地区"]:
        raw = raw.replace(suffix, "")
    return raw.strip()


CATEGORY_MAP = {
    "计算机": "技术", "软件开发": "技术", "人工智能": "技术", "数据分析": "技术",
    "产品": "产品", "运营": "运营", "新媒体": "运营",
    "金融": "金融", "投资": "金融", "银行": "金融",
    "设计": "设计", "UI": "设计",
    "市场": "市场", "营销": "市场", "销售": "市场",
    "人力资源": "人力资源", "行政": "人力资源",
    "供应链": "供应链", "物流": "供应链", "采购": "供应链",
}


def _map_category(raw: str) -> str:
    for key, cat in CATEGORY_MAP.items():
        if key in raw or key in raw.lower():
            return cat
    return "技术"


def _guess_company_type(raw: str) -> str:
    if "国有" in raw:
        return "国企"
    if "外资" in raw or "外商" in raw:
        return "外企"
    if "事业" in raw or "机关" in raw:
        return "事业单位"
    return "民企"


def _extract_tags(job: dict) -> list:
    tags = []
    welfare = job.get("welfare", "")
    if "五险一金" in welfare:
        tags.append("五险一金")
    if "年终奖" in welfare:
        tags.append("年终奖")
    if "餐补" in welfare:
        tags.append("餐饮补贴")
    if "住宿" in welfare:
        tags.append("住房补贴")
    return tags[:4]


# 可直接运行的测试
if __name__ == "__main__":
    result = asyncio.run(search_ncss_jobs(keyword="计算机", limit=5))
    print(f"Total: {result['total']}, Items: {len(result['items'])}")
    for item in result["items"]:
        print(f"  {item['title']} @ {item['company']} - {item['location']}")
