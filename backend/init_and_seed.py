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
    # === v2.0 新增 120 题 ===
    # 技术 - 阿里高频
    {"job_category": "技术", "question": "MySQL 索引底层数据结构是什么？为什么用 B+树？",
     "answer": "B+树，因为：1. 所有数据在叶子节点，范围查询效率高；2. 非叶子节点不存数据，树更矮减少IO；"
               "3. 叶子节点双向链表连接，支持正反向遍历。相比 B 树和哈希表综合性能最优。",
     "question_type": "面试", "difficulty": "medium", "source": "阿里巴巴面试题"},
    {"job_category": "技术", "question": "什么是缓存穿透、缓存击穿、缓存雪崩？如何解决？",
     "answer": "缓存穿透：查询不存在的数据，请求打到数据库 → 布隆过滤器/缓存空值。"
               "缓存击穿：热点数据过期瞬间大量请求 → 互斥锁/永不过期。"
               "缓存雪崩：大量缓存同时过期 → 过期时间加随机值/多级缓存/限流降级。",
     "question_type": "面试", "difficulty": "medium", "source": "阿里巴巴面试题"},
    # 技术 - 字节高频
    {"job_category": "技术", "question": "Go 语言的协程（goroutine）和线程有什么区别？",
     "answer": "1. goroutine 是用户态轻量线程，初始栈仅2KB，可动态扩缩；线程栈固定1-8MB。"
               "2. goroutine 由 Go 运行时调度，非内核调度，切换成本极低。"
               "3. 一个线程可运行多个 goroutine，通过 GMP 模型管理。",
     "question_type": "面试", "difficulty": "medium", "source": "字节跳动面试题"},
    {"job_category": "技术", "question": "HTTP/2 相比 HTTP/1.1 有哪些改进？",
     "answer": "1. 多路复用：一个连接并发多个请求，解决队头阻塞。2. 头部压缩：HPACK 算法减少冗余。"
               "3. 服务器推送：主动推送资源。4. 二进制分帧：解析更高效。5. 流优先级。",
     "question_type": "面试", "difficulty": "medium", "source": "字节跳动面试题"},
    {"job_category": "技术", "question": "如何实现一个线程安全的单例模式？（写代码）",
     "answer": "双重检查锁定（DCL）+ volatile：先判空→加锁→再判空→创建实例。"
               "或使用静态内部类/枚举实现。Go 可用 sync.Once。",
     "question_type": "笔试", "difficulty": "medium", "source": "字节跳动面试题"},
    # 技术 - 腾讯高频
    {"job_category": "技术", "question": "InnoDB 的 MVCC 实现原理是什么？",
     "answer": "MVCC（多版本并发控制）通过 undo log 实现：每行数据有 DB_TRX_ID（事务ID）和"
               "DB_ROLL_PTR（回滚指针）。ReadView 判断可见性：事务ID < low_limit_id 且不在活跃列表中则可见。"
               "RC 级别每次语句生成 ReadView，RR 级别事务开始生成。",
     "question_type": "面试", "difficulty": "hard", "source": "腾讯面试题"},
    {"job_category": "技术", "question": "C++ 虚函数表（vtable）的实现原理？",
     "answer": "每个有虚函数的类有一个虚函数表（vtable），存储虚函数地址。"
               "对象前 8 字节（64位）存 vptr 指向 vtable。调用虚函数时通过 vptr→vtable 间接跳转。"
               "派生类覆盖 vtable 中对应条目实现多态。",
     "question_type": "面试", "difficulty": "medium", "source": "腾讯面试题"},
    # 技术 - 美团高频
    {"job_category": "技术", "question": "分布式事务有哪些解决方案？",
     "answer": "1. 两阶段提交（2PC）：协调者→参与者 prepare→commit，强一致但性能差。"
               "2. TCC：Try-Confirm-Cancel，业务层补偿。3. 本地消息表 + 定时任务。"
               "4. RocketMQ 事务消息。5. Seata（AT/TCC/Saga模式）。6. 最终一致性+补偿。",
     "question_type": "面试", "difficulty": "hard", "source": "美团面试题"},
    {"job_category": "技术", "question": "消息队列如何保证消息不丢失？",
     "answer": "生产端：发送确认机制（ACK）+ 重试。Broker端：同步刷盘+主从复制。"
               "消费端：手动确认，处理完再 ACK。Kafka 的 ISR 机制，RocketMQ 的同步双写。",
     "question_type": "面试", "difficulty": "medium", "source": "美团面试题"},
    # 技术 - 百度高频
    {"job_category": "技术", "question": "搜索引擎倒排索引的原理是什么？",
     "answer": "倒排索引：词→文档列表的映射。建立词典（term→term_id）和倒排表（term_id→[doc_id列表]）。"
               "查询时：对查询词取交集。优化：跳表（SkipList）、BitMap、分区索引。",
     "question_type": "面试", "difficulty": "hard", "source": "百度面试题"},
    # 技术 - 华为高频
    {"job_category": "技术", "question": "OSI 七层模型每层的作用和常见协议？",
     "answer": "物理层：比特传输（RJ45）。数据链路层：帧传输（MAC/PPP）。网络层：路由寻址（IP/ICMP）。"
               "传输层：端到端（TCP/UDP）。会话层：会话管理。表示层：数据格式转换。应用层：HTTP/DNS/FTP。",
     "question_type": "笔试", "difficulty": "easy", "source": "华为面试题"},
    # 技术 - 算法/数据结构 12 题
    {"job_category": "技术", "question": "如何判断链表有环？找出环的入口？",
     "answer": "快慢指针：快指针每次两步，慢指针一步。相遇后，慢指针回到头，两指针同速前进，再次相遇点即环入口。",
     "question_type": "笔试", "difficulty": "medium", "source": "LeetCode 142"},
    {"job_category": "技术", "question": "LRU 缓存如何实现？",
     "answer": "哈希表+双向链表：get/put O(1)。哈希表存key→节点指针，链表维护访问顺序。"
               "Python 可用 OrderedDict，Java 可用 LinkedHashMap。Go 用 container/list+map。",
     "question_type": "笔试", "difficulty": "medium", "source": "LeetCode 146"},
    {"job_category": "技术", "question": "实现一个生产者-消费者模型（写代码）。",
     "answer": "使用阻塞队列：BlockingQueue（Java）、channel（Go）、queue.Queue+threading（Python）。"
               "注意：锁粒度、空/满条件判断、优雅退出。",
     "question_type": "笔试", "difficulty": "medium", "source": "多线程编程"},
    {"job_category": "技术", "question": "Top K 问题有哪些解法？时间复杂度？",
     "answer": "1. 全排序 O(nlogn)；2. 最小堆 O(nlogk)；3. 快速选择 O(n) 期望。"
               "海量数据：分治+堆合并、MapReduce。",
     "question_type": "笔试", "difficulty": "medium", "source": "LeetCode 215"},
    {"job_category": "技术", "question": "什么是动态规划？核心思想是什么？",
     "answer": "将大问题拆分为重叠子问题，自底向上或自顶向下（记忆化）求解。核心："
               "最优子结构+重叠子问题+状态转移方程。经典题：背包、编辑距离、最长子序列。",
     "question_type": "面试", "difficulty": "medium", "source": "算法基础"},
    # 技术 - 数据库 8 题
    {"job_category": "技术", "question": "SQL 查询执行顺序是什么？",
     "answer": "FROM → ON → JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT。"
               "理解执行顺序有助于写出正确的复杂查询。",
     "question_type": "笔试", "difficulty": "easy", "source": "SQL基础"},
    {"job_category": "技术", "question": "慢 SQL 如何优化？",
     "answer": "1. EXPLAIN 分析执行计划；2. 加索引（覆盖索引优先）；3. 优化 SQL（避免 SELECT *、用 JOIN 替代子查询）；"
               "4. 分库分表；5. 读写分离；6. 缓存热点数据；7. 调整数据库参数。",
     "question_type": "面试", "difficulty": "medium", "source": "数据库优化"},
    {"job_category": "技术", "question": "Redis 有哪些数据类型？各自适用场景？",
     "answer": "String：缓存、计数器；Hash：对象存储；List：消息队列、时间线；Set：去重、共同好友；"
               "ZSet：排行榜、延迟队列；Stream：消息队列（持久化）；HyperLogLog：UV统计；Bitmap：签到。",
     "question_type": "面试", "difficulty": "easy", "source": "Redis基础"},
    # 技术 - 操作系统/网络 6 题
    {"job_category": "技术", "question": "进程和线程的区别？协程又是什么？",
     "answer": "进程：资源分配最小单位，有独立地址空间，切换开销大。线程：CPU调度最小单位，共享进程资源，切换较快。"
               "协程：用户态轻量线程，由程序调度而非OS，切换极低开销，适合IO密集型。",
     "question_type": "面试", "difficulty": "easy", "source": "操作系统基础"},
    {"job_category": "技术", "question": "HTTPS 握手过程是怎样的？",
     "answer": "1. Client Hello（支持的加密套件+随机数）；2. Server Hello（选定套件+证书+随机数）；"
               "3. 客户端验证证书，生成 PreMaster Secret 用公钥加密发送；4. 双方用三个随机数生成会话密钥；"
               "5. 完成握手，后续对称加密通信。",
     "question_type": "面试", "difficulty": "medium", "source": "网络安全"},
    {"job_category": "技术", "question": "Docker 镜像分层原理是什么？有什么好处？",
     "answer": "Docker 镜像由只读层堆叠而成，每层对应 Dockerfile 一条指令。"
               "好处：层共享（不同镜像复用相同层节省空间）、层缓存（未变更层不重建）、快速分发（增量传输）。",
     "question_type": "面试", "difficulty": "medium", "source": "DevOps面试题"},
    # 技术 - 前端 6 题
    {"job_category": "技术", "question": "React 的 Fiber 架构解决了什么问题？",
     "answer": "Fiber 是 React 16 新协调引擎，将渲染任务拆分为可中断的小任务单元。解决："
               "1. 长时间JS阻塞导致掉帧；2. 任务优先级调度（用户交互>动画>数据更新）；3. 增量渲染。",
     "question_type": "面试", "difficulty": "hard", "source": "前端面试题"},
    {"job_category": "技术", "question": "Vue 3 Composition API 相比 Options API 的优势？",
     "answer": "1. 逻辑复用（组合函数替代 mixins）；2. 更好的 TypeScript 支持；3. 代码组织更灵活（按功能而非选项类型）；"
               "4. 更小的打包体积（Tree Shaking）。",
     "question_type": "面试", "difficulty": "medium", "source": "前端面试题"},
    # 产品 15 题
    {"job_category": "产品", "question": "如何设计一个短视频推荐系统的产品方案？",
     "answer": "1. 用户画像（兴趣标签、行为序列）；2. 内容理解（标签、质量评分）；3. 推荐算法（协同过滤+深度学习）；"
               "4. 冷启动（新用户兴趣探测、新内容流量扶持）；5. 评估指标（时长、互动率、留存率）。",
     "question_type": "面试", "difficulty": "hard", "source": "字节跳动产品面试题"},
    {"job_category": "产品", "question": "你如何定义一个好的产品体验？",
     "answer": "1. 可用性：用户能高效完成任务；2. 易学性：新用户快速上手；"
               "3. 容错性：错误提示友好、可撤销；4. 美观性：视觉舒适；5. 情感满足：使用后产生正向情绪。",
     "question_type": "面试", "difficulty": "easy", "source": "腾讯产品面试题"},
    {"job_category": "产品", "question": "如果要将饿了么的外卖用户引流到支付宝，你会怎么设计？",
     "answer": "1. 支付环节自然引导（外卖下单默认支付宝支付）；2. 积分互通（饿了么积分换支付宝权益）；"
               "3. 场景联动（外卖满减券需支付宝领取）；4. 会员体系打通（88VIP含饿了么会员）。",
     "question_type": "面试", "difficulty": "medium", "source": "阿里巴巴产品面试题"},
    {"job_category": "产品", "question": "PRD（产品需求文档）应该包含哪些内容？",
     "answer": "1. 版本记录；2. 背景与目标；3. 用户故事与用例；4. 功能需求（前端+后端）；"
               "5. 非功能需求（性能/安全）；6. 数据埋点需求；7. 上线计划与验收标准。",
     "question_type": "笔试", "difficulty": "easy", "source": "产品面试通用题"},
    # 运营 10 题
    {"job_category": "运营", "question": "DAU 突然下降 20%，你会如何排查和分析？",
     "answer": "1. 确认数据准确性（口径/埋点）；2. 分维度拆解（渠道/版本/地域/新增vs留存）；"
               "3. 检查产品变更（最近上线/AB测试）；4. 外部因素（竞品活动/节假日）；5. 修复后持续监控。",
     "question_type": "面试", "difficulty": "medium", "source": "运营数据分析"},
    {"job_category": "运营", "question": "如何从零搭建一个私域社群？",
     "answer": "1. 定位目标用户，确定社群价值主张；2. 设计引流路径（公众号/短视频→企微）；"
               "3. 制定群规和内容SOP；4. KOC培养+激励机制；5. 持续输出价值+转化链路设计。",
     "question_type": "面试", "difficulty": "medium", "source": "运营面试题"},
    {"job_category": "运营", "question": "小红书、抖音、微博三个平台的内容运营有什么差异？",
     "answer": "小红书：种草导向，重图文+真实体验分享，女性为主。抖音：算法推荐，重短平快+强视觉冲击。"
               "微博：话题引爆+明星/KOL驱动，重实时热点和互动讨论。",
     "question_type": "面试", "difficulty": "medium", "source": "运营面试题"},
    # 金融 10 题
    {"job_category": "金融", "question": "什么是杜邦分析法？三因子模型是什么？",
     "answer": "杜邦分析法将ROE分解为：ROE=净利率×资产周转率×权益乘数。三因子模型：Fama-French模型含"
               "市场风险、市值因子（SMB）、账面市值比因子（HML），用于解释股票收益。",
     "question_type": "面试", "difficulty": "hard", "source": "金融分析师面试"},
    {"job_category": "金融", "question": "央行降准对股市和债市有什么影响？",
     "answer": "降准释放流动性：股市短期利好（资金充裕+信心提振），中长期看基本面；"
               "债市利好（市场利率下行→债券价格上涨）。但需看预期是否已被price-in。",
     "question_type": "面试", "difficulty": "medium", "source": "宏观经济"},
    # 设计 10 题
    {"job_category": "设计", "question": "什么是设计系统（Design System）？为什么需要它？",
     "answer": "设计系统是可复用组件+设计规范的集合。价值：1. 保证多产品视觉/交互一致性；"
               "2. 提升开发效率（组件复用）；3. 降低沟通成本（统一语言）；4. 可扩展性。",
     "question_type": "面试", "difficulty": "medium", "source": "设计面试题"},
    {"job_category": "设计", "question": "如何做一次有效的用户调研？",
     "answer": "1. 明确调研目标（发现需求/验证假设）；2. 选择方法（访谈/问卷/可用性测试/A/B测试）；"
               "3. 招募有代表性的用户；4. 执行并记录；5. 分析归纳→输出洞察→驱动设计决策。",
     "question_type": "面试", "difficulty": "easy", "source": "设计面试题"},
    # HR面通用 15 题
    {"job_category": "技术", "question": "你对加班怎么看？",
     "answer": "如果是项目需要短期高强度冲刺，可以接受。同时我认为高效工作比加班更重要，"
               "会通过优化工作方法和时间管理来减少不必要的加班。",
     "question_type": "HR面", "difficulty": "easy", "source": "HR面试通用题"},
    {"job_category": "产品", "question": "你的职业规划是什么？",
     "answer": "短期1-3年：在岗位上深入实践成为骨干。中期3-5年：带项目/团队，积累管理经验。"
               "长期：成为行业专家，能独立驱动业务增长。结合应聘公司业务表达。",
     "question_type": "HR面", "difficulty": "easy", "source": "HR面试通用题"},
    {"job_category": "运营", "question": "你的期望薪资是多少？如何回答？",
     "answer": "了解行业薪资水平，根据市场行情和自我评估给出合理区间。可说："
               "'根据我的经验和市场水平，期望XX-XX，具体可面议，我更看重成长机会。'",
     "question_type": "HR面", "difficulty": "easy", "source": "HR面试通用题"},
    {"job_category": "金融", "question": "用三个词形容你自己。",
     "answer": "选择与岗位相关的特质，如：逻辑严谨+抗压能力强+学习自驱。每点准备一个具体例子支撑。",
     "question_type": "HR面", "difficulty": "easy", "source": "HR面试通用题"},
    # 技术笔试 15 题
    {"job_category": "技术", "question": "用两个栈实现一个队列。",
     "answer": "入队：压入 stack1。出队：若 stack2 为空，将 stack1 全部弹出压入 stack2，"
               "然后弹出 stack2 顶部。均摊 O(1)。",
     "question_type": "笔试", "difficulty": "easy", "source": "LeetCode 232"},
    {"job_category": "技术", "question": "合并两个有序数组（不允许额外空间）。",
     "answer": "从后往前合并：用 i,j,k 三个指针，比较 nums1[i] 和 nums2[j]，大的放到 nums1[k]。"
               "时间 O(m+n)，空间 O(1)。",
     "question_type": "笔试", "difficulty": "easy", "source": "LeetCode 88"},
    {"job_category": "技术", "question": "求二叉树的最近公共祖先。",
     "answer": "递归：若 root 为 null 或等于 p/q 则返回 root。分别在左右子树递归查找，"
               "若左右都找到则 root 为 LCA，否则返回非 null 的那侧。时间 O(n)。",
     "question_type": "笔试", "difficulty": "medium", "source": "LeetCode 236"},
    {"job_category": "技术", "question": "最长回文子串怎么求？",
     "answer": "1. 中心扩展法：枚举每个中心（1或2字符），向外扩展，O(n²)。"
               "2. Manacher 算法 O(n)。面试一般答中心扩展即可。",
     "question_type": "笔试", "difficulty": "medium", "source": "LeetCode 5"},
    {"job_category": "技术", "question": "如何设计一个秒杀系统？",
     "answer": "1. 前端：验证码+防抖；2. 网关：限流（令牌桶）；3. 业务层：Redis预减库存+MQ异步下单；"
               "4. 数据库：乐观锁+库存扣减幂等；5. 降级熔断：必要时限流→排队→告知用户。",
     "question_type": "面试", "difficulty": "hard", "source": "系统设计"},
    {"job_category": "技术", "question": "RESTful API 设计原则有哪些？",
     "answer": "1. 资源用名词复数（/users, /orders）；2. HTTP 动词表示操作（GET/POST/PUT/DELETE）；"
               "3. 状态码语义正确（200/201/400/404/500）；4. 版本控制（/api/v1/）；5. 分页/过滤/排序参数化。",
     "question_type": "面试", "difficulty": "easy", "source": "后端面试通用题"},
    {"job_category": "技术", "question": "JWT Token 和 Session 认证的区别？各自适用场景？",
     "answer": "JWT：无状态，适合微服务/移动端，缺点是无法主动失效。Session：有状态（需存储），"
               "可随时注销，适合传统Web应用。实际常用 JWT Access Token + Redis 黑名单组合。",
     "question_type": "面试", "difficulty": "medium", "source": "后端面试通用题"},
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


