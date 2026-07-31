#!/usr/bin/env python3
"""秋招行业分析仪表盘 generator.

Reads daily campus-recruitment snapshots from data/snapshots/, normalizes
them into dated analytical rows, and renders a single-file ECharts dashboard
showing job-posting trends, industry / company-type / regional distributions,
salary benchmarks, and a top-employer leaderboard.

Automation pattern: a daily crawler writes dated JSON snapshots to
data/snapshots/, then this script regenerates index.html.
"""

from __future__ import annotations

import html
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAPSHOT_DIR = ROOT / "data" / "snapshots"
ECHARTS_JS = ROOT / "echarts.min.js"
DASHBOARD_RUNTIME_JS = ROOT / "dashboard_runtime.js"
DASHBOARD_HTML = ROOT / "index.html"
DASHBOARD_DATA = ROOT / "dashboard_data.json"

DASHBOARD_TITLE = "秋招行业分析仪表盘"
DASHBOARD_SUBTITLE = "2027届秋季校园招聘市场动态监测"
TIMEZONE_LABEL = "Asia/Shanghai"
DEFAULT_RANGE = "30D"

# Static season-total top-employer leaderboard (independent of daily snapshots).
TOP_COMPANIES = [
    {"company": "农业银行", "industry": "银行", "company_type": "国企", "jobs": 18500, "salary_avg": 10000},
    {"company": "中国银行", "industry": "银行", "company_type": "国企", "jobs": 18200, "salary_avg": 11000},
    {"company": "工商银行", "industry": "银行", "company_type": "国企", "jobs": 17600, "salary_avg": 10500},
    {"company": "建设银行", "industry": "银行", "company_type": "国企", "jobs": 16800, "salary_avg": 10800},
    {"company": "比亚迪", "industry": "汽车制造", "company_type": "民企", "jobs": 5600, "salary_avg": 11000},
    {"company": "国家电网", "industry": "国企央企", "company_type": "国企", "jobs": 4800, "salary_avg": 9500},
    {"company": "字节跳动", "industry": "互联网科技", "company_type": "民企", "jobs": 4200, "salary_avg": 28000},
    {"company": "阿里巴巴", "industry": "互联网科技", "company_type": "民企", "jobs": 3800, "salary_avg": 26000},
    {"company": "腾讯", "industry": "互联网科技", "company_type": "民企", "jobs": 3500, "salary_avg": 27000},
    {"company": "华为", "industry": "互联网科技", "company_type": "民企", "jobs": 3200, "salary_avg": 25000},
    {"company": "中国移动", "industry": "国企央企", "company_type": "国企", "jobs": 2900, "salary_avg": 8800},
    {"company": "招商银行", "industry": "银行", "company_type": "民企", "jobs": 2600, "salary_avg": 13000},
    {"company": "美团", "industry": "互联网科技", "company_type": "民企", "jobs": 2200, "salary_avg": 23000},
    {"company": "百度", "industry": "互联网科技", "company_type": "民企", "jobs": 1800, "salary_avg": 24000},
    {"company": "普华永道", "industry": "咨询", "company_type": "外企", "jobs": 650, "salary_avg": 18000},
    {"company": "微软", "industry": "外企", "company_type": "外企", "jobs": 280, "salary_avg": 20000},
]


def fmt_num(value: float) -> str:
    return f"{value:,.0f}"


def fmt_salary(value: float) -> str:
    return f"¥{value:,.0f}"


def pct(value: float) -> str:
    return f"{value * 100:+.1f}%"


def read_sources() -> list[dict]:
    rows: list[dict] = []
    paths = sorted(SNAPSHOT_DIR.glob("*.json")) if SNAPSHOT_DIR.exists() else []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        batch = data.get("rows", [])
        for row in batch:
            row.setdefault("snapshot_date", data.get("snapshot_date"))
            row.setdefault("captured_at", data.get("captured_at"))
            row.setdefault("source", data.get("source"))
            row.setdefault("timezone", data.get("timezone"))
        rows.extend(batch)
    return rows


def normalize_snapshots(rows: list[dict]) -> list[dict]:
    normalized = []
    for raw in rows:
        row = dict(raw)
        row["date"] = str(row.get("date") or row.get("snapshot_date") or "")[:10]
        row["snapshot_date"] = str(row.get("snapshot_date") or row["date"])[:10]
        row["captured_at"] = str(row.get("captured_at") or "")
        row["industry"] = str(row.get("industry") or "其他")
        row["company_type"] = str(row.get("company_type") or "其他")
        row["region"] = str(row.get("region") or "其他")
        row["jobs"] = int(float(row.get("jobs") or 0))
        row["salary_avg"] = float(row.get("salary_avg") or 0)
        row["source"] = str(row.get("source") or "local snapshot")
        if row["date"]:
            normalized.append(row)

    latest_by_key: dict[tuple[str, str, str, str], dict] = {}
    for row in normalized:
        key = (row["date"], row["industry"], row["company_type"], row["region"])
        previous = latest_by_key.get(key)
        if previous is None or row["captured_at"] >= previous.get("captured_at", ""):
            latest_by_key[key] = row
    return sorted(latest_by_key.values(), key=lambda item: (item["date"], item["industry"]))


