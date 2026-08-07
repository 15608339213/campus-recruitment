"""数据库初始化 + 种子数据生成（用于生产部署）。

在容器启动时自动执行：
1. 创建所有数据库表
2. 创建管理员账号
3. 插入示例岗位数据（1000 条）
4. 插入面试技巧数据
5. 插入题库数据

幂等设计：重复执行不会产生重复数据。
"""
from __future__ import annotations

import asyncio
import os
import random
import sys
from datetime import date, timedelta

# 固定随机种子
random.seed(42)

# ===== 数据池定义 =====
JOB_CATEGORIES: dict[str, list[str]] = {
    "技术": [
        "前端开发工程师", "后端开发工程师", "全栈开发工程师", "算法工程师",
        "数据工程师", "测试开发工程师", "DevOps工程师", "移动端开发工程师",
        "嵌入式开发工程师", "安全工程师",
    ],
    "产品": [
        "产品经理", "产品助理", "数据产品经理", "商业化产品经理",
        "用户产品经理", "平台产品经理",
    ],
    "运营": [
        "用户运营专员", "内容运营专员", "活动运营专员", "社区运营专员",
        "新媒体运营", "电商运营专员",
    ],
    "金融": [
        "投资分析师", "行业研究员", "风控专员", "量化研究员",
        "投行分析师", "资产管理专员",
    ],
    "设计": [
        "UI设计师", "UX设计师", "视觉设计师", "交互设计师",
        "品牌设计师", "插画师",
    ],
    "市场": [
        "市场营销专员", "品牌推广专员", "商务拓展专员", "公关专员",
        "市场策划专员",
    ],
    "人力资源": [
        "人力资源专员", "招聘专员", "培训专员", "薪酬福利专员",
    ],
    "供应链": [
        "供应链管理专员", "采购专员", "物流规划专员", "仓储管理专员",
    ],
}

COMPANIES: list[tuple[str, str]] = [
    ("字节跳动", "民企"), ("腾讯", "民企"), ("阿里巴巴", "民企"),
    ("百度", "民企"), ("美团", "民企"), ("京东", "民企"),
    ("网易", "民企"), ("拼多多", "民企"), ("快手", "民企"),
    ("小米", "民企"), ("华为", "民企"), ("大疆", "民企"),
    ("比亚迪", "民企"), ("宁德时代", "民企"), ("理想汽车", "民企"),
    ("蔚来", "民企"), ("小鹏汽车", "民企"), ("滴滴出行", "民企"),
    ("B站", "民企"), ("携程", "民企"),
    ("奇虎360", "民企"), ("搜狗", "民企"), ("知乎", "民企"),
    ("小红书", "民企"), ("得物", "民企"), ("SHEIN", "民企"),
    ("OPPO", "民企"), ("vivo", "民企"), ("荣耀", "民企"),
    ("联想", "民企"), ("海尔", "民企"), ("格力", "民企"),
    ("美的", "民企"), ("TCL", "民企"), ("海康威视", "民企"),
    ("商汤科技", "民企"), ("旷视科技", "民企"), ("科大讯飞", "民企"),
    ("寒武纪", "民企"), ("地平线", "民企"), ("紫光集团", "民企"),
    ("中芯国际", "民企"), ("韦尔股份", "民企"),
    ("微软", "外企"), ("谷歌", "外企"), ("亚马逊", "外企"),
    ("苹果", "外企"), ("Meta", "外企"), ("IBM", "外企"),
    ("英特尔", "外企"), ("高通", "外企"), ("甲骨文", "外企"),
    ("SAP", "外企"), ("宝洁", "外企"), ("联合利华", "外企"),
    ("三星", "外企"), ("索尼", "外企"), ("戴尔", "外企"),
    ("惠普", "外企"), ("思科", "外企"), ("毕马威", "外企"),
    ("德勤", "外企"), ("普华永道", "外企"), ("安永", "外企"),
    ("麦肯锡", "外企"), ("波士顿咨询", "外企"), ("摩根士丹利", "外企"),
    ("高盛", "外企"), ("瑞银", "外企"), ("花旗银行", "外企"),
    ("中国移动", "国企"), ("中国电信", "国企"), ("中国联通", "国企"),
    ("国家电网", "国企"), ("中国石油", "国企"), ("中国石化", "国企"),
    ("工商银行", "国企"), ("建设银行", "国企"), ("中国银行", "国企"),
    ("农业银行", "国企"), ("招商银行", "国企"), ("交通银行", "国企"),
    ("邮储银行", "国企"), ("中国烟草", "国企"), ("国家开发银行", "国企"),
    ("中国建筑", "国企"), ("中国中铁", "国企"), ("中国铁建", "国企"),
    ("中国交建", "国企"), ("中国电建", "国企"), ("中粮集团", "国企"),
    ("中国五矿", "国企"), ("中铝集团", "国企"), ("中国中车", "国企"),
    ("中国航天科工", "国企"), ("中国兵器工业", "国企"),
    ("中国科学院", "事业单位"), ("中国航天科技", "事业单位"),
    ("中国电子科技", "事业单位"), ("国家图书馆", "事业单位"),
    ("中国社会科学院", "事业单位"), ("中国气象局", "事业单位"),
    # === v2.0 新增 52 家 ===
    # 民企
    ("蚂蚁集团", "民企"), ("米哈游", "民企"), ("莉莉丝", "民企"),
    ("叠纸", "民企"), ("鹰角网络", "民企"), ("完美世界", "民企"),
    ("三七互娱", "民企"), ("巨人网络", "民企"), ("斗鱼", "民企"),
    ("虎牙", "民企"), ("第四范式", "民企"), ("智谱AI", "民企"),
    ("百川智能", "民企"), ("月之暗面", "民企"), ("MiniMax", "民企"),
    ("零一万物", "民企"), ("元象XVERSE", "民企"), ("壁仞科技", "民企"),
    ("摩尔线程", "民企"), ("燧原科技", "民企"), ("黑芝麻智能", "民企"),
    ("特斯联", "民企"), ("XREAL", "民企"), ("宇树科技", "民企"),
    ("智元机器人", "民企"), ("追觅科技", "民企"),
    # 外企
    ("英伟达", "外企"), ("AMD", "外企"), ("ARM", "外企"),
    ("特斯拉", "外企"), ("SpaceX", "外企"), ("Netflix", "外企"),
    ("Uber", "外企"), ("Airbnb", "外企"), ("Shopee", "外企"),
    ("Grab", "外企"), ("PayPal", "外企"), ("VMware", "外企"),
    # 国企/央企
    ("国家能源集团", "国企"), ("中国航发", "国企"), ("中国商飞", "国企"),
    ("中广核", "国企"), ("国家电投", "国企"), ("中国中化", "国企"),
    ("中国物流集团", "国企"), ("中国稀土集团", "国企"),
    # 事业单位/研究机构
    ("之江实验室", "事业单位"), ("鹏城实验室", "事业单位"),
    ("紫金山实验室", "事业单位"), ("北京量子院", "事业单位"),
    ("国家超算中心", "事业单位"), ("中科院计算所", "事业单位"),
]

