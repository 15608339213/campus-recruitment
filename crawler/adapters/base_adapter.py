"""企业官网招聘信息适配器基类。

提供异步 HTTP 客户端、每站点速率限制（默认 ≤1 req/s）、robots.txt
遵守以及可选的 Playwright JS 渲染能力。所有企业官网适配器（字节跳动、
阿里巴巴、腾讯等）均继承 :class:`BaseCompanyAdapter` 并实现
:meth:`fetch_jobs` 与 :meth:`parse_detail`。
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

#: 爬虫统一 User-Agent，用于 robots.txt 判定与请求头
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; QiuZhaoBot/1.0; "
    "+https://github.com/autumn-recruitment/crawler) "
    "AutumnRecruitmentCrawler/1.0"
)


@dataclass
class BaseCompanyAdapter:
    """企业官网适配器基类（dataclass 定义数据结构）。

    Attributes:
        company_name: 企业名称。
        company_type: 企业类型，国企/民企/外企/事业单位。
        careers_url: 校招主页 URL。
        base_url: 站点根 URL，用于把相对链接补全为绝对链接。
        request_interval: 同一站点两次请求的最小间隔（秒），默认 1.0，
            即 ≤1 req/s，满足 robots.txt 礼貌抓取要求。
        timeout: 单次请求超时（秒）。
        use_playwright: 是否在 httpx 无法获取数据时回退到 Playwright
            渲染（需要额外安装浏览器内核）。
    """

    company_name: str = ""
    company_type: str = ""  # 国企/民企/外企/事业单位
    careers_url: str = ""
    base_url: str = ""
    request_interval: float = 1.0
    timeout: float = 30.0
    use_playwright: bool = False
    headers: dict = field(
        default_factory=lambda: {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml,"
                "application/json;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
    )

    # ------------------------------------------------------------------ #
    # 内部状态（不参与构造参数，在 __post_init__ 中初始化）
    # ------------------------------------------------------------------ #
    def __post_init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_ts: float = 0.0
        self._robots_cache: dict[str, RobotFileParser] = {}
        # 自动推导 base_url
        if not self.base_url and self.careers_url:
            parsed = urlparse(self.careers_url)
            self.base_url = f"{parsed.scheme}://{parsed.netloc}"

    # ------------------------------------------------------------------ #
    # 生命周期管理
    # ------------------------------------------------------------------ #
    async def __aenter__(self) -> "BaseCompanyAdapter":
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self.headers,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
                http2=False,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    # ------------------------------------------------------------------ #
    # robots.txt 遵守
    # ------------------------------------------------------------------ #
    async def _check_robots(self, url: str) -> bool:
        """检查 robots.txt 是否允许抓取该 URL，结果按站点缓存。"""
        parsed = urlparse(url)
        host = f"{parsed.scheme}://{parsed.netloc}"
        if host not in self._robots_cache:
            rp = RobotFileParser()
            robots_url = urljoin(host, "/robots.txt")
            try:
                client = await self._ensure_client()
                # 读取 robots.txt 不受业务速率限制约束，但仍复用同一 client
                resp = await client.get(robots_url, timeout=10)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    # 没有 robots.txt（404 等），默认允许全部
                    rp.parse([])
            except Exception as exc:  # noqa: BLE001
                logger.debug("读取 robots.txt 失败 %s: %s", robots_url, exc)
                rp.parse([])
            self._robots_cache[host] = rp
        return self._robots_cache[host].can_fetch(DEFAULT_USER_AGENT, url)

    # ------------------------------------------------------------------ #
    # 速率限制的请求方法
    # ------------------------------------------------------------------ #
    async def _rate_limit(self) -> None:
        """保证同一站点的请求间隔不小于 request_interval 秒。"""
        elapsed = time.monotonic() - self._last_request_ts
        if elapsed < self.request_interval:
            await asyncio.sleep(self.request_interval - elapsed)
        self._last_request_ts = time.monotonic()

    async def _get(self, url: str, **kwargs: Any) -> httpx.Response:
        """带 robots 校验与速率限制的 GET 请求。"""
        if not await self._check_robots(url):
            logger.warning("robots.txt 禁止抓取: %s", url)
            raise PermissionError(f"robots.txt disallows fetching {url}")
        await self._rate_limit()
        client = await self._ensure_client()
        logger.debug("[%s] GET %s", self.company_name, url)
        resp = await client.get(url, **kwargs)
        resp.raise_for_status()
        return resp

    async def _get_json(self, url: str, **kwargs: Any) -> Any:
        resp = await self._get(url, **kwargs)
        return resp.json()

    async def _get_soup(self, url: str, **kwargs: Any) -> BeautifulSoup:
        resp = await self._get(url, **kwargs)
        return BeautifulSoup(resp.text, "lxml")

    async def _get_rendered_html(self, url: str, wait_selector: str = "") -> str:
        """使用 Playwright 渲染 JS 页面并返回 HTML（可选能力）。

        当 :attr:`use_playwright` 为 True 且页面需要 JS 渲染时调用。
        若 Playwright 未安装则抛出 RuntimeError。
        """
        if not self.use_playwright:
            raise RuntimeError("Playwright 未启用（use_playwright=False）")
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "未安装 playwright，请执行: pip install playwright && "
                "python -m playwright install chromium"
            ) from exc

        await self._rate_limit()
        logger.debug("[%s] Playwright 渲染 %s", self.company_name, url)
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=DEFAULT_USER_AGENT)
            await page.goto(url, wait_until="networkidle", timeout=int(self.timeout * 1000))
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=10000)
                except Exception:  # noqa: BLE001
                    pass
            html = await page.content()
            await browser.close()
        return html

    # ------------------------------------------------------------------ #
    # 子类需实现的接口
    # ------------------------------------------------------------------ #
    async def fetch_jobs(self) -> list[dict]:
        """抓取岗位列表，返回原始 job dict 列表。

        每个 dict 至少应包含: title, company, location, url, source 等字段，
        具体字段由 :mod:`pipeline` 统一清洗。
        """
        raise NotImplementedError

    async def parse_detail(self, url: str) -> dict:
        """解析岗位详情页，返回详情 dict。"""
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # 工具方法
    # ------------------------------------------------------------------ #
    def _absurl(self, url: str) -> str:
        """把相对 URL 补全为绝对 URL。"""
        if not url:
            return ""
        if url.startswith(("http://", "https://")):
            return url
        return urljoin(self.base_url or self.careers_url, url)

    def _build_job(
        self,
        title: str = "",
        location: str = "",
        description: str = "",
        url: str = "",
        salary: str = "",
        deadline: str = "",
        job_category: str = "",
        education: str = "",
        **extra: Any,
    ) -> dict:
        """构造标准化的原始 job dict，供 pipeline 清洗。"""
        job: dict[str, Any] = {
            "title": (title or "").strip(),
            "company": self.company_name,
            "company_type": self.company_type,
            "location": (location or "").strip(),
            "salary_raw": (salary or "").strip(),
            "description": (description or "").strip(),
            "deadline": (deadline or "").strip(),
            "url": self._absurl(url) if url else "",
            "source": self.company_name,
            "job_category": (job_category or "").strip(),
            "education": (education or "").strip(),
            "raw_data": extra,
        }
        return job