def make_daily_series(rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = defaultdict(lambda: {"date": "", "jobs": 0, "salary_wsum": 0.0, "salary_wcount": 0})
    for row in rows:
        item = grouped[row["date"]]
        item["date"] = row["date"]
        item["jobs"] += row["jobs"]
        item["salary_wsum"] += row["salary_avg"] * row["jobs"]
        item["salary_wcount"] += row["jobs"]
    return [
        {
            "date": item["date"],
            "jobs": item["jobs"],
            "salary_avg": round(item["salary_wsum"] / item["salary_wcount"]) if item["salary_wcount"] else 0,
        }
        for item in (grouped[key] for key in sorted(grouped))
    ]


def make_industry_series(rows: list[dict]) -> list[dict]:
    return [
        {
            "date": row["date"],
            "industry": row["industry"],
            "jobs": row["jobs"],
            "salary_wsum": round(row["salary_avg"] * row["jobs"]),
            "salary_wcount": row["jobs"],
        }
        for row in rows
    ]


def make_company_type_series(rows: list[dict]) -> list[dict]:
    return [
        {"date": row["date"], "company_type": row["company_type"], "jobs": row["jobs"]}
        for row in rows
    ]


def make_region_series(rows: list[dict]) -> list[dict]:
    return [
        {"date": row["date"], "region": row["region"], "jobs": row["jobs"]}
        for row in rows
    ]


def sum_between(rows: list[dict], start: str, end: str, field: str) -> float:
    return sum(float(row.get(field) or 0) for row in rows if start <= row["date"] <= end)


def weighted_salary(rows: list[dict], start: str, end: str) -> float:
    wsum = 0.0
    wcount = 0
    for row in rows:
        if start <= row["date"] <= end:
            wsum += row["salary_avg"] * row["jobs"]
            wcount += row["jobs"]
    return round(wsum / wcount) if wcount else 0


def make_dashboard_payload(rows: list[dict]) -> dict:
    daily = make_daily_series(rows)
    by_industry = make_industry_series(rows)
    by_company_type = make_company_type_series(rows)
    by_region = make_region_series(rows)
    top_companies = sorted(TOP_COMPANIES, key=lambda c: c["jobs"], reverse=True)
    dates = [item["date"] for item in daily]
    latest = dates[-1] if dates else ""
    start_30 = dates[-30] if len(dates) >= 30 else (dates[0] if dates else "")
    previous_start = dates[-60] if len(dates) >= 60 else (dates[0] if dates else "")
    previous_end = dates[-31] if len(dates) >= 31 else latest

    jobs_30 = sum_between(daily, start_30, latest, "jobs") if latest else 0
    previous_jobs = sum_between(daily, previous_start, previous_end, "jobs") if latest else 0
    jobs_delta = (jobs_30 - previous_jobs) / previous_jobs if previous_jobs else 0

    salary_30 = weighted_salary(rows, start_30, latest) if latest else 0
    previous_salary = weighted_salary(rows, previous_start, previous_end) if latest else 0
    salary_delta = (salary_30 - previous_salary) / previous_salary if previous_salary else 0

    daily_avg_30 = jobs_30 / 30 if jobs_30 else 0
    prev_daily_avg = previous_jobs / 30 if previous_jobs else 0
    daily_avg_delta = (daily_avg_30 - prev_daily_avg) / prev_daily_avg if prev_daily_avg else 0

    industries_30 = len({row["industry"] for row in rows if start_30 <= row["date"] <= latest}) if latest else 0

    latest_captured = max((row.get("captured_at", "") for row in rows), default="")

    source_snippets = {
        "jobTrend": """daily = make_daily_series(rows)
filtered = [row for row in daily if start_date <= row["date"] <= end_date]
series = [{"date": row["date"], "jobs": row["jobs"]} for row in filtered]""",
        "industryMix": """by_industry = make_industry_series(rows)
filtered = [row for row in by_industry if start_date <= row["date"] <= end_date]
grouped = sum jobs by industry for the active time range""",
        "companyTypeMix": """by_company_type = make_company_type_series(rows)
filtered = [row for row in by_company_type if start_date <= row["date"] <= end_date]
grouped = sum jobs by company_type for the active time range""",
        "regionDist": """by_region = make_region_series(rows)
filtered = [row for row in by_region if start_date <= row["date"] <= end_date]
grouped = sum jobs by region for the active time range""",
        "salaryIndustry": """by_industry = make_industry_series(rows)
filtered = [row for row in by_industry if start_date <= row["date"] <= end_date]
weighted_avg = sum(salary_wsum) / sum(salary_wcount) per industry""",
        "topCompanies": """TOP_COMPANIES static season-total leaderboard
sorted by jobs descending, bounded for display""",
    }

    return {
        "title": DASHBOARD_TITLE,
        "subtitle": DASHBOARD_SUBTITLE,
        "timezone": TIMEZONE_LABEL,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "freshness": {
            "latestDataDate": latest,
            "latestCapturedAt": latest_captured,
            "source": rows[-1]["source"] if rows else "No source rows",
        },
        "availableDates": dates,
        "defaultRange": DEFAULT_RANGE,
        "kpis": [
            {
                "id": "totalJobs",
                "label": "近30日岗位总数",
                "value": fmt_num(jobs_30),
                "delta": pct(jobs_delta),
                "detail": "对比上一30日窗口",
            },
            {
                "id": "avgSalary",
                "label": "加权平均月薪",
                "value": fmt_salary(salary_30),
                "delta": pct(salary_delta),
                "detail": "按岗位数加权",
            },
            {
                "id": "dailyAvg",
                "label": "日均发布岗位",
                "value": fmt_num(daily_avg_30),
                "delta": pct(daily_avg_delta),
                "detail": "近30日平均",
            },
            {
                "id": "activeIndustries",
                "label": "活跃行业数",
                "value": fmt_num(industries_30),
                "delta": f"{len(top_companies)} 家头部企业",
                "detail": "覆盖主要招聘赛道",
            },
        ],
        "datasets": {
            "daily": daily,
            "byIndustry": by_industry,
            "byCompanyType": by_company_type,
            "byRegion": by_region,
            "topCompanies": top_companies,
        },
        "sourceSnippets": source_snippets,
    }


def js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def json_script(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_kpi_block(block: dict) -> str:
    return f"""
    <section class="kpi-tile" id="{html.escape(block["id"])}">
      <p>{html.escape(block["label"])}</p>
      <strong>{html.escape(block["value"])}</strong>
      <span>{html.escape(block["delta"])}</span>
      <small>{html.escape(block["detail"])}</small>
    </section>
    """


def render_panel_actions(block: dict) -> str:
    edit = ""
    edit_command = ""
    if len(block.get("allowed_types", [])) > 1:
        options = "\n".join(
            f'<option value="{html.escape(kind)}"{" selected" if kind == block.get("initial_type") else ""}>{html.escape(kind)}</option>'
            for kind in block["allowed_types"]
        )
        edit_command = f"""<button onclick="toggleEdit('{html.escape(block["chart_id"])}')">Edit</button>"""
        edit = f"""
        <div class="edit-panel" id="edit-{html.escape(block["chart_id"])}">
          <label for="select-{html.escape(block["chart_id"])}">Type</label>
          <select id="select-{html.escape(block["chart_id"])}" onchange="setChartType('{html.escape(block["chart_id"])}', this.value)">
            {options}
          </select>
        </div>
        """
    return f"""
    <div class="chart-actions">
      {edit}
      <div class="toolbox">
        <button class="tool-button" aria-label="Panel actions" onclick="toggleMenu('{html.escape(block["chart_id"])}')"><span class="dot"></span><span class="dot"></span><span class="dot"></span></button>
        <div class="menu" id="menu-{html.escape(block["chart_id"])}">
          {edit_command}
          <button onclick="viewSource('{html.escape(block["source_key"])}')">View Data Source</button>
        </div>
      </div>
    </div>
    """


def infer_panel_span(block: dict) -> int:
    if block.get("span") is not None:
        span = int(block["span"])
        return span if span in (4, 6, 12) else 6
    if block["kind"] == "table":
        columns = block.get("columns", [])
        has_long_text = any(col.get("long_text") for col in columns)
        return 12 if len(columns) >= 6 or has_long_text else 6
    if block["kind"] == "chart":
        chart_type = str(block.get("initial_type") or "")
        dense_chart = chart_type in {"heatmap", "scatter"} or block.get("dense")
        many_categories = int(block.get("category_count") or 0) > 8
        return 12 if dense_chart or many_categories else 6
    if block["kind"] == "note":
        return 4 if block.get("compact") else 6
    return 6


def panel_span_attr(block: dict) -> str:
    span = infer_panel_span(block)
    return f'data-span="{span}"'


def render_chart_block(block: dict) -> str:
    return f"""
    <section class="dashboard-panel chart-panel" {panel_span_attr(block)} id="{html.escape(block["id"])}">
      <header>
        <div>
          <h2>{html.escape(block["title"])}</h2>
          <p>{html.escape(block["subtitle"])}</p>
        </div>
        {render_panel_actions(block)}
      </header>
      <div class="chart" id="{html.escape(block["chart_id"])}" role="img" aria-label="{html.escape(block["title"])}"></div>
      <footer>{html.escape(block["unit"])} | {html.escape(block["source_context"])}</footer>
    </section>
    """


def render_table_block(block: dict) -> str:
    columns = block["columns"]
    head = "".join(f"<th>{html.escape(col['label'])}</th>" for col in columns)
    return f"""
    <section class="dashboard-panel table-panel" {panel_span_attr(block)} id="{html.escape(block["id"])}">
      <header>
        <div>
          <h2>{html.escape(block["title"])}</h2>
          <p>{html.escape(block["subtitle"])}</p>
        </div>
        <div class="toolbox">
          <button class="tool-button" aria-label="Panel actions" onclick="toggleMenu('{html.escape(block["source_key"])}')"><span class="dot"></span><span class="dot"></span><span class="dot"></span></button>
          <div class="menu" id="menu-{html.escape(block["source_key"])}">
            <button onclick="viewSource('{html.escape(block["source_key"])}')">View Data Source</button>
          </div>
        </div>
      </header>
      <div class="table-scroll">
        <table id="{html.escape(block["table_id"])}">
          <thead><tr>{head}</tr></thead>
          <tbody></tbody>
        </table>
      </div>
      <footer>{html.escape(block["source_context"])}</footer>
    </section>
    """


def render_note_block(block: dict) -> str:
    return f"""
    <section class="dashboard-note" {panel_span_attr(block)} id="{html.escape(block["id"])}">
      <strong>{html.escape(block["title"])}</strong>
      <span>{html.escape(block["body"])}</span>
    </section>
    """


def build_dashboard_blocks(payload: dict) -> list[dict]:
    blocks = []
    blocks.extend({"kind": "kpi", **kpi} for kpi in payload["kpis"])
    blocks.extend(
        [
            {
                "kind": "chart",
                "id": "panel-job-trend",
                "chart_id": "jobTrend",
                "source_key": "jobTrend",
                "title": "每日岗位发布趋势",
                "subtitle": "按日统计的新增岗位数量",
                "unit": "岗位数",
                "source_context": "数据来源: GitHub校招仓库 + 企业官网爬虫",
                "allowed_types": ["line", "bar"],
                "initial_type": "line",
                "category_count": 60,
                "span": 12,
            },
            {
                "kind": "chart",
                "id": "panel-industry-mix",
                "chart_id": "industryMix",
                "source_key": "industryMix",
                "title": "行业岗位分布",
                "subtitle": "各行业岗位数量占比",
                "unit": "岗位数",
                "source_context": "数据来源: 爬虫清洗分类后聚合",
                "allowed_types": ["bar", "pie"],
                "initial_type": "bar",
                "category_count": 8,
            },
            {
                "kind": "chart",
                "id": "panel-company-type",
                "chart_id": "companyTypeMix",
                "source_key": "companyTypeMix",
                "title": "企业类型分布",
                "subtitle": "国企 / 民企 / 外企 / 事业单位",
                "unit": "岗位数",
                "source_context": "数据来源: companies.csv + AI分类",
                "allowed_types": ["pie", "bar"],
                "initial_type": "pie",
            },
            {
                "kind": "chart",
                "id": "panel-region-dist",
                "chart_id": "regionDist",
                "source_key": "regionDist",
                "title": "地域岗位分布",
                "subtitle": "主要城市岗位数量",
                "unit": "岗位数",
                "source_context": "数据来源: 岗位地点字段解析",
                "allowed_types": ["bar"],
                "initial_type": "bar",
                "category_count": 10,
            },
            {
                "kind": "chart",
                "id": "panel-salary-industry",
                "chart_id": "salaryIndustry",
                "source_key": "salaryIndustry",
                "title": "行业薪资对比",
                "subtitle": "各行业加权平均月薪",
                "unit": "元/月",
                "source_context": "数据来源: 正则+AI抽取薪资范围",
                "allowed_types": ["bar"],
                "initial_type": "bar",
                "category_count": 8,
            },
            {
                "kind": "table",
                "id": "panel-top-companies",
                "table_id": "topCompaniesTable",
                "source_key": "topCompanies",
                "title": "头部企业招聘榜",
                "subtitle": "本季招聘规模最大的企业",
                "source_context": "数据来源: 季度汇总统计",
                "columns": [
                    {"field": "company", "label": "企业"},
                    {"field": "industry", "label": "行业"},
                    {"field": "company_type", "label": "类型"},
                    {"field": "jobs", "label": "岗位数", "numeric": True},
                    {"field": "salary_avg", "label": "平均月薪", "numeric": True},
                ],
            },
            {
                "kind": "note",
                "id": "automation-note",
                "title": "数据更新机制",
                "body": "GitHub Actions 每日8:00自动爬取校招仓库与企业官网，清洗分类后写入 data/snapshots/，随后运行 python dashboard.py 刷新本仪表盘。",
            },
            {
                "kind": "note",
                "id": "compliance-note",
                "title": "数据声明",
                "body": "信息来源于公开渠道，仅供参考。岗位详情页标注数据来源与原文链接，不保证信息时效性。",
            },
        ]
    )
    return blocks


def render_dashboard_blocks(blocks: list[dict]) -> str:
    kpis = "\n".join(render_kpi_block(block) for block in blocks if block["kind"] == "kpi")
    panels = []
    for block in blocks:
        if block["kind"] == "chart":
            panels.append(render_chart_block(block))
        elif block["kind"] == "table":
            panels.append(render_table_block(block))
        elif block["kind"] == "note":
            panels.append(render_note_block(block))
    return f"""
    <section class="kpi-grid">{kpis}</section>
    <section class="panel-grid">{"".join(panels)}</section>
    """


ANALYSIS_LOGIC = """Analysis logic
- read_sources() loads daily JSON snapshots from data/snapshots/.
- normalize_snapshots() standardizes date, industry, company_type, region, jobs, salary_avg, source, and captured_at.
- duplicate rows are resolved by (date, industry, company_type, region), keeping the newest captured_at.
- make_daily_series() aggregates total jobs and weighted-average salary per date.
- make_industry_series() / make_company_type_series() / make_region_series() produce per-date dimensional breakdowns.
- dashboard_runtime.js applies client-side date filtering, then chart factories aggregate within the active range."""


def build_html(payload: dict) -> str:
    echarts = ECHARTS_JS.read_text(encoding="utf-8")
    runtime = DASHBOARD_RUNTIME_JS.read_text(encoding="utf-8")
    blocks = build_dashboard_blocks(payload)
    content = render_dashboard_blocks(blocks)
    initial_charts = [
        {"id": block["chart_id"], "type": block["initial_type"]}
        for block in blocks
        if block["kind"] == "chart"
    ]
    table_config = {
        "topCompaniesTable": {
            "dataset": "topCompanies",
            "sortField": "jobs",
            "sortDirection": "desc",
            "limit": 16,
            "columns": [
                {"field": "company"},
                {"field": "industry"},
                {"field": "company_type"},
                {"field": "jobs", "numeric": True},
                {"field": "salary_avg", "numeric": True},
            ],
        }
    }
    source_map = payload["sourceSnippets"]

    css = """
    :root {
      color-scheme: light;
      --ink: #2f3437;
      --muted: #68707a;
      --faint: #8b95a3;
      --line: #e1e5ea;
      --line-strong: #cbd3dc;
      --panel: #FAFAFA;
      --page: #ffffff;
      --surface: #FAFAFA;
      --soft: #f2f3f5;
      --soft-blue: #f3f6fb;
      --control-bg: rgba(255, 255, 255, 0.94);
      --topbar-bg: rgba(255, 255, 255, 0.96);
      --menu-bg: #ffffff;
      --modal-bg: #ffffff;
      --modal-backdrop: rgba(55, 53, 47, 0.34);
      --table-head: #FAFAFA;
      --table-hover: #f1f2ff;
      --chart-bg: #FAFAFA;
      --chart-text: #2f3437;
      --chart-muted: #68707a;
      --chart-line: #e1e5ea;
      --chart-primary: #2F6BFF;
      --chart-secondary: #00BFA6;
      --chart-tertiary: #FF7A3D;
      --chart-quaternary: #F45BB3;
      --chart-1: #F45BB3;
      --chart-2: #2F6BFF;
      --chart-3: #00BFA6;
      --chart-4: #FF7A3D;
      --chart-5: #9BD82E;
      --chart-6: #7C3AED;
      --chart-7: #FFD23F;
      --brand: #6979F8;
      --brand-hover: #9EA9FF;
      --brand-end: #CDD2FD;
      --brand-text: #ffffff;
      --accent: #2F6BFF;
      --accent-2: #00BFA6;
      --warn: #b7791f;
    }
    html[data-theme="trae-dark"] {
      color-scheme: dark;
      --ink: #f5f9fe;
      --muted: #9599a6;
      --faint: #666b75;
      --line: #2a2d31;
      --line-strong: #3a3f45;
      --panel: #1a1b1d;
      --page: #0c0c0d;
      --surface: #222427;
      --soft: #2a2d31;
      --soft-blue: #202123;
      --control-bg: #202123;
      --topbar-bg: rgba(12, 12, 13, 0.92);
      --menu-bg: #202123;
      --modal-bg: #1a1b1d;
      --modal-backdrop: rgba(0, 0, 0, 0.58);
      --table-head: #222427;
      --table-hover: #202123;
      --chart-bg: #222427;
      --chart-text: #d1d3db;
      --chart-muted: #9599a6;
      --chart-line: #2a2d31;
      --chart-primary: #28d9ff;
      --chart-secondary: #32f08c;
      --chart-tertiary: #f6c85f;
      --chart-quaternary: #ff6b9a;
      --chart-1: #32f08c;
      --chart-2: #28d9ff;
      --chart-3: #a78bfa;
      --chart-4: #f6c85f;
      --chart-5: #ff6b9a;
      --chart-6: #6ea8ff;
      --chart-7: #d1d3db;
      --brand: #32f08c;
      --brand-hover: #0fdc78;
      --brand-end: #32f08c;
      --brand-text: #0c0c0d;
      --accent: #32f08c;
      --accent-2: #0fdc78;
    }
    * { box-sizing: border-box; }
    html { background: var(--page); }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      background: var(--page);
      color: var(--ink);
      font-size: 1rem;
      line-height: 1.55;
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
    }
    .topbar {
      position: sticky;
      top: 0;
      z-index: 20;
      border-bottom: 1px solid var(--line);
      background: var(--topbar-bg);
      backdrop-filter: blur(12px);
    }
    .topbar-inner {
      max-width: 1320px;
      margin: 0 auto;
      padding: 14px 22px;
      display: grid;
      grid-template-columns: minmax(260px, 1fr) auto;
      gap: 18px;
      align-items: center;
    }
    h1, h2, p { margin: 0; }
    h1 { font-size: 22px; font-weight: 500; letter-spacing: 0; }
    .subtitle, .freshness, .range-label, .dashboard-panel p, footer, small {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      font-weight: 400;
    }
    .controls {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: flex-end;
      gap: 10px;
    }
    .range-label { display: none; }
    .segmented {
      display: inline-flex;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: var(--control-bg);
    }
    .segmented button, .menu button, .edit-panel button {
      border: 0;
      background: transparent;
      color: var(--ink);
      font: inherit;
      cursor: pointer;
    }
    .segmented button {
      min-width: 44px;
      height: 34px;
      padding: 0 10px;
      border-right: 1px solid var(--line);
      font-size: 13px;
      font-weight: 400;
    }
    .segmented button:last-child { border-right: 0; }
    .segmented button.active { background: var(--brand); color: var(--brand-text); font-weight: 500; }
    .theme-switch button.active { background: var(--brand); color: var(--brand-text); }
    .theme-switch button {
      width: 38px;
      min-width: 38px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0;
    }
    .theme-switch svg {
      width: 16px;
      height: 16px;
      stroke-width: 2;
    }
    .date-fields { display: inline-flex; align-items: center; gap: 6px; }
    input[type="date"] {
      height: 34px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0 8px;
      background: var(--control-bg);
      color: var(--ink);
      font: inherit;
      font-size: 13px;
      font-weight: 400;
    }
    .dashboard-shell {
      max-width: 1320px;
      margin: 0 auto;
      padding: 18px 22px 44px;
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .kpi-tile {
      min-height: 126px;
      padding: 15px;
      display: grid;
      align-content: space-between;
      gap: 8px;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 12px;
    }
    .kpi-tile:first-child {
      background: linear-gradient(135deg, var(--brand) 0%, var(--brand-hover) 58%, var(--brand-end) 100%);
      border-color: var(--brand);
    }
    .kpi-tile p { color: var(--muted); font-size: 13px; font-weight: 500; }
    .kpi-tile strong { font-size: 28px; font-weight: 500; letter-spacing: 0; }
    .kpi-tile span { color: var(--ink); font-size: 15px; font-weight: 500; line-height: 1.35; }
    .kpi-tile small { font-size: 13px; font-weight: 400; }
    .kpi-tile:first-child p,
    .kpi-tile:first-child strong,
    .kpi-tile:first-child span,
    .kpi-tile:first-child small { color: var(--brand-text); }
    .panel-grid {
      display: grid;
      grid-template-columns: repeat(12, minmax(0, 1fr));
      gap: 20px 16px;
    }
    .dashboard-panel {
      min-height: 360px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      background: transparent;
      border: 0;
      border-radius: 0;
      padding: 0;
    }
    [data-span="4"] { grid-column: span 4; }
    [data-span="6"] { grid-column: span 6; }
    [data-span="12"] { grid-column: 1 / -1; }
    .dashboard-note {
      min-height: 180px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: transparent;
    }
    .dashboard-panel header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      min-height: 42px;
    }
    .dashboard-panel h2 { font-size: 17px; font-weight: 500; letter-spacing: 0; }
    .chart {
      width: 100%;
      height: 276px;
      min-height: 276px;
      padding: 8px 0 6px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--chart-bg);
    }
    [data-span="12"] .chart { height: 320px; min-height: 320px; }
    .chart-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
      flex: 0 0 auto;
      position: relative;
      z-index: 12;
    }
    .toolbox { position: relative; flex: 0 0 auto; }
    .tool-button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 3px;
      width: 34px;
      height: 30px;
      border: 1px solid var(--line-strong);
      border-radius: 999px;
      background: var(--control-bg);
      color: var(--muted);
      cursor: pointer;
      font-size: 0;
      line-height: 0;
      padding: 0;
      opacity: 0;
      transition: opacity 140ms ease, background-color 140ms ease;
    }
    .tool-button .dot {
      display: block;
      width: 3px;
      height: 3px;
      border-radius: 50%;
      background: currentColor;
    }
    .dashboard-panel:hover .tool-button,
    .dashboard-panel:focus-within .tool-button,
    .dashboard-note:hover .tool-button,
    .dashboard-note:focus-within .tool-button { opacity: 1; }
    .menu {
      display: none;
      position: absolute;
      right: 0;
      top: 34px;
      z-index: 40;
      width: 188px;
      padding: 6px;
      border: 1px solid var(--line-strong);
      border-radius: 8px;
      background: var(--menu-bg);
      box-shadow: 0 8px 18px rgba(32, 33, 36, 0.12);
    }
    .menu.open { display: block; }
    .edit-panel {
      display: none;
      align-items: center;
      gap: 6px;
      height: 28px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--control-bg);
      color: var(--muted);
      font-size: 13px;
    }
    .edit-panel.open { display: flex; }
    .edit-panel label {
      padding-left: 8px;
      white-space: nowrap;
    }
    .edit-panel select {
      height: 26px;
      border: 0;
      border-left: 1px solid var(--line);
      border-radius: 0 5px 5px 0;
      padding: 0 24px 0 7px;
      background: transparent;
      color: var(--ink);
      font: inherit;
      font-size: 13px;
      outline: none;
      cursor: pointer;
    }
    .menu button {
      display: block;
      width: 100%;
      border: 0;
      background: transparent;
      padding: 8px 10px;
      border-radius: 6px;
      text-align: left;
      cursor: pointer;
      color: var(--ink);
      font: inherit;
      font-size: 13px;
    }
    .menu button:hover, .menu button:focus-visible {
      background: var(--soft-blue);
      outline: none;
    }
    .table-scroll {
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--surface);
    }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { padding: 10px; border-bottom: 1px solid var(--line); text-align: left; white-space: nowrap; }
    th { color: var(--muted); font-weight: 500; background: var(--table-head); }
    td.num { text-align: right; font-variant-numeric: tabular-nums; }
    tbody tr:last-child td { border-bottom: 0; }
    tbody tr:hover td { background: var(--table-hover); }
    .modal-backdrop {
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background: var(--modal-backdrop);
      z-index: 50;
    }
    .modal-backdrop.open { display: flex; }
    .modal {
      width: min(860px, 100%);
      max-height: min(780px, 92vh);
      overflow: auto;
      border-radius: 16px;
      background: var(--modal-bg);
      border: 1px solid var(--line-strong);
      box-shadow: 0 18px 48px rgba(55, 53, 47, 0.18);
    }
    .modal-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      padding: 18px 20px 14px;
      border-bottom: 1px solid var(--line);
    }
    .modal-head h3 {
      margin: 0;
      font-size: 16px;
      line-height: 1.4;
      font-weight: 600;
    }
    .modal-subtitle {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
    }
    .modal-body { padding: 18px 20px 20px; }
    .source-section + .source-section { margin-top: 16px; }
    .source-section h4 {
      margin: 0 0 8px;
      color: var(--ink);
      font-size: 14px;
      line-height: 1.4;
      font-weight: 600;
    }
    .code-wrap { position: relative; }
    pre {
      margin: 0;
      padding: 14px;
      overflow: auto;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: var(--soft);
      color: var(--ink);
      font-size: 12px;
      line-height: 1.5;
    }
    .close {
      width: 32px;
      height: 32px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 0;
      border-radius: 999px;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      padding: 0;
    }
    .close svg { width: 18px; height: 18px; stroke-width: 2.1; }
    .close:hover, .close:focus-visible { background: var(--soft); outline: none; }
    .copy-button {
      position: absolute;
      right: 8px;
      top: 8px;
      width: 28px;
      height: 28px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--control-bg);
      color: var(--muted);
      cursor: pointer;
    }
    .copy-button svg { width: 15px; height: 15px; stroke-width: 2; }
    .copy-button:hover, .copy-button:focus-visible {
      background: var(--soft);
      color: var(--ink);
      outline: none;
    }
    @media (max-width: 900px) {
      .topbar-inner { grid-template-columns: 1fr; }
      .controls { justify-content: flex-start; }
      .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .dashboard-panel, .dashboard-note, [data-span] { grid-column: 1 / -1; }
    }
    @media (max-width: 620px) {
      .topbar-inner, .dashboard-shell { padding-left: 14px; padding-right: 14px; }
      .kpi-grid { grid-template-columns: 1fr; }
      .segmented { width: 100%; }
      .segmented button { flex: 1; min-width: 0; }
      .date-fields { width: 100%; }
      input[type="date"] { min-width: 0; width: 100%; }
      .chart { height: 240px; min-height: 240px; }
    }
    """

    chart_js = f"""
    const dashboardPayload = {json_script(payload)};
    function cssToken(name) {{
      return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }}
    function chartTheme() {{
      return {{
        text: cssToken("--chart-text"),
        muted: cssToken("--chart-muted"),
        line: cssToken("--chart-line"),
        primary: cssToken("--chart-primary"),
        secondary: cssToken("--chart-secondary"),
        tertiary: cssToken("--chart-tertiary"),
        quaternary: cssToken("--chart-quaternary"),
        palette: [1, 2, 3, 4, 5, 6, 7].map(index => cssToken("--chart-" + index))
      }};
    }}
    function axisStyle(extra) {{
      const theme = chartTheme();
      const base = {{
        axisLabel: {{ color: theme.muted }},
        axisLine: {{ lineStyle: {{ color: theme.line }} }},
        axisTick: {{ lineStyle: {{ color: theme.line }} }},
        splitLine: {{ lineStyle: {{ color: theme.line }} }}
      }};
      const merged = Object.assign({{}}, base, extra || {{}});
      merged.axisLabel = Object.assign({{}}, base.axisLabel, (extra || {{}}).axisLabel || {{}});
      return merged;
    }}
    function chartBase(...colorKeys) {{
      const theme = chartTheme();
      return {{
        textStyle: {{ color: theme.text }},
        color: colorKeys.map(key => theme[key] || key)
      }};
    }}
    function fmtJobs(value) {{
      return value >= 10000 ? (value / 10000).toFixed(1) + "万" : value.toLocaleString();
    }}
    function fmtSal(value) {{
      return "¥" + (value / 1000).toFixed(1) + "k";
    }}
    const categoryColorKeys = {{
      "互联网科技": "primary",
      "银行": "secondary",
      "证券基金": "tertiary",
      "国企央企": "quaternary",
      "外企": "chart-5",
      "汽车制造": "chart-6",
      "咨询": "chart-7",
      "事业单位": "#8A94A3",
      "国企": "primary",
      "民企": "secondary",
      "Other": "#8A94A3",
      "其他": "#8A94A3",
      "Unknown": "#A7ADB6"
    }};
    function categoricalColor(name, index) {{
      const key = String(name || "").trim();
      const theme = chartTheme();
      const tokenOrColor = categoryColorKeys[key];
      return theme[tokenOrColor] || tokenOrColor || theme.palette[index % theme.palette.length];
    }}
    const chartFactories = {{
      jobTrend: function(type, filteredRows) {{
        const rows = filteredRows("daily");
        return {{
          ...chartBase("primary"),
          tooltip: {{ trigger: "axis", valueFormatter: value => fmtJobs(value) + " 岗位" }},
          grid: {{ left: 56, right: 18, top: 28, bottom: 36 }},
          xAxis: axisStyle({{ type: "category", data: rows.map(row => row.date), axisLabel: {{ hideOverlap: true }} }}),
          yAxis: axisStyle({{ type: "value", axisLabel: {{ formatter: value => fmtJobs(value) }} }}),
          series: [{{ type: type, smooth: type === "line", data: rows.map(row => row.jobs), areaStyle: type === "line" ? {{ opacity: 0.1 }} : undefined, barMaxWidth: 18 }}]
        }};
      }},
      industryMix: function(type, filteredRows) {{
        const totals = new Map();
        filteredRows("byIndustry").forEach(row => totals.set(row.industry, (totals.get(row.industry) || 0) + row.jobs));
        const rows = Array.from(totals, ([industry, jobs]) => ({{ industry, jobs }})).sort((a, b) => a.jobs - b.jobs);
        if (type === "pie") {{
          const sorted = rows.slice().reverse();
          return {{
            ...chartBase(),
            color: sorted.map((row, index) => categoricalColor(row.industry, index)),
            tooltip: {{ trigger: "item", formatter: p => p.name + ": " + fmtJobs(p.value) + " (" + p.percent + "%)" }},
            legend: {{ type: "scroll", orient: "vertical", right: 10, top: "center", textStyle: {{ color: chartTheme().muted }} }},
            series: [{{ type: "pie", radius: ["42%", "70%"], center: ["38%", "50%"], data: sorted.map(row => ({{ name: row.industry, value: row.jobs }})), label: {{ formatter: p => p.percent + "%" }} }}]
          }};
        }}
        return {{
          ...chartBase("secondary"),
          tooltip: {{ trigger: "axis", valueFormatter: value => fmtJobs(value) + " 岗位" }},
          grid: {{ left: 88, right: 24, top: 24, bottom: 30 }},
          xAxis: axisStyle({{ type: "value", axisLabel: {{ formatter: value => fmtJobs(value) }} }}),
          yAxis: axisStyle({{ type: "category", data: rows.map(row => row.industry) }}),
          series: [{{ type: "bar", data: rows.map((row, index) => ({{ value: row.jobs, itemStyle: {{ color: categoricalColor(row.industry, index) }} }})), barMaxWidth: 26 }}]
        }};
      }},
      companyTypeMix: function(type, filteredRows) {{
        const totals = new Map();
        filteredRows("byCompanyType").forEach(row => totals.set(row.company_type, (totals.get(row.company_type) || 0) + row.jobs));
        const rows = Array.from(totals, ([company_type, jobs]) => ({{ company_type, jobs }})).sort((a, b) => b.jobs - a.jobs);
        if (type === "bar") {{
          const sorted = rows.slice().reverse();
          return {{
            ...chartBase("primary"),
            tooltip: {{ trigger: "axis", valueFormatter: value => fmtJobs(value) + " 岗位" }},
            grid: {{ left: 80, right: 24, top: 24, bottom: 30 }},
            xAxis: axisStyle({{ type: "value", axisLabel: {{ formatter: value => fmtJobs(value) }} }}),
            yAxis: axisStyle({{ type: "category", data: sorted.map(row => row.company_type) }}),
            series: [{{ type: "bar", data: sorted.map((row, index) => ({{ value: row.jobs, itemStyle: {{ color: categoricalColor(row.company_type, index) }} }})), barMaxWidth: 30 }}]
          }};
        }}
        return {{
          ...chartBase(),
          color: rows.map((row, index) => categoricalColor(row.company_type, index)),
          tooltip: {{ trigger: "item", formatter: p => p.name + ": " + fmtJobs(p.value) + " (" + p.percent + "%)" }},
          legend: {{ type: "scroll", orient: "vertical", right: 10, top: "center", textStyle: {{ color: chartTheme().muted }} }},
          series: [{{ type: "pie", radius: ["42%", "70%"], center: ["38%", "50%"], data: rows.map(row => ({{ name: row.company_type, value: row.jobs }})), label: {{ formatter: p => p.percent + "%" }} }}]
        }};
      }},
      regionDist: function(type, filteredRows) {{
        const totals = new Map();
        filteredRows("byRegion").forEach(row => totals.set(row.region, (totals.get(row.region) || 0) + row.jobs));
        const rows = Array.from(totals, ([region, jobs]) => ({{ region, jobs }})).sort((a, b) => a.jobs - b.jobs);
        return {{
          ...chartBase("primary"),
          tooltip: {{ trigger: "axis", valueFormatter: value => fmtJobs(value) + " 岗位" }},
          grid: {{ left: 70, right: 24, top: 24, bottom: 30 }},
          xAxis: axisStyle({{ type: "value", axisLabel: {{ formatter: value => fmtJobs(value) }} }}),
          yAxis: axisStyle({{ type: "category", data: rows.map(row => row.region) }}),
          series: [{{ type: "bar", data: rows.map(row => row.jobs), barMaxWidth: 26, itemStyle: {{ borderRadius: [0, 4, 4, 0] }} }}]
        }};
      }},
      salaryIndustry: function(type, filteredRows) {{
        const grouped = new Map();
        filteredRows("byIndustry").forEach(row => {{
          const item = grouped.get(row.industry) || {{ industry: row.industry, wsum: 0, wcount: 0 }};
          item.wsum += row.salary_wsum;
          item.wcount += row.salary_wcount;
          grouped.set(row.industry, item);
        }});
        const rows = Array.from(grouped.values()).map(item => ({{
          industry: item.industry,
          salary: item.wcount ? Math.round(item.wsum / item.wcount) : 0
        }})).sort((a, b) => a.salary - b.salary);
        return {{
          ...chartBase("tertiary"),
          tooltip: {{ trigger: "axis", valueFormatter: value => fmtSal(value) + "/月" }},
          grid: {{ left: 88, right: 24, top: 24, bottom: 30 }},
          xAxis: axisStyle({{ type: "value", axisLabel: {{ formatter: value => fmtSal(value) }} }}),
          yAxis: axisStyle({{ type: "category", data: rows.map(row => row.industry) }}),
          series: [{{ type: "bar", data: rows.map((row, index) => ({{ value: row.salary, itemStyle: {{ color: categoricalColor(row.industry, index) }} }})), barMaxWidth: 26 }}]
        }};
      }}
    }};
    const sourceMap = {json_script(source_map)};
    setupDashboardRuntime({{
      datasets: dashboardPayload.datasets,
      availableDates: dashboardPayload.availableDates,
      defaultRange: dashboardPayload.defaultRange,
      initialCharts: {json_script(initial_charts)},
      chartFactories,
      sourceMap,
      tables: {json_script(table_config)},
      fullScript: {js_string(ANALYSIS_LOGIC)},
      modalSubtitlePrefix: "面板数据来源: "
    }});
    """

    return f"""<!-- Generated by Trae Work -->
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(payload["title"])}</title>
  <style>{css}</style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div>
        <h1>{html.escape(payload["title"])}</h1>
        <p class="subtitle">{html.escape(payload["subtitle"])}</p>
        <p class="freshness" id="dataFreshness">最新数据: {html.escape(payload["freshness"]["latestDataDate"])} | 采集时间: {html.escape(payload["freshness"]["latestCapturedAt"])} | {html.escape(payload["timezone"])}</p>
      </div>
      <div class="controls" aria-label="仪表盘时间控件">
        <span class="range-label" id="activeRangeLabel"></span>
        <div class="segmented" aria-label="时间预设">
          <button data-range-preset="7D">7天</button>
          <button data-range-preset="30D">30天</button>
          <button data-range-preset="MTD">月初至今</button>
          <button data-range-preset="QTD">本季至今</button>
          <button data-range-preset="YTD">年初至今</button>
          <button data-range-preset="ALL">全部</button>
        </div>
        <div class="date-fields">
          <input id="rangeStart" data-range-input type="date" aria-label="开始日期">
          <input id="rangeEnd" data-range-input type="date" aria-label="结束日期">
        </div>
        <div class="segmented theme-switch" aria-label="主题">
          <button data-theme-choice="light" type="button" aria-label="浅色主题" title="浅色">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
              <circle cx="12" cy="12" r="4"></circle>
              <path d="M12 2v2"></path>
              <path d="M12 20v2"></path>
              <path d="m4.93 4.93 1.41 1.41"></path>
              <path d="m17.66 17.66 1.41 1.41"></path>
              <path d="M2 12h2"></path>
              <path d="M20 12h2"></path>
              <path d="m6.34 17.66-1.41 1.41"></path>
              <path d="m19.07 4.93-1.41 1.41"></path>
            </svg>
          </button>
          <button data-theme-choice="trae-dark" type="button" aria-label="深色主题" title="深色">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
              <path d="M20.99 13.53A8.5 8.5 0 1 1 10.47 3.01 7 7 0 0 0 20.99 13.53Z"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </header>
  <main class="dashboard-shell">
    {content}
  </main>
  <div id="modalBackdrop" class="modal-backdrop" role="dialog" aria-modal="true">
    <section class="modal">
      <div class="modal-head">
        <div>
          <h3 id="modalTitle">数据来源</h3>
          <p class="modal-subtitle" id="modalSubtitle"></p>
        </div>
        <button class="close" aria-label="关闭" onclick="closeModal()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
            <path d="M18 6 6 18"></path>
            <path d="m6 6 12 12"></path>
          </svg>
        </button>
      </div>
      <div class="modal-body">
        <section class="source-section">
          <h4>面板数据转换</h4>
          <div class="code-wrap">
            <button class="copy-button" aria-label="复制数据转换代码" onclick="copyCode('modalSnippet', this)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                <rect x="9" y="9" width="11" height="11" rx="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
            </button>
            <pre><code id="modalSnippet"></code></pre>
          </div>
        </section>
        <section class="source-section">
          <h4>分析逻辑</h4>
          <div class="code-wrap">
            <button class="copy-button" aria-label="复制分析逻辑" onclick="copyCode('modalCode', this)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                <rect x="9" y="9" width="11" height="11" rx="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
            </button>
            <pre><code id="modalCode"></code></pre>
          </div>
        </section>
      </div>
    </section>
  </div>
  <script>{echarts}</script>
  <script>{runtime}</script>
  <script>{chart_js}</script>
</body>
</html>
"""


def main() -> None:
    rows = normalize_snapshots(read_sources())
    payload = make_dashboard_payload(rows)
    with DASHBOARD_DATA.open("w", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(payload, indent=2, ensure_ascii=False))
    with DASHBOARD_HTML.open("w", encoding="utf-8", newline="") as handle:
        handle.write(build_html(payload))
    print(f"Wrote {DASHBOARD_HTML}")
    print(f"Wrote {DASHBOARD_DATA}")


if __name__ == "__main__":
    main()