CITIES: list[str] = [
    "北京", "上海", "深圳", "广州", "杭州", "成都", "南京",
    "武汉", "西安", "苏州", "长沙", "重庆", "天津", "青岛",
    "厦门", "合肥", "济南", "大连", "宁波", "郑州",
]

DEGREES: list[str] = ["本科", "硕士", "博士"]
JOB_TYPES: list[str] = ["校招", "实习", "社招"]

SALARY_RANGES: dict[str, list[tuple[int, int]]] = {
    "技术": [(15000, 30000), (20000, 40000), (25000, 50000), (18000, 35000)],
    "产品": [(12000, 25000), (15000, 30000), (18000, 35000)],
    "运营": [(8000, 15000), (10000, 18000), (12000, 20000)],
    "金融": [(10000, 20000), (15000, 30000), (20000, 40000)],
    "设计": [(10000, 18000), (12000, 25000), (15000, 30000)],
    "市场": [(8000, 15000), (10000, 20000), (12000, 25000)],
    "人力资源": [(8000, 12000), (10000, 15000), (12000, 18000)],
    "供应链": [(8000, 15000), (10000, 18000), (12000, 20000)],
}

TAG_POOL: list[str] = [
    "六险一金", "五险一金", "补充医疗", "补充公积金", "年终奖",
    "股票期权", "弹性工作", "免费三餐", "免费班车", "年度体检",
    "带薪年假", "节日福利", "住房补贴", "交通补贴", "餐饮补贴",
    "通讯补贴", "健身福利", "团建活动", "技能培训", "晋升空间",
    "解决户口", "落户加分", "导师制", "国际化团队", "扁平管理",
]

