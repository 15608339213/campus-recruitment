"""数据清洗管线。

负责将各数据源抓取到的原始 job dict 清洗为标准化结构，主要包含：

    - :func:`clean_jobs`           清洗原始数据，输出标准化 job dict 列表
    - :func:`deduplicate`          基于 hash(title + company + location) 去重
    - :func:`classify_company_type` 企业类型识别（国企/民企/外企/事业单位）
    - :func:`parse_salary`         薪资解析（支持中文多种表达，归一化为元/月）
    - :func:`parse_deadline`       截止时间解析（支持中文日期表达）
    - :func:`extract_tags`         从描述中提取技能/福利标签

数据结构使用 :class:`Job` dataclass 定义。
"""
from __future__ import annotations

import calendar
import csv
import hashlib
import logging
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional

from dateutil import parser as dateparser

logger = logging.getLogger(__name__)

#: companies.csv 所在目录
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_COMPANIES_CSV = os.path.join(_BASE_DIR, "companies.csv")
_EDU_CSV = os.path.join(_BASE_DIR, "edu_domains.csv")


# ====================================================================== #
# 数据结构
# ====================================================================== #
@dataclass
class Job:
    """标准化岗位数据结构（dataclass）。"""

    title: str = ""
    company: str = ""
    company_type: str = ""          # 国企/民企/外企/事业单位
    location: str = ""
    salary_min: int = 0             # 归一化为元/月
    salary_max: int = 0             # 归一化为元/月
    salary_unit: str = ""           # 原始单位说明，如 "元/月·14薪"
    salary_raw: str = ""            # 原始薪资字符串
    description: str = ""
    requirement: str = ""
    deadline: str = ""              # 标准化日期 YYYY-MM-DD
    deadline_raw: str = ""          # 原始截止时间字符串
    tags: list = field(default_factory=list)
    url: str = ""
    source: str = ""
    source_repo: str = ""
    education: str = ""             # 本科/硕士/博士/大专
    job_category: str = ""          # 技术/产品/运营/金融...
    job_type: str = "校招"          # 校招/实习/社招
    experience: str = ""
    job_hash: str = ""              # hash(title + company + location)
    raw_data: dict = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ====================================================================== #
# 企业类型识别
# ====================================================================== #
_COMPANIES_CACHE: Optional[dict[str, str]] = None