# ===== 10套内置简历模板 =====
RESUME_TEMPLATES: list[dict] = [
    {
        "name": "经典黑白",
        "category": "经典",
        "description": "传统两栏布局，适合金融、咨询等传统行业",
        "is_builtin": True,
        "is_public": True,
        "html_structure": '<div class="resume classic"><div class="header"><h1>{{name}}</h1><p>{{email}} | {{phone}}</p></div><div class="body"><div class="left"><div class="section"><h2>教育背景</h2>{{#education}}<p><b>{{school}}</b> - {{major}} · {{degree}}<br>{{period}}</p>{{/education}}</div><div class="section"><h2>技能</h2><p>{{skills}}</p></div></div><div class="right"><div class="section"><h2>工作经历</h2>{{#experience}}<h3>{{company}} - {{role}}</h3><p class="period">{{period}}</p><p>{{description}}</p>{{/experience}}</div><div class="section"><h2>项目经历</h2>{{#projects}}<h3>{{name}}</h3><p>{{description}}</p><p class="tech">{{tech_stack}}</p>{{/projects}}</div><div class="section"><h2>自我评价</h2><p>{{self_evaluation}}</p></div></div></div></div>',
        "css_rules": '.resume.classic{max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif;color:#333}.header{text-align:center;border-bottom:2px solid #222;padding-bottom:15px;margin-bottom:20px}.header h1{font-size:28px;margin:0 0 6px}.body{display:flex;gap:30px}.left{width:30%}.right{width:70%}.section{margin-bottom:18px}.section h2{font-size:16px;border-bottom:1px solid #ccc;padding-bottom:4px;margin-bottom:8px}.left h2{border-bottom:2px solid #222}.period,.tech{font-size:12px;color:#888}',
        "preview_url": "",
    },
    {
        "name": "现代简约",
        "category": "现代",
        "description": "清爽配色，圆角卡片，适合互联网、科技行业",
        "is_builtin": True,
        "is_public": True,
        "html_structure": '<div class="resume modern"><div class="profile"><div class="avatar"></div><div class="info"><h1>{{name}}</h1><p>{{email}} | {{phone}} | {{school}}</p></div></div><div class="grid"><div class="card"><h2>教育背景</h2>{{#education}}<div class="item"><b>{{school}}</b><span>{{major}} · {{degree}}</span><span>{{period}}</span></div>{{/education}}</div><div class="card"><h2>技能</h2><div class="skills">{{#skills}}<span class="tag">{{.}}</span>{{/skills}}</div></div><div class="card"><h2>工作经历</h2>{{#experience}}<div class="item"><b>{{company}}</b><span>{{role}}</span><span>{{period}}</span><p>{{description}}</p></div>{{/experience}}</div><div class="card"><h2>项目经历</h2>{{#projects}}<div class="item"><b>{{name}}</b><p>{{description}}</p><span class="tech">{{tech_stack}}</span></div>{{/projects}}</div><div class="card"><h2>自我评价</h2><p>{{self_evaluation}}</p></div></div></div>',
        "css_rules": '.resume.modern{max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif;background:#f8fafc}.profile{display:flex;align-items:center;gap:20px;padding:30px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border-radius:12px;margin-bottom:20px}.avatar{width:60px;height:60px;border-radius:50%;background:rgba(255,255,255,0.3)}.info h1{font-size:26px;margin:0 0 4px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.card{background:#fff;border-radius:10px;padding:18px;box-shadow:0 2px 8px rgba(0,0,0,0.04)}.card h2{font-size:15px;color:#667eea;margin:0 0 10px;border-bottom:2px solid #667eea;padding-bottom:6px}.item{margin-bottom:10px}.item b{display:block;font-size:14px}.item span{font-size:12px;color:#888;margin-right:10px}.tag{display:inline-block;background:#eef2ff;color:#667eea;padding:3px 10px;border-radius:20px;font-size:12px;margin:2px}.tech{font-size:12px;color:#aaa}@media(max-width:600px){.grid{grid-template-columns:1fr}}',
        "preview_url": "",
    },
    {
        "name": "创意设计",
        "category": "创意",
        "description": "大胆配色，视觉冲击力强，适合设计、市场岗位",
        "is_builtin": True,
        "is_public": True,
        "html_structure": '<div class="resume creative"><div class="hero"><h1>{{name}}</h1><p class="subtitle">{{school}} · {{major}}</p><p class="contact">{{email}} | {{phone}}</p></div><div class="content"><div class="section"><h2>🎓 教育背景</h2>{{#education}}<p><b>{{school}}</b> - {{major}} · {{degree}} ({{period}})</p>{{/education}}</div><div class="section"><h2>💡 技能</h2><p>{{skills}}</p></div><div class="section"><h2>💼 工作经历</h2>{{#experience}}<div class="exp"><span class="company">{{company}}</span><span class="role">{{role}}</span><span class="period">{{period}}</span><p>{{description}}</p></div>{{/experience}}</div><div class="section"><h2>🚀 项目经历</h2>{{#projects}}<div class="exp"><span class="company">{{name}}</span><p>{{description}}</p><span class="period">{{tech_stack}}</span></div>{{/projects}}</div><div class="section"><h2>✨ 自我评价</h2><p>{{self_evaluation}}</p></div></div></div>',
        "css_rules": '.resume.creative{max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}.hero{background:linear-gradient(135deg,#f093fb,#f5576c);color:#fff;padding:40px 30px;text-align:center;border-radius:0 0 30px 30px}.hero h1{font-size:32px;margin:0}.subtitle{font-size:16px;opacity:0.9;margin:6px 0}.contact{font-size:13px;opacity:0.8}.content{padding:20px 30px}.section h2{font-size:18px;color:#f5576c;margin:20px 0 10px}.exp{margin-bottom:14px;padding-bottom:10px;border-bottom:1px dashed #eee}.company{font-size:15px;font-weight:bold;display:block}.role{font-size:14px;color:#f5576c}.period{font-size:12px;color:#aaa;float:right}',
        "preview_url": "",
    },
    {
        "name": "极简白",
        "category": "极简",
        "description": "大量留白，极简排版，适合注重简洁的岗位",
        "is_builtin": True,
        "is_public": True,
        "html_structure": '<div class="resume minimal"><div class="top"><h1>{{name}}</h1><p>{{email}} · {{phone}} · {{school}}</p></div><hr><h2>教育背景</h2>{{#education}}<p>{{school}} / {{major}} / {{degree}} / {{period}}</p>{{/education}}<h2>技能</h2><p>{{skills}}</p><h2>工作经历</h2>{{#experience}}<p><b>{{company}}</b> — {{role}}<br><span class="grey">{{period}}</span><br>{{description}}</p>{{/experience}}<h2>项目经历</h2>{{#projects}}<p><b>{{name}}</b><br>{{description}}<br><span class="grey">{{tech_stack}}</span></p>{{/projects}}<h2>自我评价</h2><p>{{self_evaluation}}</p></div>',
        "css_rules": '.resume.minimal{max-width:700px;margin:40px auto;padding:40px;font-family:"Georgia",serif;color:#1a1a1a;line-height:1.8}.top{text-align:center;margin-bottom:30px}.top h1{font-size:30px;letter-spacing:4px;margin:0}.top p{font-size:13px;color:#666;margin:6px 0 0}hr{border:0;border-top:1px solid #1a1a1a;margin:20px 0}h2{font-size:14px;text-transform:uppercase;letter-spacing:3px;margin:28px 0 10px;color:#1a1a1a}.grey{font-size:12px;color:#999}p{margin:8px 0;font-size:14px}',
        "preview_url": "",
    },
    {
        "name": "学术风格",
        "category": "学术",
        "description": "严谨排版，适合学术、研究、教育岗位",
        "is_builtin": True,
        "is_public": True,
        "html_structure": '<div class="resume academic"><h1 class="name">{{name}}</h1><p class="contact">{{email}} | {{phone}} | {{school}}</p><div class="section"><h2>EDUCATION</h2>{{#education}}<div class="entry"><div class="entry-header"><b>{{school}}</b><span>{{period}}</span></div><p>{{major}} · {{degree}}</p></div>{{/education}}</div><div class="section"><h2>SKILLS</h2><p>{{skills}}</p></div><div class="section"><h2>EXPERIENCE</h2>{{#experience}}<div class="entry"><div class="entry-header"><b>{{company}}</b><span>{{period}}</span></div><p><i>{{role}}</i></p><p>{{description}}</p></div>{{/experience}}</div><div class="section"><h2>PROJECTS</h2>{{#projects}}<div class="entry"><div class="entry-header"><b>{{name}}</b></div><p>{{description}}</p><p class="tech">{{tech_stack}}</p></div>{{/projects}}</div><div class="section"><h2>SUMMARY</h2><p>{{self_evaluation}}</p></div></div>',
        "css_rules": '.resume.academic{max-width:780px;margin:0 auto;font-family:"Times New Roman",serif;padding:30px 40px;border:1px solid #ccc}.name{font-size:26px;text-align:center;text-transform:uppercase;letter-spacing:2px;margin:0}.contact{text-align:center;font-size:12px;color:#555;margin:4px 0 20px}.section{margin-bottom:20px}.section h2{font-size:13px;border-bottom:1.5px solid #222;padding-bottom:3px;margin-bottom:10px;letter-spacing:2px}.entry{margin-bottom:12px}.entry-header{display:flex;justify-content:space-between;font-size:14px}.entry-header span{font-size:12px;color:#666}.entry p{font-size:13px;margin:3px 0}.tech{font-size:11px;color:#999;font-style:italic}',
        "preview_url": "",
    },
    {
        "name": "科技蓝",
        "category": "科技",
        "description": "深蓝配色，数据驱动展示，适合技术、数据岗位",
        "is_builtin": True,
        "is_public": True,
        "html_structure": '<div class="resume tech"><div class="sidebar"><div class="avatar"></div><h1>{{name}}</h1><p class="role-title">{{major}}</p><div class="block"><h3>联系方式</h3><p>{{email}}<br>{{phone}}</p></div><div class="block"><h3>教育背景</h3>{{#education}}<p>{{school}}<br>{{major}} · {{degree}}<br>{{period}}</p>{{/education}}</div><div class="block"><h3>技能</h3>{{#skills}}<div class="skill-bar"><span>{{.}}</span></div>{{/skills}}</div></div><div class="main"><h2>工作经历</h2>{{#experience}}<div class="exp"><h3>{{company}} <span>{{period}}</span></h3><p class="role">{{role}}</p><p>{{description}}</p></div>{{/experience}}<h2>项目经历</h2>{{#projects}}<div class="exp"><h3>{{name}}</h3><p>{{description}}</p><p class="tags">{{tech_stack}}</p></div>{{/projects}}<h2>自我评价</h2><p>{{self_evaluation}}</p></div></div>',
        "css_rules": '.resume.tech{display:flex;max-width:850px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif;min-height:100vh}.sidebar{width:280px;background:#1e293b;color:#e2e8f0;padding:30px 20px}.sidebar h1{font-size:22px;margin:16px 0 4px}.role-title{font-size:13px;color:#94a3b8}.block{margin-top:24px}.block h3{font-size:12px;text-transform:uppercase;color:#64748b;border-bottom:1px solid #334155;padding-bottom:4px;margin-bottom:8px}.skill-bar{background:#334155;padding:5px 10px;border-radius:4px;margin:4px 0;font-size:12px}.main{flex:1;padding:30px}.main h2{font-size:16px;color:#1e293b;border-bottom:2px solid #3b82f6;padding-bottom:4px;margin:20px 0 12px}.exp{margin-bottom:14px}.exp h3{font-size:14px;margin:0}.exp h3 span{font-size:12px;color:#94a3b8;float:right}.role{font-size:13px;color:#3b82f6;margin:2px 0}.tags{font-size:12px;color:#64748b}@media(max-width:700px){.resume.tech{flex-direction:column}.sidebar{width:100%}}',
        "preview_url": "",
    },
    {
        "name": "商务精英",
        "category": "经典",
        "description": "深色调，适合投行、咨询、管理培训生",
        "is_builtin": True,
        "is_public": True,
        "html_structure": '<div class="resume business"><div class="header"><div><h1>{{name}}</h1><p class="title">{{major}} · {{school}}</p></div><div class="contact-col"><p>{{email}}<br>{{phone}}</p></div></div><div class="body"><div class="section"><h2>教育背景</h2>{{#education}}<p>{{school}} · {{major}} · {{degree}} · {{period}}</p>{{/education}}</div><div class="section"><h2>核心能力</h2><p>{{skills}}</p></div><div class="section"><h2>工作经历</h2>{{#experience}}<div class="exp"><div class="exp-left"><b>{{company}}</b><br><span>{{period}}</span></div><div class="exp-right"><b>{{role}}</b><p>{{description}}</p></div></div>{{/experience}}</div><div class="section"><h2>项目经验</h2>{{#projects}}<div class="exp"><div class="exp-left"><b>{{name}}</b></div><div class="exp-right"><p>{{description}}</p><span class="grey">{{tech_stack}}</span></div></div>{{/projects}}</div><div class="section"><h2>个人陈述</h2><p>{{self_evaluation}}</p></div></div></div>',
        "css_rules": '.resume.business{max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif;background:#fff}.header{display:flex;justify-content:space-between;background:#1a1a2e;color:#fff;padding:25px 30px}.header h1{font-size:28px;margin:0}.title{font-size:14px;opacity:0.8}.contact-col{text-align:right;font-size:13px}.body{padding:20px 30px}.section{margin-bottom:20px}.section h2{font-size:15px;color:#1a1a2e;border-bottom:2px solid #e94560;padding-bottom:4px;margin-bottom:10px}.exp{display:flex;gap:20px;margin-bottom:12px}.exp-left{width:160px;font-size:13px}.exp-left span{font-size:11px;color:#888}.exp-right{flex:1;font-size:13px}.grey{font-size:12px;color:#999}',
        "preview_url": "",
    },
    {
        "name": "清新绿",
        "category": "现代",
        "description": "绿色主题，亲和力强，适合教育、HR、公益岗位",
        "is_builtin": True,
        "is_public": True,
        "html_structure": '<div class="resume fresh"><div class="banner"><h1>{{name}}</h1><p>{{email}} · {{phone}} · {{school}}</p></div><div class="content"><div class="section"><h2>教育背景</h2>{{#education}}<p><b>{{school}}</b> - {{major}} · {{degree}} ({{period}})</p>{{/education}}</div><div class="section"><h2>技能专长</h2><p>{{skills}}</p></div><div class="section"><h2>工作经历</h2>{{#experience}}<div class="item"><div class="dot"></div><div><b>{{company}} · {{role}}</b><span>{{period}}</span><p>{{description}}</p></div></div>{{/experience}}</div><div class="section"><h2>项目经历</h2>{{#projects}}<div class="item"><div class="dot"></div><div><b>{{name}}</b><p>{{description}}</p><span>{{tech_stack}}</span></div></div>{{/projects}}</div><div class="section"><h2>自我评价</h2><p>{{self_evaluation}}</p></div></div></div>',
        "css_rules": '.resume.fresh{max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif;background:#f0fdf4}.banner{background:linear-gradient(135deg,#10b981,#059669);color:#fff;padding:35px;text-align:center}.banner h1{font-size:28px;margin:0}.banner p{font-size:13px;opacity:0.9;margin:8px 0 0}.content{padding:20px 30px}.section h2{font-size:15px;color:#059669;border-left:3px solid #10b981;padding-left:10px;margin:20px 0 10px}.item{display:flex;gap:12px;margin-bottom:12px}.dot{width:8px;height:8px;background:#10b981;border-radius:50%;margin-top:6px;flex-shrink:0}.item b{font-size:14px;display:block}.item span{font-size:12px;color:#888}',
        "preview_url": "",
    },
    {
        "name": "双栏专业",
        "category": "经典",
        "description": "左右两栏，信息密度高，适合简历内容丰富的求职者",
        "is_builtin": True,
        "is_public": True,
        "html_structure": '<div class="resume twocol"><div class="left"><h1>{{name}}</h1><p class="contact">{{email}}<br>{{phone}}<br>{{school}}</p><h2>教育背景</h2>{{#education}}<p>{{school}}<br>{{major}} · {{degree}}<br>{{period}}</p>{{/education}}<h2>技能</h2>{{#skills}}<p class="skill">{{.}}</p>{{/skills}}</div><div class="right"><h2>工作经历</h2>{{#experience}}<h3>{{company}} - {{role}}</h3><span>{{period}}</span><p>{{description}}</p>{{/experience}}<h2>项目经历</h2>{{#projects}}<h3>{{name}}</h3><p>{{description}}</p><p class="tech">{{tech_stack}}</p>{{/projects}}<h2>自我评价</h2><p>{{self_evaluation}}</p></div></div>',
        "css_rules": '.resume.twocol{display:flex;max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}.left{width:35%;background:#2d3436;color:#dfe6e9;padding:30px 20px}.left h1{font-size:22px;margin:0;border-bottom:2px solid #636e72;padding-bottom:10px}.contact{font-size:12px;opacity:0.8;margin:10px 0}.left h2{font-size:13px;margin:20px 0 8px;letter-spacing:1px}.skill{font-size:12px;padding:3px 0;border-bottom:1px solid #636e72}.right{width:65%;padding:30px 25px}.right h2{font-size:15px;border-bottom:2px solid #2d3436;padding-bottom:4px;margin:20px 0 10px}.right h3{font-size:14px;margin:0}.right span{font-size:12px;color:#888}.tech{font-size:12px;color:#aaa}',
        "preview_url": "",
    },
    {
        "name": "卡片式布局",
        "category": "现代",
        "description": "卡片化信息呈现，视觉清晰，适合产品、运营岗位",
        "is_builtin": True,
        "is_public": True,
        "html_structure": '<div class="resume cards"><div class="intro"><h1>{{name}}</h1><p>{{email}} · {{phone}} · {{school}} · {{major}}</p></div><div class="card-grid"><div class="card"><h2>教育背景</h2>{{#education}}<p><b>{{school}}</b><br>{{major}} · {{degree}}<br>{{period}}</p>{{/education}}</div><div class="card"><h2>技能</h2>{{#skills}}<span class="pill">{{.}}</span>{{/skills}}</div><div class="card wide"><h2>工作经历</h2>{{#experience}}<div class="entry"><b>{{company}} - {{role}}</b><span>{{period}}</span><p>{{description}}</p></div>{{/experience}}</div><div class="card wide"><h2>项目经历</h2>{{#projects}}<div class="entry"><b>{{name}}</b><p>{{description}}</p><span class="muted">{{tech_stack}}</span></div>{{/projects}}</div><div class="card wide"><h2>自我评价</h2><p>{{self_evaluation}}</p></div></div></div>',
        "css_rules": '.resume.cards{max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif;background:#f3f4f6;padding:20px}.intro{text-align:center;padding:20px;background:#fff;border-radius:12px;margin-bottom:16px}.intro h1{font-size:26px;margin:0}.card-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.card{background:#fff;border-radius:10px;padding:16px}.card.wide{grid-column:span 2}.card h2{font-size:14px;color:#6366f1;margin:0 0 8px;border-bottom:2px solid #eef2ff;padding-bottom:6px}.pill{display:inline-block;background:#eef2ff;color:#6366f1;padding:3px 10px;border-radius:20px;font-size:11px;margin:2px}.entry{margin-bottom:10px}.entry b{font-size:14px;display:block}.entry span{font-size:11px;color:#888}.muted{font-size:12px;color:#aaa}@media(max-width:600px){.card-grid{grid-template-columns:1fr}.card.wide{grid-column:span 1}}',
        "preview_url": "",
    },
]


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
        ResumeTemplate,
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

    # 5. 简历模板
    print("[5/5] 生成简历模板...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count()).select_from(ResumeTemplate))
        existing = result.scalar() or 0
        if existing >= 10:
            print(f"      已有 {existing} 套模板，跳过")
        else:
            for tpl in RESUME_TEMPLATES:
                session.add(ResumeTemplate(**tpl))
            await session.commit()
            print(f"      完成，共 {len(RESUME_TEMPLATES)} 套模板")

    await engine.dispose()
    print("\n数据库初始化完毕！")


if __name__ == "__main__":
    asyncio.run(init_and_seed())