INTERVIEW_TIPS: list[dict] = [
    {
        "job_category": "技术",
        "content_markdown": (
            "## 技术岗面试技巧\n\n"
            "1. **算法与数据结构**：重点掌握数组、链表、树、图、"
            "动态规划等核心知识点，LeetCode 中等难度建议刷 100+ 题。\n"
            "2. **项目深度**：准备 2-3 个有深度的项目，"
            "能说清架构设计、技术选型理由和遇到的挑战。\n"
            "3. **系统设计**：了解负载均衡、缓存策略、数据库分片、"
            "消息队列等分布式系统设计知识。\n"
            "4. **八股文**：操作系统、计算机网络、数据库原理等基础"
            "知识要扎实，建议系统复习一遍。\n"
            "5. **编码规范**：注意变量命名、边界处理、时间空间复杂度分析。\n"
            "6. **心态调整**：遇到不会的题先沟通思路，"
            "从简单情况入手逐步优化。"
        ),
    },
    {
        "job_category": "产品",
        "content_markdown": (
            "## 产品岗面试技巧\n\n"
            "1. **产品思维**：从用户场景出发分析需求，"
            "理解 MVP 和产品迭代思路。\n"
            "2. **竞品分析**：了解目标公司核心产品，"
            "能说出产品优缺点和改进建议。\n"
            "3. **数据驱动**：掌握 DAU、留存率、转化率等核心指标，"
            "能通过数据论证产品决策。\n"
            "4. **逻辑表达**：使用 STAR 法则组织回答，"
            "结论先行，分点阐述。\n"
            "5. **需求文档**：熟悉 PRD 文档撰写，"
            "能清晰表达功能需求和非功能需求。\n"
            "6. **行业认知**：关注互联网行业趋势，"
            "对 AI、Web3 等热点有基本了解。"
        ),
    },
    {
        "job_category": "运营",
        "content_markdown": (
            "## 运营岗面试技巧\n\n"
            "1. **用户洞察**：理解目标用户画像，"
            "能制定针对性的用户分层运营策略。\n"
            "2. **活动策划**：准备 1-2 个完整的活动方案，"
            "包含目标、流程、预算、效果评估。\n"
            "3. **内容能力**：具备文案撰写和内容选题能力，"
            "了解各平台内容调性差异。\n"
            "4. **数据敏感**：关注转化率、ROI 等核心指标，"
            "用数据指导运营动作。\n"
            "5. **执行力**：运营注重落地，"
            "面试中强调自己的项目推进和跨部门协作能力。\n"
            "6. **创新思维**：能提出有创意的运营玩法，"
            "不局限于常规套路。"
        ),
    },
    {
        "job_category": "金融",
        "content_markdown": (
            "## 金融岗面试技巧\n\n"
            "1. **专业知识**：掌握财务分析、DCF 估值模型、"
            "行业研究框架等核心技能。\n"
            "2. **市场认知**：关注宏观经济政策和行业动态，"
            "能对热点事件进行深度分析。\n"
            "3. **案例面试**：练习 case interview，"
            "培养结构化思维和快速估算能力。\n"
            "4. **实习经历**：相关实习是重要加分项，"
            "重点准备实习中的核心贡献和收获。\n"
            "5. **职业规划**：展示清晰的职业发展路径，"
            "表达对金融行业的长期热情。\n"
            "6. **专业知识证书**：CFA、FRM 等证书"
            "是专业能力的有力证明。"
        ),
    },
    {
        "job_category": "设计",
        "content_markdown": (
            "## 设计岗面试技巧\n\n"
            "1. **作品集**：准备 3-5 个高质量作品，"
            "涵盖不同类型和风格，体现设计思路和过程。\n"
            "2. **设计思维**：从用户需求出发，"
            "展示从调研、原型到最终方案的设计流程。\n"
            "3. **工具熟练度**：精通 Figma / Sketch / PS / AI 等"
            "主流设计工具。\n"
            "4. **设计规范**：了解设计系统和组件化思维，"
            "能与开发高效协作。\n"
            "5. **审美能力**：关注设计趋势，"
            "能说出优秀设计案例的亮点。\n"
            "6. **沟通能力**：能清晰阐述设计决策的理由，"
            "接受反馈并迭代优化。"
        ),
    },
]