def _load_companies() -> dict[str, str]:
    """加载 companies.csv，构建「名称/别名 -> 类型」映射并缓存。"""
    global _COMPANIES_CACHE
    if _COMPANIES_CACHE is not None:
        return _COMPANIES_CACHE

    mapping: dict[str, str] = {}
    if os.path.exists(_COMPANIES_CSV):
        try:
            with open(_COMPANIES_CSV, encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    name = (row.get("name") or "").strip()
                    ctype = (row.get("type") or "").strip()
                    aliases = (row.get("aliases") or "").strip()
                    if name:
                        mapping[name] = ctype
                    for alias in aliases.split("|"):
                        alias = alias.strip()
                        if alias:
                            mapping[alias] = ctype
        except Exception as exc:  # noqa: BLE001
            logger.warning("加载 companies.csv 失败: %s", exc)
    _COMPANIES_CACHE = mapping
    return mapping


def classify_company_type(company_name: str) -> str:
    """识别企业类型：国企/民企/外企/事业单位。

    优先查 companies.csv 精确/包含匹配；未命中时按名称特征启发式推断。
    """
    if not company_name:
        return ""
    mapping = _load_companies()
    name = company_name.strip()

    # 1) 精确匹配（含别名）
    if name in mapping:
        return mapping[name]

    # 2) 包含匹配：CSV 中的别名出现在企业名中
    for alias, ctype in mapping.items():
        if alias and len(alias) >= 2 and alias in name:
            return ctype

    # 3) 启发式推断
    if re.search(r"(银行|集团)$", name) and not re.search(
        r"(科技|互联|网络|控股|资本)", name
    ):
        return "国企"
    if re.search(r"(局|院|所|中心|委员会|研究院)$", name):
        return "事业单位"
    if re.search(r"(中国|国家|全国|中央)", name):
        return "国企"
    # 含外资品牌特征
    if re.search(
        r"(Microsoft|Google|Amazon|Apple|Intel|NVIDIA|Qualcomm|Cisco|IBM|SAP"
        r"|Samsung|Sony|Deloitte|PwC|Ernst|KPMG|McKinsey)",
        name,
        re.I,
    ):
        return "外企"
    return "民企"


# ====================================================================== #
# 薪资解析
# ====================================================================== #
def parse_salary(salary_str: str) -> tuple[int, int, str]:
    """解析薪资字符串，返回 ``(min, max, unit)``。

    min/max 归一化为 **元/月**（年薪除以 12，日薪按 22 个工作日折算），
    unit 保留原始单位描述信息。

    支持的表达式::

        "15-25K"          -> (15000, 25000, "元/月")
        "15-25K·14薪"     -> (15000, 25000, "元/月·14薪")
        "8000-12000元/月" -> (8000, 12000, "元/月")
        "20-40万/年"      -> (16666, 33333, "万/年(折算月)")
        "1.5万-2.5万/月"  -> (15000, 25000, "元/月")
        "300元/天"        -> (6600, 6600, "元/天(折算月)")
        "20W-40W"         -> (16666, 33333, "万/年(折算月)")  # W 默认按年薪
        "面议"            -> (0, 0, "面议")
    """
    s = (salary_str or "").strip()
    if not s:
        return (0, 0, "")

    # 面议类
    if re.search(r"面议|另议|negotiable|薪资面谈", s, re.I):
        return (0, 0, "面议")

    original = s
    work = s.replace("～", "~").replace("—", "-").replace("–", "-")

    # 单位判定
    is_year = bool(re.search(r"/\s*年|年薪|每年|annual|/y\b", work, re.I))
    is_day = bool(re.search(r"/\s*天|日薪|每天|/d\b", work, re.I))
    # 14薪 / 16薪 中的乘数
    m_extra = re.search(r"(\d+)\s*薪", work)
    extra_months = int(m_extra.group(1)) if m_extra else 0

    # 万 / W 模式（"20万" 或 "20W"）
    wan_mode = bool(re.search(r"万|(?<![a-zA-Z])w(?![a-zA-Z])", work, re.I))
    # K 模式
    k_mode = bool(re.search(r"[kK]", work)) and not wan_mode

    # 提取所有数字
    nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", work)]
    # 去掉 "14薪" 的乘数
    if extra_months:
        nums = [n for n in nums if n != extra_months]
    if not nums:
        return (0, 0, original)

    if len(nums) == 1:
        lo = hi = nums[0]
    else:
        lo, hi = nums[0], nums[1]
        if lo > hi:
            lo, hi = hi, lo

    def to_yuan_monthly(val: float) -> int:
        if wan_mode:
            val = val * 10000.0
        elif k_mode:
            val = val * 1000.0
        if is_year:
            val = val / 12.0
        elif is_day:
            val = val * 22.0  # 约 22 个工作日/月
        return int(round(val))

    lo_m = to_yuan_monthly(lo)
    hi_m = to_yuan_monthly(hi)

    # 构造单位描述
    if is_year:
        unit = ("万/年" if wan_mode else ("元/年" if not k_mode else "K/年")) + "(折算月)"
    elif is_day:
        unit = "元/天(折算月)"
    elif wan_mode:
        unit = "万/月(折算元)"
    elif k_mode:
        unit = "K/月(折算元)"
    else:
        unit = "元/月"
    if extra_months:
        unit += f"·{extra_months}薪"

    return (lo_m, hi_m, unit)


# ====================================================================== #
# 截止时间解析
# ====================================================================== #
def _last_day(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _safe_date(year: int, month: int, day: int) -> str:
    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        # 修正非法日期（如 2 月 30 日）
        try:
            return datetime(year, month, min(day, _last_day(year, month))).strftime(
                "%Y-%m-%d"
            )
        except ValueError:
            return ""


def parse_deadline(date_str: str) -> str:
    """解析截止时间，返回标准日期 ``YYYY-MM-DD``。

    支持中文日期表达::

        "2024年10月31日"      -> "2024-10-31"
        "2024-10-31"          -> "2024-10-31"
        "2024.10.31"          -> "2024-10-31"
        "10月31日"            -> "2024-10-31"（自动补当前年/顺延到明年）
        "2024年10月"          -> "2024-10-31"（取月末）
        "10月底" / "10月初"   -> 月末 / 月初
        "尽快" / "招满即止"   -> "" （无明确截止）
    """
    s = (date_str or "").strip()
    if not s:
        return ""

    now = datetime.now()

    # 无明确截止时间
    if re.search(r"尽快|尽早|招满即止|额满即止|长期有效|rolling|随时|未定", s, re.I):
        return ""

    # 去除常见前缀
    s2 = re.sub(r"^(截止|截止时间|报名截止|投递截止|deadline)[：:\s]*", "", s, flags=re.I)

    # 1) 完整中文日期: 2024年10月31日
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?", s2)
    if m:
        return _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # 2) 年月: 2024年10月
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月", s2)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        return _safe_date(y, mo, _last_day(y, mo))

    # 3) 标准分隔符日期: 2024-10-31 / 2024.10.31 / 2024/10/31
    m = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s2)
    if m:
        return _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # 4) 月日: 10月31日（自动补年，已过则顺延明年）
    m = re.search(r"(\d{1,2})\s*月\s*(\d{1,2})\s*日?", s2)
    if m:
        mo, d = int(m.group(1)), int(m.group(2))
        y = now.year
        try:
            if datetime(y, mo, d) < now - timedelta(days=1):
                y += 1
        except ValueError:
            pass
        return _safe_date(y, mo, d)

    # 5) 月底/月初/月中: 10月底 / 10月末 / 10月初 / 10月中
    m = re.search(r"(\d{1,2})\s*月(底|末|初|中)", s2)
    if m:
        mo = int(m.group(1))
        pos = m.group(2)
        y = now.year
        if pos in ("底", "末"):
            d = _last_day(y, mo)
        elif pos == "初":
            d = 1
        else:
            d = 15
        return _safe_date(y, mo, d)

    # 6) 仅月份: 10月（取月末）
    m = re.search(r"(\d{1,2})\s*月", s2)
    if m:
        mo = int(m.group(1))
        y = now.year
        try:
            if datetime(y, mo, 1) < now.replace(day=1) - timedelta(days=1):
                y += 1
        except ValueError:
            pass
        return _safe_date(y, mo, _last_day(y, mo))

    # 7) dateutil 兜底
    try:
        dt = dateparser.parse(s2, fuzzy=True, default=now)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, OverflowError, TypeError):
        pass

    return ""


