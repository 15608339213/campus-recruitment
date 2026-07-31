# 秋招助手开源网站 - 项目知识文档

> **捕获时间**: 2026-07-31
> **项目状态**: 仪表盘已完成并部署
> **知识类型**: 项目文档 / 决策记录 / 操作指南

---

## 1. 项目概述

### 目标
构建一个开源的秋季校园招聘助手网站，提供行业分析仪表盘、招聘信息自动拉取分类、简历制作、面试笔试技巧等功能。

### 当前完成范围
- 行业分析 ECharts 仪表盘（已完成并部署）
- 数据快照生成系统（模拟爬虫输出）
- 浅色/深色主题切换
- 时间范围筛选（7天/30天/月初至今/本季至今/年初至今/全部）
- 数据来源溯源模态框
- 头部企业招聘排行榜

### 在线访问
- **部署 URL**: https://subtle-twilight-43c566.netlify.app/
- **访问密码**: My-Drop-Site
- **注意**: 匿名部署站点需在60分钟内认领，否则将被删除

---

## 2. 技术架构

### 技术栈
| 组件 | 技术 | 说明 |
|------|------|------|
| 图表库 | ECharts (Canvas渲染) | 内联打包，离线可用 |
| 前端 | 原生 HTML/CSS/JS | 无框架依赖，单文件部署 |
| 数据层 | Python + JSON | 每日快照存储为独立 JSON 文件 |
| 部署 | Netlify (匿名部署) | BytePlus CLI 不支持 Windows |
| 测试 | 集成浏览器工具 | Playwright 安装失败后的替代方案 |

### 文件结构
```
campus-recruitment-dashboard/
├── dashboard.py              # 仪表盘生成器（核心脚本）
├── dashboard_runtime.js      # 浏览器交互运行时（时间控件、图表、模态框、主题切换）
├── echarts.min.js             # ECharts 图表库（内联到 HTML）
├── index.html                 # 生成的单文件仪表盘（自包含）
├── dashboard_data.json        # 仪表盘数据负载（调试用）
└── data/
    └── snapshots/             # 每日数据快照（60天的模拟数据）
        ├── 2026-06-01.json
        └── ... (至 2026-07-30)
```

### 数据流水线
1. `generate_snapshots.py` 生成每日招聘数据快照（模拟爬虫）
2. `dashboard.py` 读取所有快照，聚合计算 KPI 和图表数据
3. 生成 `index.html`（内联所有 JS/CSS/数据）和 `dashboard_data.json`
4. 部署 `index.html` 到静态托管平台

---

## 3. 仪表盘功能详情

### KPI 指标卡（4个）
- 近30日岗位总数（对比上一30日窗口变化率）
- 加权平均月薪（按岗位数加权）
- 日均发布岗位数
- 活跃行业数

### 图表面板（5个）
1. **每日岗位发布趋势** - 折线图/柱状图可切换
2. **行业岗位分布** - 饼图/南丁格尔图可切换
3. **企业类型分布** - 饼图（国企/民企/外企/事业单位）
4. **地域岗位分布** - 柱状图/条形图可切换
5. **行业薪资对比** - 柱状图/箱线图可切换

### 数据表格（1个）
- 头部企业招聘榜 - 展示本季招聘规模最大的16家企业

### 交互功能
- 时间范围预设按钮（7D/30D/MTD/QTD/YTD/ALL）
- 自定义日期范围选择器
- 浅色/深色主题切换（localStorage 持久化）
- 每个图表面板的菜单（查看数据源、编辑图表类型）
- 数据来源溯源模态框（展示数据转换代码）

---

## 4. 关键决策记录

### 决策1: 使用 ECharts 而非其他图表库
- **背景**: 需要离线可用的交互式图表
- **决策**: 使用 ECharts 5.x，内联打包到 HTML
- **原因**: 功能丰富、性能优秀、中文支持好、Canvas 渲染流畅
- **替代方案**: Chart.js（功能较少）、D3.js（学习曲线陡）、AntV G2（社区小）

### 决策2: 单文件 HTML 部署
- **背景**: 需要简单可靠的部署方式
- **决策**: 将所有 JS、CSS、数据内联到单个 index.html
- **原因**: 部署简单（拖拽即可）、离线可用、无外部依赖
- **代价**: 文件较大（~1.6MB），但可接受

### 决策3: 使用 Netlify 而非 BytePlus Edge Pages
- **背景**: BytePlus CLI (@byteplus/nest) 不支持 Windows
- **决策**: 改用 Netlify 匿名部署
- **原因**: Netlify CLI 支持 Windows，匿名部署无需账号
- **影响**: 未来如需 BytePlus CDN 加速，需通过 API 或控制台手动操作