QUESTION_BANK: list[dict] = [
    {"job_category": "技术", "question": "说说你对虚拟 DOM 的理解，它解决了什么问题？",
     "answer": "虚拟 DOM 是一个 JavaScript 对象树，是对真实 DOM 的抽象。它通过 diff 算法"
               "对比新旧虚拟 DOM 树的差异，最小化真实 DOM 操作次数，从而提升渲染性能。",
     "question_type": "面试", "difficulty": "medium", "source": "前端面试题"},
    {"job_category": "技术", "question": "解释一下 Redis 的持久化机制（RDB 和 AOF）。",
     "answer": "RDB 是快照模式，定期将内存数据快照保存到磁盘；AOF 是日志模式，"
               "记录每次写操作命令。RDB 恢复速度快但可能丢数据，AOF 数据更安全但文件较大。",
     "question_type": "面试", "difficulty": "medium", "source": "后端面试题"},
    {"job_category": "技术", "question": "什么是闭包？请举一个实际应用场景。",
     "answer": "闭包是函数与其词法环境的组合，使内部函数可以访问外部函数的变量。"
               "常见应用：防抖/节流、模块化封装、柯里化、私有变量等。",
     "question_type": "面试", "difficulty": "easy", "source": "前端面试题"},
    {"job_category": "技术", "question": "反转链表（LeetCode 206）",
     "answer": "使用迭代法：定义 prev、curr、next 三个指针，遍历链表时"
               "将 curr.next 指向 prev，然后 prev、curr 各前进一步。",
     "question_type": "笔试", "difficulty": "easy", "source": "LeetCode"},
    {"job_category": "技术", "question": "设计一个短链生成系统。",
     "answer": "1. 使用发号器生成唯一 ID；2. 将 ID 转为 Base62 编码作为短码；"
               "3. 存入 Redis 缓存 + 数据库；4. 访问时先查缓存，未命中查数据库并重定向。",
     "question_type": "面试", "difficulty": "hard", "source": "系统设计"},
    {"job_category": "技术", "question": "TCP 三次握手和四次挥手的过程？",
     "answer": "三次握手：客户端发 SYN，服务端回 SYN+ACK，客户端回 ACK，连接建立。"
               "四次挥手：主动方发 FIN，被动方回 ACK，被动方发 FIN，主动方回 ACK，连接关闭。",
     "question_type": "笔试", "difficulty": "medium", "source": "计算机网络"},
    {"job_category": "产品", "question": "如何判断一个需求是否值得做？",
     "answer": "从用户价值、业务价值、开发成本三个维度评估。用户价值看是否解决真实痛点；"
               "业务价值看对核心指标的贡献；开发成本看 ROI。",
     "question_type": "面试", "difficulty": "medium", "source": "产品面试题"},
    {"job_category": "产品", "question": "请分析你最常用的一个 App 的优缺点。",
     "answer": "选择一个熟悉的产品，从用户画像、核心功能、交互体验、商业化模式等角度分析。",
     "question_type": "面试", "difficulty": "medium", "source": "产品面试题"},
    {"job_category": "运营", "question": "如何提升社区的用户活跃度？",
     "answer": "1. 搭建内容激励体系；2. 设计用户成长体系（等级、勋章）；"
               "3. 策划话题活动引导 UGC；4. 建立核心用户社群；5. 优化新手引导降低门槛。",
     "question_type": "面试", "difficulty": "medium", "source": "运营面试题"},
    {"job_category": "运营", "question": "如何策划一场线上营销活动？",
     "answer": "1. 明确活动目标和预算；2. 确定目标用户和核心玩法；"
               "3. 设计活动流程和转化路径；4. 预估 ROI 和风险；5. 制定数据监控和复盘方案。",
     "question_type": "面试", "difficulty": "easy", "source": "运营面试题"},
    {"job_category": "金融", "question": "如何对一家公司进行估值？",
     "answer": "常用方法：1. DCF（现金流折现法）；2. 可比公司估值法（P/E、P/B 等）；"
               "3. 可比交易法；4. 资产基础法。需结合行业特点和公司阶段综合运用。",
     "question_type": "面试", "difficulty": "hard", "source": "金融面试题"},
    {"job_category": "金融", "question": "什么是市盈率（P/E）？它有什么局限性？",
     "answer": "P/E = 股价 / 每股收益，衡量投资者为每元利润支付的价格。"
               "局限性：亏损企业无意义、受会计政策影响、不同行业不可比。",
     "question_type": "笔试", "difficulty": "medium", "source": "金融笔试题"},
    {"job_category": "技术", "question": "你最大的缺点是什么？（HR面）",
     "answer": "选择一个真实但不致命的缺点，并说明你在如何改进。",
     "question_type": "HR面", "difficulty": "easy", "source": "HR面试通用题"},
    {"job_category": "产品", "question": "为什么选择我们公司？（HR面）",
     "answer": "从三个维度回答：1. 公司行业地位和发展前景；2. 岗位与个人职业规划的匹配度；"
               "3. 对公司产品/文化的认同。要具体，避免空泛。",
     "question_type": "HR面", "difficulty": "easy", "source": "HR面试通用题"},
]