# ====================================================================== #
# 标签提取
# ====================================================================== #
#: 技能标签 -> 关键词列表
TAG_KEYWORDS: dict[str, list[str]] = {
    "Python": ["python", "django", "flask", "fastapi"],
    "Java": ["java", "spring", "springboot", "spring boot", "mybatis", "jvm"],
    "Go": ["golang", "go语言", "go开发", "go"],
    "C/C++": ["c++", "c语言", "c/c++", "cpp"],
    "Rust": ["rust"],
    "JavaScript": ["javascript", "js开发"],
    "TypeScript": ["typescript"],
    "前端": ["前端", "frontend", "html5", "css3", "vue", "react", "angular", "小程序"],
    "后端": ["后端", "backend", "服务端", "服务端开发"],
    "全栈": ["全栈", "fullstack", "full stack"],
    "算法": ["算法", "algorithm", "机器学习", "深度学习", "ai算法", "推荐算法"],
    "NLP": ["nlp", "自然语言", "文本处理"],
    "CV": ["计算机视觉", "图像处理", "cv算法", "目标检测"],
    "数据分析": ["数据分析", "数据挖掘", "商业分析", "bi分析"],
    "大数据": ["大数据", "hadoop", "spark", "flink", "hive", "kafka", "数仓"],
    "云原生": ["kubernetes", "k8s", "docker", "容器", "devops", "ci/cd", "cicd"],
    "数据库": ["mysql", "redis", "mongodb", "postgresql", "oracle", "sql"],
    "测试": ["测试", "qa", "自动化测试", "测试开发", "性能测试"],
    "安全": ["网络安全", "渗透测试", "信息安全", "web安全", "漏洞", "安全研究"],
    "Android": ["android", "安卓"],
    "iOS": ["ios", "swift", "objective-c"],
    "产品": ["产品经理", "产品策划", "pm"],
    "运营": ["运营", "用户运营", "内容运营", "活动运营"],
    "设计": ["ui设计", "ux设计", "视觉设计", "交互设计", "设计师"],
    "金融": ["金融", "投行", "风控", "量化", "固收"],
    "硬件": ["嵌入式", "fpga", "pcb", "硬件", "单片机"],
}

#: 学历标签
EDUCATION_TAGS = ["博士", "硕士", "本科", "大专"]

#: 福利/待遇标签
WELFARE_KEYWORDS: dict[str, list[str]] = {
    "六险一金": ["六险一金", "六险二金"],
    "五险一金": ["五险一金"],
    "补充医疗": ["补充医疗", "商业保险"],
    "免费三餐": ["免费三餐", "免费餐饮", "包吃"],
    "住房补贴": ["住房补贴", "租房补贴", "免费住宿"],
    "带薪年假": ["带薪年假", "年假"],
    "股票期权": ["股票期权", "期权", "股权激励"],
    "解决户口": ["解决户口", "落户", "北京户口", "上海户口"],
    "弹性工作": ["弹性工作", "弹性打卡"],
    "年终奖": ["年终奖", "年终奖金"],
}