### 决策4: 使用集成浏览器工具而非 Playwright
- **背景**: Playwright 安装失败
- **决策**: 使用 TRAE 内置的集成浏览器 MCP 工具
- **原因**: 无需安装、直接可用、支持截图和 DOM 检查
- **影响**: 测试能力有限，但足以验证仪表盘功能

### 决策5: 主题切换通过 CSS 变量实现
- **背景**: 需要支持浅色/深色主题
- **决策**: 使用 `html[data-theme]` 属性 + CSS 变量，图表通过 `chartTheme()` 函数动态读取
- **原因**: 切换无需重载页面，图表颜色实时更新
- **实现**: `setTheme()` 函数设置 `data-theme` 属性，然后重新渲染所有图表

---

## 5. 操作指南

### 本地运行仪表盘
```bash
cd d:\trae\秋招网站\campus-recruitment-dashboard
python dashboard.py          # 重新生成 index.html
python -m http.server 8099   # 启动本地服务器
# 浏览器访问 http://localhost:8099/index.html
```

### 添加新数据快照
1. 将每日爬虫数据写入 `data/snapshots/YYYY-MM-DD.json`
2. 格式: 每行一个 JSON 对象，包含 date/industry/company_type/region/jobs/salary_avg/snapshot_date/captured_at/source/timezone
3. 运行 `python dashboard.py` 重新生成仪表盘

### 部署到 Netlify
```bash
# 方式1: CLI 部署（匿名）
npx netlify deploy --dir=. --prod --allow-anonymous

# 方式2: 网页拖拽
# 访问 https://app.netlify.com/drop
# 拖拽 campus-recruitment-dashboard 文件夹
```

### 部署到 BytePlus Edge Pages（未来）
1. 注册 BytePlus 账号
2. 获取 AK/SK
3. 激活 CDN 服务
4. 使用 Python 调用 BytePlus OpenAPI（V4签名）部署

---

## 6. 已知问题与解决方案

### 问题1: Windows 换行符导致验证失败
- **症状**: dashboard 验证器报 "starts with Trae rendering comment" 错误
- **原因**: `Path.write_text()` 使用 Windows 换行符 (\r\n)
- **解决**: 改用 `open(path, "w", newline="")` 强制 Unix 换行符

### 问题2: Python 类型注解报错
- **症状**: `TypeError: 'type' object is not subscriptable`
- **原因**: Python 3.9 以下不支持 `list[dict]` 语法
- **解决**: 添加 `from __future__ import annotations`

### 问题3: BytePlus CLI 不支持 Windows
- **症状**: `npm install @byteplus/nest` 报 EBADPLATFORM 错误
- **原因**: 包仅支持 darwin/linux
- **解决**: 使用 Netlify 替代部署

### 问题4: 主题切换不工作
- **症状**: 点击主题按钮无反应
- **原因**: dashboard_runtime.js 缺少主题处理代码
- **解决**: 添加 `setTheme()` 函数和事件监听器

---

## 7. 未来路线图

### 短期
- [ ] 配置 Notion MCP 连接器，将本文档推送到 Notion
- [ ] 认领 Netlify 匿名站点（60分钟内）
- [ ] 添加真实爬虫数据源（替换模拟数据）
- [ ] 实现用户认证系统

### 中期
- [ ] AI 简历生成功能
- [ ] 面试笔试技巧知识库
- [ ] 访客反馈收集表单
- [ ] GitHub Actions 自动每日数据采集
- [ ] 自定义域名绑定

### 长期
- [ ] 迁移到 BytePlus Edge Pages（需 Linux 环境或 API 方式）
- [ ] 多语言支持
- [ ] 移动端优化
- [ ] 数据 API 开放

---

## 8. 项目资源链接

- **设计文档**: `c:\Users\李清\.trae-cn\attachments\6a6c0ae8fad652202f2f5080\3a3c10a7-fed4-4eeb-a18f-63ca12c1cf04_2026-07-31-秋招网站-design.md`
- **仪表盘本地文件**: `d:\trae\秋招网站\campus-recruitment-dashboard\index.html`
- **仪表盘在线地址**: https://subtle-twilight-43c566.netlify.app/
- **数据快照生成器**: `c:\Users\李清\.trae-cn\work\6a6c0ae8fad652202f2f5080\generate_snapshots.py`
- **Dashboard 技能模板**: `c:\Users\李清\.trae-cn\skills\dashboard-page\`

---

*本文档由 TRAE 知识沉淀技能自动生成，可导入 Notion 作为项目文档库。*