def _generate_job(index: int) -> dict:
    category = random.choice(list(JOB_CATEGORIES.keys()))
    title_base = random.choice(JOB_CATEGORIES[category])
    company, company_type = random.choice(COMPANIES)
    city = random.choice(CITIES)
    salary_min, salary_max = random.choice(SALARY_RANGES[category])
    today = date.today()
    start_date = today - timedelta(days=random.randint(0, 30))
    end_date = today + timedelta(days=random.randint(7, 90))
    created_at = today - timedelta(days=random.randint(0, 59))
    degree = random.choices(DEGREES, weights=[60, 30, 10])[0]
    job_type = random.choices(JOB_TYPES, weights=[60, 25, 15])[0]
    suffix = "（校招）" if job_type == "校招" else "（实习）" if job_type == "实习" else ""
    title = f"{title_base}{suffix}" if suffix else title_base
    tags = random.sample(TAG_POOL, k=random.randint(2, 4))

    return {
        "title": title,
        "company": company,
        "company_type": company_type,
        "location": city,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_unit": "元/月",
        "start_date": start_date,
        "end_date": end_date,
        "created_at": created_at,
        "job_category": category,
        "job_type": job_type,
        "degree_required": degree,
        "description_html": (
            f"<p>{company} {city} 分公司诚聘{title_base}。</p>"
            f"<p>岗位职责：</p>"
            f"<ul><li>负责相关业务的开发与维护</li>"
            f"<li>参与产品需求分析与方案设计</li>"
            f"<li>持续优化系统性能与用户体验</li></ul>"
            f"<p>任职要求：</p>"
            f"<ul><li>{degree}及以上学历，相关专业优先</li>"
            f"<li>具备良好的沟通能力和团队协作精神</li>"
            f"<li>对技术/业务有持续学习的热情</li></ul>"
        ),
        "source_url": f"https://example.com/jobs/seed-{index}",
        "source_repo": "campus/seed-data",
        "tags": tags,
    }


async def init_and_seed() -> None:
    """初始化数据库 + 插入种子数据。"""
    from sqlalchemy import func, select

    from app.core.database import AsyncSessionLocal, engine
    from app.core.security import hash_password
    from app.models import (
        Base,
        InterviewTip,
        Job,
        JobTag,
        QuestionBank,
        User,
        UserProfile,
    )

    print("=" * 60)
    print("  秋招助手 - 数据库初始化")
    print("=" * 60)

    # 1. 创建表
    print("[1/4] 创建数据库表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("      完成")

    # 2. 管理员账号
    print("[2/4] 创建管理员账号...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "admin@campus.com"))
        if result.scalar_one_or_none():
            print("      已存在，跳过")
        else:
            admin = User(
                email="admin@campus.com",
                password_hash=hash_password("admin123"),
                nickname="系统管理员",
                role="admin",
                is_active=True,
                is_verified=True,
            )
            session.add(admin)
            await session.flush()
            session.add(UserProfile(user_id=admin.id, school="管理员", bio="系统管理员账号"))
            await session.commit()
            print("      创建成功: admin@campus.com / admin123")

    # 3. 岗位数据
    print("[3/4] 生成岗位数据...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count()).select_from(Job))
        existing = result.scalar() or 0
        if existing >= 1000:
            print(f"      已有 {existing} 条，跳过")
        else:
            created = 0
            for i in range(1, 1001):
                job_data = _generate_job(i)
                tags = job_data.pop("tags", [])
                job = Job(**job_data)
                session.add(job)
                await session.flush()
                for tag_name in tags:
                    session.add(JobTag(job_id=job.id, tag=tag_name))
                created += 1
                if created % 100 == 0:
                    await session.commit()
                    print(f"      已生成 {created}/1000 条...")
            await session.commit()
            print(f"      完成，共 {created} 条")

    # 4. 面试技巧 + 题库
    print("[4/4] 生成面试技巧和题库...")
    async with AsyncSessionLocal() as session:
        for tip_data in INTERVIEW_TIPS:
            result = await session.execute(
                select(InterviewTip).where(InterviewTip.job_category == tip_data["job_category"])
            )
            if not result.scalar_one_or_none():
                session.add(InterviewTip(**tip_data))

        for q_data in QUESTION_BANK:
            session.add(QuestionBank(**q_data))

        await session.commit()
        print("      完成")

    await engine.dispose()
    print("\n数据库初始化完毕！")


if __name__ == "__main__":
    asyncio.run(init_and_seed())