#: 标签匹配时视作分隔符的字符（归一化为空格，便于短词边界匹配）
_TAG_SEPARATORS = "/、，,()（）【】[]｜|·"


def _match_keyword(kw_lower: str, text_lower: str, sep_text: str) -> bool:
    """智能关键词匹配。

    - 含分隔符/空格/非 ASCII 的关键词：在原始小写文本上做子串匹配
      （如 ``c/c++``、``spring boot``、``go语言``）。
    - 纯 ASCII 单词：在分隔符归一化后的文本上做词边界匹配，
      避免短词误命中（如 ``go`` 不命中 ``google``/``good``）。
    """
    if not kw_lower:
        return False
    if (
        any(c in _TAG_SEPARATORS for c in kw_lower)
        or " " in kw_lower
        or not kw_lower.isascii()
    ):
        return kw_lower in text_lower
    pattern = r"(?<![a-z0-9])" + re.escape(kw_lower) + r"(?![a-z0-9])"
    return re.search(pattern, sep_text) is not None


def extract_tags(description: str) -> list[str]:
    """从岗位描述中提取标签（技能 + 学历 + 福利），去重保序。"""
    if not description:
        return []
    text = description.lower()
    # 将分隔符归一化为空格，便于 go / qa / pm 等短词做词边界匹配
    sep_text = re.sub(r"[" + re.escape(_TAG_SEPARATORS) + r"]+", " ", text)
    tags: list[str] = []

    # 技能标签
    for tag, keywords in TAG_KEYWORDS.items():
        for kw in keywords:
            if _match_keyword(kw.lower(), text, sep_text):
                tags.append(tag)
                break

    # 福利标签（中文关键词，直接子串匹配）
    for tag, keywords in WELFARE_KEYWORDS.items():
        for kw in keywords:
            if kw in description:
                tags.append(tag)
                break

    # 学历标签（仅取最高匹配的一个）
    for edu in EDUCATION_TAGS:
        if edu in description:
            tags.append(edu)
            break

    # 去重保序
    seen: set[str] = set()
    result: list[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


def _extract_education(text: str) -> str:
    """从文本中提取学历要求，返回最高匹配项。"""
    for edu in ("博士", "硕士", "本科", "大专"):
        if edu in text:
            return edu
    return ""


def _classify_category(title: str, description: str) -> str:
    """根据岗位名与描述推断岗位类别。"""
    text = f"{title} {description}".lower()
    if any(k in text for k in ("算法", "机器学习", "深度学习", "ai", "nlp", "cv")):
        return "算法"
    if any(k in text for k in ("前端", "frontend", "vue", "react")):
        return "前端"
    if any(k in text for k in ("后端", "backend", "服务端", "java", "golang", "python开发")):
        return "后端"
    if any(k in text for k in ("测试", "qa")):
        return "测试"
    if any(k in text for k in ("数据", "大数据", "数仓")):
        return "数据"
    if any(k in text for k in ("产品", "pm")):
        return "产品"
    if any(k in text for k in ("运营",)) :
        return "运营"
    if any(k in text for k in ("设计", "ui", "ux")):
        return "设计"
    if any(k in text for k in ("安全",)) :
        return "安全"
    return ""


# ====================================================================== #
# 哈希与去重
# ====================================================================== #
def _hash_job(title: str, company: str, location: str) -> str:
    """基于 title + company + location 生成 MD5 去重哈希。"""
    # 归一化：去除空白与常见标点，统一小写
    key = re.sub(r"\s+", "", f"{title}|{company}|{location}").strip().lower()
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def deduplicate(jobs: list) -> list:
    """对清洗后的岗位列表去重。

    以 ``job_hash = md5(title + company + location)`` 为唯一键；
    冲突时合并两条记录，保留信息更丰富的一方（更长的描述、更多标签）。
    """
    seen: dict[str, dict] = {}
    result: list[dict] = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        h = job.get("job_hash") or _hash_job(
            job.get("title", ""), job.get("company", ""), job.get("location", "")
        )
        job["job_hash"] = h
        if h in seen:
            existing = seen[h]
            _merge_job(existing, job)
            continue
        seen[h] = job
        result.append(job)
    logger.info("去重: %d -> %d", len(jobs), len(result))
    return result


def _merge_job(existing: dict, incoming: dict) -> None:
    """将 incoming 合并进 existing，保留更丰富的信息。"""
    # 描述取较长者
    if len(incoming.get("description", "")) > len(existing.get("description", "")):
        existing["description"] = incoming["description"]
    if len(incoming.get("requirement", "")) > len(existing.get("requirement", "")):
        existing["requirement"] = incoming["requirement"]
    # 合并 tags（去重保序）
    merged_tags: list[str] = list(existing.get("tags", []))
    tag_set = set(merged_tags)
    for t in incoming.get("tags", []):
        if t not in tag_set:
            merged_tags.append(t)
            tag_set.add(t)
    existing["tags"] = merged_tags
    # 补充缺失字段
    for key in (
        "url",
        "salary_min",
        "salary_max",
        "salary_unit",
        "salary_raw",
        "deadline",
        "education",
        "job_category",
        "company_type",
        "source_repo",
    ):
        if not existing.get(key) and incoming.get(key):
            existing[key] = incoming[key]


# ====================================================================== #
# 清洗主入口
# ====================================================================== #
def clean_jobs(raw_jobs: list) -> list[dict]:
    """清洗原始 job dict 列表，输出标准化 job dict 列表。

    处理流程：字段标准化 -> 薪资解析 -> 截止时间解析 -> 企业类型识别
    -> 标签提取 -> 哈希生成。
    """
    cleaned: list[dict] = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for raw in raw_jobs:
        if not isinstance(raw, dict):
            continue
        title = (raw.get("title") or "").strip()
        company = (raw.get("company") or "").strip()
        # 标题与公司为必填，缺失则跳过
        if not title or not company:
            continue

        location = (raw.get("location") or "").strip()
        salary_raw = (
            raw.get("salary_raw") or raw.get("salary") or ""
        ).strip()
        smin, smax, sunit = parse_salary(salary_raw)

        deadline_raw = (raw.get("deadline") or "").strip()
        deadline = parse_deadline(deadline_raw)

        # 企业类型：优先用抓取时标注的，否则按名称识别
        company_type = raw.get("company_type") or classify_company_type(company)

        description = (raw.get("description") or "").strip()
        requirement = (raw.get("requirement") or "").strip()
        full_text = f"{title} {description} {requirement}"

        tags = extract_tags(full_text)
        education = raw.get("education") or _extract_education(full_text)
        job_category = raw.get("job_category") or _classify_category(title, description)
        job_type = raw.get("job_type") or "校招"

        raw_data = raw.get("raw_data")
        if not isinstance(raw_data, dict):
            raw_data = {}

        job = Job(
            title=title,
            company=company,
            company_type=company_type,
            location=location,
            salary_min=smin,
            salary_max=smax,
            salary_unit=sunit,
            salary_raw=salary_raw,
            description=description,
            requirement=requirement,
            deadline=deadline,
            deadline_raw=deadline_raw,
            tags=tags,
            url=(raw.get("url") or "").strip(),
            source=(raw.get("source") or "").strip(),
            source_repo=(raw.get("source_repo") or "").strip(),
            education=education,
            job_category=job_category,
            job_type=job_type,
            experience=(raw.get("experience") or "").strip(),
            raw_data=raw_data,
            created_at=now_str,
        )
        job.job_hash = _hash_job(title, company, location)
        cleaned.append(job.to_dict())

    logger.info("清洗完成: %d 条原始数据 -> %d 条标准化岗位", len(raw_jobs), len(cleaned))
    return cleaned


# ====================================================================== #
# 工具：教育邮箱后缀（供其他模块复用）
# ====================================================================== #
_EDU_CACHE: Optional[dict[str, str]] = None


def load_edu_domains() -> dict[str, str]:
    """加载 edu_domains.csv，返回「邮箱后缀 -> 学校名」映射。"""
    global _EDU_CACHE
    if _EDU_CACHE is not None:
        return _EDU_CACHE
    mapping: dict[str, str] = {}
    if os.path.exists(_EDU_CSV):
        try:
            with open(_EDU_CSV, encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    domain = (row.get("email_domain") or "").strip().lower()
                    uni = (row.get("university") or "").strip()
                    if domain and uni:
                        mapping[domain] = uni
        except Exception as exc:  # noqa: BLE001
            logger.warning("加载 edu_domains.csv 失败: %s", exc)
    _EDU_CACHE = mapping
    return mapping


def identify_university(email: str) -> str:
    """根据教育邮箱后缀识别学校名（无匹配返回空串）。"""
    if not email or "@" not in email:
        return ""
    domain = email.rsplit("@", 1)[-1].strip().lower()
    domains = load_edu_domains()
    if domain in domains:
        return domains[domain]
    # 支持子域匹配（如 mail.xxx.edu.cn）
    for d, uni in domains.items():
        if domain.endswith("." + d) or domain == d:
            return uni
    return ""
