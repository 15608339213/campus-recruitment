"""30套简历模板种子数据脚本。

运行方式：从 backend 目录执行 `python scripts/seed_templates.py`

模板分类（6类）：
- 经典上下结构（8个）- professional_layout
- 经典左右分栏（8个）- split_layout
- 创意/时尚（5个）- creative
- 极简线条（4个）- minimal
- 表格风格（3个）- table_style
- 技术/程序员（2个）- tech_focused
"""
from __future__ import annotations

import asyncio
import sys
import os

# 确保可以导入 app 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ============================================================
# 模板数据定义
# ============================================================
# 变量占位符说明：
# {{name}} {{phone}} {{email}} {{location}}
# {{school}} {{major}} {{degree}} {{graduation_year}}
# {{education_list}} - 教育背景列表HTML
# {{experience_list}} - 工作经历列表HTML
# {{projects_list}} - 项目经历列表HTML
# {{skills_list}} - 技能列表HTML
# {{self_evaluation}} - 自我评价文本

TEMPLATES = [
    # =====================
    # 经典上下结构 (8个)
    # =====================
    {
        "name": "经典白底黑字",
        "category": "经典上下结构",
        "description": "最经典的单栏上下排列布局，白底黑字，适合各类传统行业求职",
        "style_tags": '["简约", "专业", "经典"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#1a1a1a", "accent": "#2c3e50", "bg": "#ffffff", "text": "#333333"}',
        "html_structure": (
            '<div class="resume classic-bw">'
            '<div class="header">'
            '<h1>{{name}}</h1>'
            '<p>{{email}} | {{phone}} | {{location}}</p>'
            '<p>{{school}} · {{major}} · {{degree}}</p>'
            '</div>'
            '<div class="section"><h2>教育背景</h2>{{education_list}}</div>'
            '<div class="section"><h2>工作经历</h2>{{experience_list}}</div>'
            '<div class="section"><h2>项目经历</h2>{{projects_list}}</div>'
            '<div class="section"><h2>专业技能</h2>{{skills_list}}</div>'
            '<div class="section"><h2>自我评价</h2><p>{{self_evaluation}}</p></div>'
            '</div>'
        ),
        "css_rules": (
            '.resume.classic-bw{max-width:750px;margin:0 auto;padding:40px 35px;'
            'font-family:"Microsoft YaHei",sans-serif;color:#333;background:#fff;line-height:1.7}'
            '.header{text-align:center;border-bottom:2px solid #1a1a1a;padding-bottom:18px;margin-bottom:24px}'
            '.header h1{font-size:28px;margin:0 0 8px;color:#1a1a1a}'
            '.header p{font-size:13px;color:#555;margin:2px 0}'
            '.section{margin-bottom:22px}'
            '.section h2{font-size:16px;border-bottom:1px solid #ddd;padding-bottom:5px;margin-bottom:10px;'
            'color:#1a1a1a;text-transform:uppercase;letter-spacing:2px}'
        ),
    },
    {
        "name": "蓝调专业",
        "category": "经典上下结构",
        "description": "以蓝色为主色调，上方个人信息区配蓝色背景，适合金融、管理类岗位",
        "style_tags": '["专业", "稳重", "商务"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#1e40af", "accent": "#3b82f6", "bg": "#ffffff", "text": "#1f2937"}',
        "html_structure": (
            '<div class="resume blue-pro">'
            '<div class="top-banner"><h1>{{name}}</h1>'
            '<p>{{email}} | {{phone}} | {{location}}</p></div>'
            '<div class="content">'
            '<div class="section"><h2>教育背景</h2>{{education_list}}</div>'
            '<div class="section"><h2>工作经历</h2>{{experience_list}}</div>'
            '<div class="section"><h2>项目经历</h2>{{projects_list}}</div>'
            '<div class="section"><h2>技能</h2>{{skills_list}}</div>'
            '<div class="section"><h2>自我评价</h2><p>{{self_evaluation}}</p></div>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.blue-pro{max-width:750px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}'
            '.top-banner{background:linear-gradient(135deg,#1e40af,#3b82f6);color:#fff;'
            'padding:30px 35px;text-align:center;border-radius:8px 8px 0 0}'
            '.top-banner h1{font-size:28px;margin:0 0 6px}'
            '.top-banner p{font-size:13px;opacity:0.9;margin:0}'
            '.content{padding:25px 30px;background:#fff}'
            '.section{margin-bottom:20px}'
            '.section h2{font-size:15px;color:#1e40af;border-bottom:2px solid #dbeafe;'
            'padding-bottom:5px;margin-bottom:10px}'
        ),
    },
    {
        "name": "灰色专业风",
        "category": "经典上下结构",
        "description": "灰色渐变顶栏，稳重内敛，适合咨询、法律等行业",
        "style_tags": '["稳重", "专业", "内敛"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#374151", "accent": "#6366f1", "bg": "#f9fafb", "text": "#1f2937"}',
        "html_structure": (
            '<div class="resume gray-pro">'
            '<div class="top"><h1>{{name}}</h1>'
            '<div class="contact-row"><span>{{email}}</span><span>{{phone}}</span><span>{{location}}</span></div>'
            '<p class="subtitle">{{school}} · {{major}} · {{degree}} · {{graduation_year}}届</p></div>'
            '<div class="main">'
            '<div class="section"><h2>教育背景</h2>{{education_list}}</div>'
            '<div class="section"><h2>工作经历</h2>{{experience_list}}</div>'
            '<div class="section"><h2>项目经历</h2>{{projects_list}}</div>'
            '<div class="section"><h2>技术能力</h2>{{skills_list}}</div>'
            '<div class="section"><h2>自我评价</h2><p>{{self_evaluation}}</p></div>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.gray-pro{max-width:750px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}'
            '.top{background:linear-gradient(135deg,#374151,#4b5563);color:#fff;'
            'padding:28px 35px;text-align:center}'
            '.top h1{font-size:27px;margin:0 0 8px}'
            '.contact-row{display:flex;justify-content:center;gap:20px;font-size:13px;opacity:0.9}'
            '.subtitle{font-size:13px;opacity:0.8;margin:6px 0 0}'
            '.main{padding:25px 30px;background:#f9fafb}'
            '.section{margin-bottom:20px}'
            '.section h2{font-size:15px;color:#374151;border-left:3px solid #6366f1;'
            'padding-left:10px;margin-bottom:10px}'
        ),
    },
    {
        "name": "暖橙色活力",
        "category": "经典上下结构",
        "description": "橙色点缀带来温暖活力感，适合运营、市场类岗位",
        "style_tags": '["活力", "温暖", "亲和"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#ea580c", "accent": "#f97316", "bg": "#fff7ed", "text": "#431407"}',
        "html_structure": (
            '<div class="resume warm-orange">'
            '<div class="header"><h1>{{name}}</h1>'
            '<p>{{email}} | {{phone}} | {{location}}</p>'
            '<p class="sub">{{school}} · {{major}} · {{degree}}</p></div>'
            '<div class="body">'
            '<div class="section"><h2>教育背景</h2>{{education_list}}</div>'
            '<div class="section"><h2>工作经历</h2>{{experience_list}}</div>'
            '<div class="section"><h2>项目经历</h2>{{projects_list}}</div>'
            '<div class="section"><h2>核心能力</h2>{{skills_list}}</div>'
            '<div class="section"><h2>自我评价</h2><p>{{self_evaluation}}</p></div>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.warm-orange{max-width:750px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif;'
            'background:#fff7ed}'
            '.header{background:linear-gradient(135deg,#ea580c,#f97316);color:#fff;padding:30px 35px;'
            'text-align:center;border-radius:10px 10px 0 0}'
            '.header h1{font-size:28px;margin:0 0 6px}'
            '.header p{font-size:13px;opacity:0.95;margin:2px 0}'
            '.body{padding:25px 30px}'
            '.section{margin-bottom:20px}'
            '.section h2{font-size:15px;color:#ea580c;border-bottom:2px solid #fed7aa;'
            'padding-bottom:5px;margin-bottom:10px}'
        ),
    },
    {
        "name": "绿色清新风",
        "category": "经典上下结构",
        "description": "绿色主色调，清新自然，适合教育、环保、医疗行业",
        "style_tags": '["清新", "自然", "亲和"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#059669", "accent": "#10b981", "bg": "#ecfdf5", "text": "#064e3b"}',
        "html_structure": (
            '<div class="resume green-fresh">'
            '<div class="header"><h1>{{name}}</h1>'
            '<p>{{email}} | {{phone}} | {{location}}</p>'
            '<p>{{school}} · {{major}} · {{degree}}</p></div>'
            '<div class="body">'
            '<div class="section"><h2>教育背景</h2>{{education_list}}</div>'
            '<div class="section"><h2>工作经历</h2>{{experience_list}}</div>'
            '<div class="section"><h2>项目经历</h2>{{projects_list}}</div>'
            '<div class="section"><h2>专业技能</h2>{{skills_list}}</div>'
            '<div class="section"><h2>自我评价</h2><p>{{self_evaluation}}</p></div>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.green-fresh{max-width:750px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}'
            '.header{background:linear-gradient(135deg,#059669,#10b981);color:#fff;padding:30px 35px;'
            'text-align:center;border-radius:8px 8px 0 0}'
            '.header h1{font-size:28px;margin:0 0 6px}'
            '.header p{font-size:13px;opacity:0.95;margin:2px 0}'
            '.body{padding:25px 30px;background:#ecfdf5}'
            '.section{margin-bottom:20px}'
            '.section h2{font-size:15px;color:#059669;border-bottom:2px solid #a7f3d0;'
            'padding-bottom:5px;margin-bottom:10px}'
        ),
    },
    {
        "name": "深紫典雅",
        "category": "经典上下结构",
        "description": "紫色主题，典雅高端，适合金融、奢侈品、艺术行业",
        "style_tags": '["典雅", "高端", "艺术"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#7c3aed", "accent": "#a78bfa", "bg": "#faf5ff", "text": "#3b0764"}',
        "html_structure": (
            '<div class="resume purple-elegant">'
            '<div class="header"><h1>{{name}}</h1>'
            '<p>{{email}} | {{phone}} | {{location}}</p>'
            '<p>{{school}} · {{major}} · {{degree}}</p></div>'
            '<div class="main">'
            '<div class="section"><h2>教育背景</h2>{{education_list}}</div>'
            '<div class="section"><h2>工作经历</h2>{{experience_list}}</div>'
            '<div class="section"><h2>项目经历</h2>{{projects_list}}</div>'
            '<div class="section"><h2>核心技能</h2>{{skills_list}}</div>'
            '<div class="section"><h2>自我评价</h2><p>{{self_evaluation}}</p></div>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.purple-elegant{max-width:750px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}'
            '.header{background:linear-gradient(135deg,#7c3aed,#a78bfa);color:#fff;padding:30px 35px;'
            'text-align:center;border-radius:12px 12px 0 0}'
            '.header h1{font-size:28px;margin:0 0 6px;letter-spacing:2px}'
            '.header p{font-size:13px;opacity:0.95;margin:2px 0}'
            '.main{padding:25px 30px;background:#faf5ff}'
            '.section{margin-bottom:20px}'
            '.section h2{font-size:15px;color:#7c3aed;border-bottom:2px solid #ddd6fe;'
            'padding-bottom:5px;margin-bottom:10px}'
        ),
    },
    {
        "name": "暗黑专业版",
        "category": "经典上下结构",
        "description": "深色背景白色文字，现代感十足，适合科技、设计行业",
        "style_tags": '["现代", "科技", "暗黑"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#e2e8f0", "accent": "#3b82f6", "bg": "#1e293b", "text": "#e2e8f0"}',
        "html_structure": (
            '<div class="resume dark-pro">'
            '<div class="header"><h1>{{name}}</h1>'
            '<p>{{email}} | {{phone}} | {{location}}</p>'
            '<p>{{school}} · {{major}} · {{degree}}</p></div>'
            '<div class="content">'
            '<div class="section"><h2>教育背景</h2>{{education_list}}</div>'
            '<div class="section"><h2>工作经历</h2>{{experience_list}}</div>'
            '<div class="section"><h2>项目经历</h2>{{projects_list}}</div>'
            '<div class="section"><h2>技能</h2>{{skills_list}}</div>'
            '<div class="section"><h2>自我评价</h2><p>{{self_evaluation}}</p></div>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.dark-pro{max-width:750px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif;'
            'background:#1e293b;color:#e2e8f0;padding:0;border-radius:12px;overflow:hidden}'
            '.header{background:#0f172a;padding:30px 35px;text-align:center;'
            'border-bottom:2px solid #3b82f6}'
            '.header h1{font-size:28px;margin:0 0 6px;color:#f8fafc}'
            '.header p{font-size:13px;color:#94a3b8;margin:2px 0}'
            '.content{padding:25px 30px}'
            '.section{margin-bottom:20px}'
            '.section h2{font-size:15px;color:#3b82f6;border-bottom:1px solid #334155;'
            'padding-bottom:5px;margin-bottom:10px}'
        ),
    },
    {
        "name": "两端对齐版",
        "category": "经典上下结构",
        "description": "左对齐标题+右对齐日期，干净利落的排版风格",
        "style_tags": '["干净", "利落", "现代"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#0f172a", "accent": "#2563eb", "bg": "#ffffff", "text": "#334155"}',
        "html_structure": (
            '<div class="resume aligned">'
            '<div class="header"><h1>{{name}}</h1>'
            '<p>{{email}} &middot; {{phone}} &middot; {{location}}</p></div>'
            '<div class="body">'
            '<div class="section"><h2>教育背景</h2>{{education_list}}</div>'
            '<div class="section"><h2>工作经历</h2>{{experience_list}}</div>'
            '<div class="section"><h2>项目经历</h2>{{projects_list}}</div>'
            '<div class="section"><h2>专业技能</h2>{{skills_list}}</div>'
            '<div class="section"><h2>自我评价</h2><p>{{self_evaluation}}</p></div>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.aligned{max-width:750px;margin:0 auto;padding:35px;font-family:"Microsoft YaHei",sans-serif;'
            'color:#334155;background:#fff}'
            '.header{text-align:center;margin-bottom:28px;padding-bottom:18px;'
            'border-bottom:1px solid #e2e8f0}'
            '.header h1{font-size:28px;margin:0 0 8px;color:#0f172a;letter-spacing:1px}'
            '.header p{font-size:13px;color:#64748b}'
            '.section{margin-bottom:22px}'
            '.section h2{font-size:14px;color:#0f172a;letter-spacing:2px;text-transform:uppercase;'
            'border-bottom:1px solid #cbd5e1;padding-bottom:6px;margin-bottom:12px}'
        ),
    },

    # =====================
    # 经典左右分栏 (8个)
    # =====================
    {
        "name": "经典左栏信息",
        "category": "经典左右分栏",
        "description": "左侧深色边栏展示个人信息+技能，右侧展示详细经历",
        "style_tags": '["经典", "双栏", "专业"]',
        "supported_sections": '["基本信息", "联系方式", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#1e293b", "accent": "#3b82f6", "bg": "#ffffff", "text": "#334155", "sidebar": "#1e293b"}',
        "html_structure": (
            '<div class="resume split-left">'
            '<div class="sidebar">'
            '<h1>{{name}}</h1>'
            '<div class="contact"><p>{{email}}</p><p>{{phone}}</p><p>{{location}}</p></div>'
            '<h2>教育背景</h2>{{education_list}}'
            '<h2>技能</h2>{{skills_list}}'
            '</div>'
            '<div class="main">'
            '<h2>工作经历</h2>{{experience_list}}'
            '<h2>项目经历</h2>{{projects_list}}'
            '<h2>自我评价</h2><p>{{self_evaluation}}</p>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.split-left{display:flex;max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif;'
            'min-height:100vh}'
            '.sidebar{width:35%;background:#1e293b;color:#e2e8f0;padding:35px 25px}'
            '.sidebar h1{font-size:24px;color:#f8fafc;margin:0 0 15px;border-bottom:2px solid #3b82f6;'
            'padding-bottom:10px}'
            '.contact p{font-size:12px;margin:4px 0;color:#94a3b8}'
            '.sidebar h2{font-size:13px;color:#94a3b8;margin:22px 0 8px;letter-spacing:1px}'
            '.main{width:65%;padding:35px 30px;background:#fff}'
            '.main h2{font-size:16px;color:#1e293b;border-bottom:2px solid #e2e8f0;'
            'padding-bottom:6px;margin:20px 0 12px}'
            '@media(max-width:700px){.resume.split-left{flex-direction:column}.sidebar,.main{width:100%}}'
        ),
    },
    {
        "name": "蓝调双栏",
        "category": "经典左右分栏",
        "description": "左侧蓝底白字边栏，右侧白底深色文字，对比清晰",
        "style_tags": '["专业", "双栏", "商务"]',
        "supported_sections": '["基本信息", "联系方式", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#1e40af", "accent": "#60a5fa", "bg": "#ffffff", "text": "#1f2937", "sidebar": "#1e3a5f"}',
        "html_structure": (
            '<div class="resume blue-split">'
            '<div class="left">'
            '<div class="avatar-area"><div class="avatar-circle">{{name}}</div></div>'
            '<h1>{{name}}</h1>'
            '<p class="contact">{{email}}<br>{{phone}}<br>{{location}}</p>'
            '<h2>教育</h2>{{education_list}}'
            '<h2>技能</h2>{{skills_list}}'
            '</div>'
            '<div class="right">'
            '<h2>工作经历</h2>{{experience_list}}'
            '<h2>项目经历</h2>{{projects_list}}'
            '<h2>自我评价</h2><p>{{self_evaluation}}</p>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.blue-split{display:flex;max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}'
            '.left{width:32%;background:linear-gradient(180deg,#1e3a5f,#1e40af);color:#e0e7ff;'
            'padding:35px 22px;text-align:center}'
            '.avatar-circle{width:80px;height:80px;border-radius:50%;background:rgba(255,255,255,0.2);'
            'margin:0 auto 15px;display:flex;align-items:center;justify-content:center;font-size:24px}'
            '.left h1{font-size:22px;margin:0 0 10px;color:#fff}'
            '.contact{font-size:11px;color:#93c5fd;line-height:1.6}'
            '.left h2{font-size:12px;color:#93c5fd;margin:20px 0 8px;letter-spacing:1px}'
            '.right{width:68%;padding:35px 30px;background:#fff}'
            '.right h2{font-size:16px;color:#1e40af;border-bottom:2px solid #dbeafe;'
            'padding-bottom:5px;margin:18px 0 10px}'
            '@media(max-width:700px){.resume.blue-split{flex-direction:column}.left,.right{width:100%}}'
        ),
    },
    {
        "name": "深灰双栏",
        "category": "经典左右分栏",
        "description": "深灰与白色的经典搭配，稳重专业",
        "style_tags": '["稳重", "双栏", "经典"]',
        "supported_sections": '["基本信息", "联系方式", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#374151", "accent": "#818cf8", "bg": "#ffffff", "text": "#1f2937", "sidebar": "#374151"}',
        "html_structure": (
            '<div class="resume gray-split">'
            '<div class="left"><h1>{{name}}</h1>'
            '<p class="role">{{major}} · {{degree}}</p>'
            '<p class="contact">{{email}}<br>{{phone}}<br>{{location}}</p>'
            '<h2>教育背景</h2>{{education_list}}'
            '<h2>技能</h2>{{skills_list}}</div>'
            '<div class="right">'
            '<h2>工作经历</h2>{{experience_list}}'
            '<h2>项目经历</h2>{{projects_list}}'
            '<h2>自我评价</h2><p>{{self_evaluation}}</p>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.gray-split{display:flex;max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}'
            '.left{width:33%;background:#374151;color:#d1d5db;padding:35px 22px}'
            '.left h1{font-size:22px;color:#f9fafb;margin:0}'
            '.role{font-size:12px;color:#818cf8;margin:4px 0 15px}'
            '.contact{font-size:12px;color:#9ca3af;line-height:1.6}'
            '.left h2{font-size:12px;color:#9ca3af;margin:20px 0 8px;letter-spacing:1px;'
            'border-bottom:1px solid #4b5563;padding-bottom:4px}'
            '.right{width:67%;padding:35px 30px;background:#fff}'
            '.right h2{font-size:16px;color:#374151;border-bottom:2px solid #e5e7eb;'
            'padding-bottom:5px;margin:18px 0 10px}'
            '@media(max-width:700px){.resume.gray-split{flex-direction:column}.left,.right{width:100%}}'
        ),
    },
    {
        "name": "炫紫双栏",
        "category": "经典左右分栏",
        "description": "紫色渐变边栏，现代时尚的双栏布局",
        "style_tags": '["现代", "时尚", "双栏"]',
        "supported_sections": '["基本信息", "联系方式", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#6d28d9", "accent": "#c4b5fd", "bg": "#ffffff", "text": "#1f2937", "sidebar": "#5b21b6"}',
        "html_structure": (
            '<div class="resume purple-split">'
            '<div class="left"><h1>{{name}}</h1>'
            '<p class="info">{{email}}<br>{{phone}}<br>{{location}}</p>'
            '<h2>教育背景</h2>{{education_list}}'
            '<h2>技能</h2>{{skills_list}}</div>'
            '<div class="right">'
            '<h2>工作经历</h2>{{experience_list}}'
            '<h2>项目经历</h2>{{projects_list}}'
            '<h2>自我评价</h2><p>{{self_evaluation}}</p>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.purple-split{display:flex;max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}'
            '.left{width:33%;background:linear-gradient(180deg,#5b21b6,#7c3aed);color:#ede9fe;'
            'padding:35px 22px}'
            '.left h1{font-size:22px;color:#faf5ff;margin:0 0 15px;border-bottom:2px solid #a78bfa;'
            'padding-bottom:10px}'
            '.info{font-size:12px;color:#c4b5fd;line-height:1.7}'
            '.left h2{font-size:12px;color:#c4b5fd;margin:22px 0 8px;letter-spacing:1px}'
            '.right{width:67%;padding:35px 30px;background:#fff}'
            '.right h2{font-size:16px;color:#6d28d9;border-bottom:2px solid #ede9fe;'
            'padding-bottom:5px;margin:18px 0 10px}'
            '@media(max-width:700px){.resume.purple-split{flex-direction:column}.left,.right{width:100%}}'
        ),
    },
    {
        "name": "简约双栏",
        "category": "经典左右分栏",
        "description": "极简双栏布局，左栏仅用线条分割，干净利落",
        "style_tags": '["简约", "现代", "双栏"]',
        "supported_sections": '["基本信息", "联系方式", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#18181b", "accent": "#71717a", "bg": "#fafafa", "text": "#27272a", "sidebar": "#f4f4f5"}',
        "html_structure": (
            '<div class="resume clean-split">'
            '<div class="left"><h1>{{name}}</h1>'
            '<p>{{email}}<br>{{phone}}<br>{{location}}</p>'
            '<hr><h2>教育</h2>{{education_list}}'
            '<hr><h2>技能</h2>{{skills_list}}</div>'
            '<div class="right">'
            '<h2>工作经历</h2>{{experience_list}}'
            '<h2>项目经历</h2>{{projects_list}}'
            '<h2>自我评价</h2><p>{{self_evaluation}}</p>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.clean-split{display:flex;max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}'
            '.left{width:30%;background:#f4f4f5;padding:35px 22px}'
            '.left h1{font-size:22px;color:#18181b;margin:0 0 15px}'
            '.left p{font-size:12px;color:#71717a;line-height:1.7}'
            '.left hr{border:0;border-top:1px solid #d4d4d8;margin:18px 0}'
            '.left h2{font-size:12px;color:#18181b;margin:14px 0 8px;letter-spacing:2px;text-transform:uppercase}'
            '.right{width:70%;padding:35px 30px;background:#fff}'
            '.right h2{font-size:16px;color:#18181b;border-bottom:1px solid #d4d4d8;'
            'padding-bottom:5px;margin:18px 0 10px}'
            '@media(max-width:700px){.resume.clean-split{flex-direction:column}.left,.right{width:100%}}'
        ),
    },
    {
        "name": "绿色双栏",
        "category": "经典左右分栏",
        "description": "绿色主题双栏，左侧深绿边栏，清新专业",
        "style_tags": '["清新", "双栏", "专业"]',
        "supported_sections": '["基本信息", "联系方式", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#064e3b", "accent": "#34d399", "bg": "#ffffff", "text": "#1f2937", "sidebar": "#064e3b"}',
        "html_structure": (
            '<div class="resume green-split">'
            '<div class="left"><h1>{{name}}</h1>'
            '<p>{{email}}<br>{{phone}}<br>{{location}}</p>'
            '<h2>教育背景</h2>{{education_list}}'
            '<h2>技能</h2>{{skills_list}}</div>'
            '<div class="right">'
            '<h2>工作经历</h2>{{experience_list}}'
            '<h2>项目经历</h2>{{projects_list}}'
            '<h2>自我评价</h2><p>{{self_evaluation}}</p>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.green-split{display:flex;max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}'
            '.left{width:33%;background:#064e3b;color:#d1fae5;padding:35px 22px}'
            '.left h1{font-size:22px;color:#ecfdf5;margin:0;border-bottom:2px solid #34d399;padding-bottom:10px}'
            '.left p{font-size:12px;color:#6ee7b7;line-height:1.7;margin:12px 0}'
            '.left h2{font-size:12px;color:#6ee7b7;margin:20px 0 8px;letter-spacing:1px}'
            '.right{width:67%;padding:35px 30px;background:#fff}'
            '.right h2{font-size:16px;color:#064e3b;border-bottom:2px solid #a7f3d0;'
            'padding-bottom:5px;margin:18px 0 10px}'
            '@media(max-width:700px){.resume.green-split{flex-direction:column}.left,.right{width:100%}}'
        ),
    },
    {
        "name": "金色双栏",
        "category": "经典左右分栏",
        "description": "金色主题，适合金融、管理类岗位，彰显尊贵气质",
        "style_tags": '["高端", "金融", "双栏"]',
        "supported_sections": '["基本信息", "联系方式", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#92400e", "accent": "#fbbf24", "bg": "#ffffff", "text": "#1f2937", "sidebar": "#78350f"}',
        "html_structure": (
            '<div class="resume gold-split">'
            '<div class="left"><h1>{{name}}</h1>'
            '<p>{{email}}<br>{{phone}}<br>{{location}}</p>'
            '<h2>教育背景</h2>{{education_list}}'
            '<h2>技能</h2>{{skills_list}}</div>'
            '<div class="right">'
            '<h2>工作经历</h2>{{experience_list}}'
            '<h2>项目经历</h2>{{projects_list}}'
            '<h2>自我评价</h2><p>{{self_evaluation}}</p>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.gold-split{display:flex;max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}'
            '.left{width:33%;background:linear-gradient(180deg,#78350f,#92400e);color:#fef3c7;'
            'padding:35px 22px}'
            '.left h1{font-size:22px;color:#fffbeb;margin:0;border-bottom:2px solid #fbbf24;padding-bottom:10px}'
            '.left p{font-size:12px;color:#fcd34d;line-height:1.7;margin:12px 0}'
            '.left h2{font-size:12px;color:#fcd34d;margin:20px 0 8px;letter-spacing:1px}'
            '.right{width:67%;padding:35px 30px;background:#fff}'
            '.right h2{font-size:16px;color:#92400e;border-bottom:2px solid #fde68a;'
            'padding-bottom:5px;margin:18px 0 10px}'
            '@media(max-width:700px){.resume.gold-split{flex-direction:column}.left,.right{width:100%}}'
        ),
    },
    {
        "name": "珊瑚双栏",
        "category": "经典左右分栏",
        "description": "温暖珊瑚色边栏，适合教育、公益、人力资源行业",
        "style_tags": '["温暖", "双栏", "亲和"]',
        "supported_sections": '["基本信息", "联系方式", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#be123c", "accent": "#fda4af", "bg": "#ffffff", "text": "#1f2937", "sidebar": "#9f1239"}',
        "html_structure": (
            '<div class="resume coral-split">'
            '<div class="left"><h1>{{name}}</h1>'
            '<p>{{email}}<br>{{phone}}<br>{{location}}</p>'
            '<h2>教育背景</h2>{{education_list}}'
            '<h2>技能</h2>{{skills_list}}</div>'
            '<div class="right">'
            '<h2>工作经历</h2>{{experience_list}}'
            '<h2>项目经历</h2>{{projects_list}}'
            '<h2>自我评价</h2><p>{{self_evaluation}}</p>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.coral-split{display:flex;max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}'
            '.left{width:33%;background:#9f1239;color:#ffe4e6;padding:35px 22px}'
            '.left h1{font-size:22px;color:#fff1f2;margin:0;border-bottom:2px solid #fda4af;padding-bottom:10px}'
            '.left p{font-size:12px;color:#fda4af;line-height:1.7;margin:12px 0}'
            '.left h2{font-size:12px;color:#fda4af;margin:20px 0 8px;letter-spacing:1px}'
            '.right{width:67%;padding:35px 30px;background:#fff}'
            '.right h2{font-size:16px;color:#9f1239;border-bottom:2px solid #ffe4e6;'
            'padding-bottom:5px;margin:18px 0 10px}'
            '@media(max-width:700px){.resume.coral-split{flex-direction:column}.left,.right{width:100%}}'
        ),
    },

    # =====================
    # 创意/时尚 (5个)
    # =====================
    {
        "name": "渐变霓虹",
        "category": "创意/时尚",
        "description": "大胆的紫红渐变背景，白色文字，适合设计、创意行业",
        "style_tags": '["创意", "大胆", "视觉冲击"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#ec4899", "accent": "#fdf2f8", "bg": "#831843", "text": "#fce7f3"}',
        "html_structure": (
            '<div class="resume neon">'
            '<div class="hero"><h1>{{name}}</h1>'
            '<p class="tagline">{{major}} · {{school}} · {{degree}}</p>'
            '<p class="contact">{{email}} &bull; {{phone}} &bull; {{location}}</p></div>'
            '<div class="grid">'
            '<div class="card"><h2>01 教育背景</h2>{{education_list}}</div>'
            '<div class="card"><h2>02 技能</h2>{{skills_list}}</div>'
            '<div class="card wide"><h2>03 工作经历</h2>{{experience_list}}</div>'
            '<div class="card wide"><h2>04 项目经历</h2>{{projects_list}}</div>'
            '<div class="card"><h2>05 自我评价</h2><p>{{self_evaluation}}</p></div>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.neon{max-width:780px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}'
            '.hero{background:linear-gradient(135deg,#831843,#be185d,#ec4899);color:#fce7f3;'
            'padding:40px;text-align:center;border-radius:16px 16px 0 0}'
            '.hero h1{font-size:34px;margin:0 0 8px;text-shadow:2px 2px 4px rgba(0,0,0,0.3)}'
            '.tagline{font-size:16px;opacity:0.9;margin:4px 0}'
            '.contact{font-size:13px;opacity:0.8;margin:8px 0 0}'
            '.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:20px;background:#fdf2f8}'
            '.card{background:#fff;border-radius:12px;padding:18px;box-shadow:0 2px 12px rgba(0,0,0,0.06)}'
            '.card.wide{grid-column:span 2}'
            '.card h2{font-size:15px;color:#be185d;margin:0 0 10px;border-bottom:2px solid #fce7f3;padding-bottom:6px}'
            '@media(max-width:600px){.grid{grid-template-columns:1fr}.card.wide{grid-column:span 1}}'
        ),
    },
    {
        "name": "杂志风排版",
        "category": "创意/时尚",
        "description": "类杂志大标题+分栏设计，适合媒体、设计、市场岗位",
        "style_tags": '["创意", "杂志", "设计感"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#0f172a", "accent": "#f43f5e", "bg": "#fff1f2", "text": "#1f2937"}',
        "html_structure": (
            '<div class="resume magazine">'
            '<div class="masthead"><span class="issue">RESUME / 2026</span>'
            '<h1>{{name}}</h1><p class="dek">{{school}} · {{major}} · {{degree}}</p></div>'
            '<div class="contact-bar"><span>{{email}}</span><span>{{phone}}</span><span>{{location}}</span></div>'
            '<div class="cols">'
            '<div class="col"><h2>教育背景</h2>{{education_list}}<h2>技能</h2>{{skills_list}}'
            '<h2>自我评价</h2><p>{{self_evaluation}}</p></div>'
            '<div class="col"><h2>工作经历</h2>{{experience_list}}<h2>项目经历</h2>{{projects_list}}</div>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.magazine{max-width:800px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif;'
            'background:#fff1f2;padding:30px}'
            '.masthead{text-align:center;padding:20px 0}' 
            '.issue{font-size:11px;color:#f43f5e;letter-spacing:4px}'
            '.masthead h1{font-size:42px;margin:8px 0;color:#0f172a;letter-spacing:-1px}'
            '.dek{font-size:14px;color:#64748b}'
            '.contact-bar{display:flex;justify-content:center;gap:24px;padding:12px 0;'
            'border-top:1px solid #fecdd3;border-bottom:1px solid #fecdd3;font-size:12px;color:#881337}'
            '.cols{display:flex;gap:24px;margin-top:20px}'
            '.col{flex:1}'
            '.col h2{font-size:14px;color:#f43f5e;border-bottom:2px solid #fecdd3;padding-bottom:5px;margin:16px 0 8px}'
            '@media(max-width:600px){.cols{flex-direction:column}}'
        ),
    },
    {
        "name": "赛博朋克风",
        "category": "创意/时尚",
        "description": "霓虹绿+深黑配色，科技感十足，适合游戏、电竞、Web3行业",
        "style_tags": '["科技", "赛博", "前卫"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#00ff41", "accent": "#0d0d0d", "bg": "#0a0a0a", "text": "#e0e0e0"}',
        "html_structure": (
            '<div class="resume cyber">'
            '<div class="header"><h1>{{name}}</h1>'
            '<p class="glitch">{{major}} // {{school}} // {{degree}}</p>'
            '<p class="contact">{{email}} | {{phone}} | {{location}}</p></div>'
            '<div class="content">'
            '<div class="section"><h2>[ 教育背景 ]</h2>{{education_list}}</div>'
            '<div class="section"><h2>[ 工作经历 ]</h2>{{experience_list}}</div>'
            '<div class="section"><h2>[ 项目经历 ]</h2>{{projects_list}}</div>'
            '<div class="section"><h2>[ 技术栈 ]</h2>{{skills_list}}</div>'
            '<div class="section"><h2>[ 关于我 ]</h2><p>{{self_evaluation}}</p></div>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.cyber{max-width:750px;margin:0 auto;font-family:"Consolas","Courier New",monospace;'
            'background:#0a0a0a;color:#e0e0e0;padding:30px;border:1px solid #00ff41;border-radius:8px}'
            '.header{text-align:center;border-bottom:1px solid #00ff41;padding-bottom:20px;margin-bottom:20px}'
            '.header h1{font-size:30px;color:#00ff41;margin:0;text-shadow:0 0 10px rgba(0,255,65,0.5)}'
            '.glitch{font-size:13px;color:#39ff14;margin:6px 0}'
            '.contact{font-size:12px;color:#666}'
            '.section{margin-bottom:20px}'
            '.section h2{font-size:14px;color:#00ff41;margin:0 0 8px;letter-spacing:1px}'
        ),
    },
    {
        "name": "艺术手绘风",
        "category": "创意/时尚",
        "description": "圆润柔和的配色+圆角设计，适合插画、UI/UX设计岗位",
        "style_tags": '["艺术", "柔和", "设计"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#6366f1", "accent": "#f472b6", "bg": "#eef2ff", "text": "#312e81"}',
        "html_structure": (
            '<div class="resume artistic">'
            '<div class="intro"><h1>{{name}}</h1><p class="desc">{{school}} · {{major}} · {{degree}}</p>'
            '<div class="dots"><span>{{email}}</span><span>{{phone}}</span><span>{{location}}</span></div></div>'
            '<div class="flow">'
            '<div class="box"><h2>教育背景</h2>{{education_list}}</div>'
            '<div class="box"><h2>技能</h2>{{skills_list}}</div>'
            '<div class="box"><h2>工作经历</h2>{{experience_list}}</div>'
            '<div class="box"><h2>项目经历</h2>{{projects_list}}</div>'
            '<div class="box"><h2>自我评价</h2><p>{{self_evaluation}}</p></div>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.artistic{max-width:700px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif;'
            'background:#eef2ff;padding:30px;border-radius:24px}'
            '.intro{text-align:center;margin-bottom:24px}'
            '.intro h1{font-size:30px;color:#312e81;margin:0;font-weight:700}'
            '.desc{font-size:14px;color:#6366f1;margin:6px 0 12px}'
            '.dots{display:flex;justify-content:center;gap:16px;font-size:12px;color:#818cf8}'
            '.flow{display:flex;flex-direction:column;gap:14px}'
            '.box{background:#fff;border-radius:16px;padding:20px;box-shadow:0 4px 16px rgba(99,102,241,0.08)}'
            '.box h2{font-size:15px;color:#6366f1;margin:0 0 10px;display:flex;align-items:center;gap:6px}'
            '.box h2::before{content:"";width:8px;height:8px;background:#f472b6;border-radius:50%}'
        ),
    },
    {
        "name": "拼贴画风格",
        "category": "创意/时尚",
        "description": "不规则色块背景+大胆排版，适合广告、创意策划行业",
        "style_tags": '["创意", "拼贴", "活力"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#1e293b", "accent": "#f59e0b", "bg": "#fffbeb", "text": "#1e293b"}',
        "html_structure": (
            '<div class="resume collage">'
            '<div class="banner"><div class="stripe yellow"></div><h1>{{name}}</h1>'
            '<p>{{email}} | {{phone}} | {{location}}</p>'
            '<div class="stripe pink"></div></div>'
            '<div class="blocks">'
            '<div class="block accent1"><h2>教育背景</h2>{{education_list}}</div>'
            '<div class="block accent2"><h2>技能</h2>{{skills_list}}</div>'
            '<div class="block accent3"><h2>工作经历</h2>{{experience_list}}</div>'
            '<div class="block accent4"><h2>项目经历</h2>{{projects_list}}</div>'
            '<div class="block accent1"><h2>自我评价</h2><p>{{self_evaluation}}</p></div>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.collage{max-width:780px;margin:0 auto;font-family:"Microsoft YaHei",sans-serif}'
            '.banner{text-align:center;padding:25px;background:#fff;position:relative}'
            '.stripe{height:3px;margin:8px auto;border-radius:2px}'
            '.stripe.yellow{width:60%;background:#f59e0b}'
            '.stripe.pink{width:40%;background:#ec4899}'
            '.banner h1{font-size:32px;color:#1e293b;margin:10px 0}'
            '.banner p{font-size:13px;color:#64748b}'
            '.blocks{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:0 15px 15px}'
            '.block{padding:20px;border-radius:12px}'
            '.block.accent1{background:#fef3c7}'
            '.block.accent2{background:#dbeafe}'
            '.block.accent3{background:#fce7f3}'
            '.block.accent4{background:#d1fae5}'
            '.block h2{font-size:15px;color:#1e293b;margin:0 0 10px}'
            '@media(max-width:600px){.blocks{grid-template-columns:1fr}}'
        ),
    },

    # =====================
    # 极简线条 (4个)
    # =====================
    {
        "name": "纯净极简",
        "category": "极简线条",
        "description": "极致留白，仅用细线分割区域，适合注重简洁的企业",
        "style_tags": '["极简", "留白", "优雅"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#171717", "accent": "#737373", "bg": "#ffffff", "text": "#404040"}',
        "html_structure": (
            '<div class="resume pure">'
            '<h1>{{name}}</h1>'
            '<p class="contact">{{email}} &middot; {{phone}} &middot; {{location}}</p>'
            '<hr>'
            '<h3>教育</h3>{{education_list}}<hr>'
            '<h3>经历</h3>{{experience_list}}<hr>'
            '<h3>项目</h3>{{projects_list}}<hr>'
            '<h3>技能</h3>{{skills_list}}<hr>'
            '<h3>关于我</h3><p>{{self_evaluation}}</p>'
            '</div>'
        ),
        "css_rules": (
            '.resume.pure{max-width:620px;margin:40px auto;padding:50px;font-family:"Georgia","Microsoft YaHei",serif;'
            'color:#404040;line-height:1.8}'
            '.resume.pure h1{font-size:32px;color:#171717;margin:0 0 6px;font-weight:400;letter-spacing:3px}'
            '.contact{font-size:12px;color:#a3a3a3;margin:0 0 30px}'
            '.resume.pure hr{border:0;border-top:1px solid #e5e5e5;margin:24px 0}'
            '.resume.pure h3{font-size:12px;color:#737373;letter-spacing:4px;text-transform:uppercase;'
            'margin:0 0 10px;font-weight:400}'
            '.resume.pure p{font-size:14px;margin:4px 0}'
        ),
    },
    {
        "name": "细线网格",
        "category": "极简线条",
        "description": "用细线构建网格感，信息层次分明，适合建筑、设计行业",
        "style_tags": '["极简", "网格", "现代"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#262626", "accent": "#a3a3a3", "bg": "#fafafa", "text": "#525252"}',
        "html_structure": (
            '<div class="resume gridline">'
            '<div class="top"><h1>{{name}}</h1><p>{{email}} | {{phone}} | {{location}}</p></div>'
            '<div class="line"></div>'
            '<div class="two-col">'
            '<div class="col"><h2>教育背景</h2>{{education_list}}<h2>技能</h2>{{skills_list}}</div>'
            '<div class="col"><h2>工作经历</h2>{{experience_list}}<h2>项目经历</h2>{{projects_list}}</div>'
            '</div>'
            '<div class="line"></div>'
            '<h2>自我评价</h2><p>{{self_evaluation}}</p>'
            '</div>'
        ),
        "css_rules": (
            '.resume.gridline{max-width:700px;margin:30px auto;padding:35px;font-family:"Microsoft YaHei",sans-serif;'
            'background:#fafafa;color:#525252}'
            '.top{text-align:center;margin-bottom:20px}'
            '.top h1{font-size:26px;color:#262626;margin:0;font-weight:400;letter-spacing:2px}'
            '.top p{font-size:12px;color:#a3a3a3;margin:6px 0 0}'
            '.line{height:1px;background:#d4d4d4;margin:18px 0}'
            '.two-col{display:flex;gap:40px}'
            '.col{flex:1}'
            '.col h2,.resume.gridline>h2{font-size:11px;color:#a3a3a3;letter-spacing:3px;'
            'text-transform:uppercase;margin:0 0 10px}'
            '@media(max-width:600px){.two-col{flex-direction:column;gap:0}}'
        ),
    },
    {
        "name": "竖线分割",
        "category": "极简线条",
        "description": "左侧竖线贯穿，所有内容在右侧展开，独特而优雅",
        "style_tags": '["极简", "优雅", "独特"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#18181b", "accent": "#a1a1aa", "bg": "#ffffff", "text": "#3f3f46"}',
        "html_structure": (
            '<div class="resume vline">'
            '<div class="vline-inner">'
            '<div class="vline-left"><h1>{{name}}</h1><p>{{email}}<br>{{phone}}<br>{{location}}</p></div>'
            '<div class="vline-right">'
            '<h2>教育背景</h2>{{education_list}}'
            '<h2>工作经历</h2>{{experience_list}}'
            '<h2>项目经历</h2>{{projects_list}}'
            '<h2>技能</h2>{{skills_list}}'
            '<h2>自我评价</h2><p>{{self_evaluation}}</p>'
            '</div></div></div>'
        ),
        "css_rules": (
            '.resume.vline{max-width:700px;margin:30px auto;padding:30px;font-family:"Microsoft YaHei",sans-serif}'
            '.vline-inner{display:flex;gap:0;position:relative}'
            '.vline-left{width:220px;padding-right:30px;text-align:right}'
            '.vline-left h1{font-size:22px;color:#18181b;margin:0 0 10px}'
            '.vline-left p{font-size:11px;color:#a1a1aa;line-height:1.6}'
            '.vline-right{flex:1;padding-left:30px;border-left:1px solid #d4d4d4}'
            '.vline-right h2{font-size:13px;color:#18181b;margin:16px 0 8px;letter-spacing:2px}'
            '@media(max-width:550px){.vline-inner{flex-direction:column}'
            '.vline-left{width:100%;text-align:center;padding-right:0;margin-bottom:20px}'
            '.vline-right{border-left:0;border-top:1px solid #d4d4d4;padding-left:0;padding-top:20px}}'
        ),
    },
    {
        "name": "圆形极简",
        "category": "极简线条",
        "description": "圆角容器+大量留白，柔和而现代的极简风格",
        "style_tags": '["极简", "圆润", "现代"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#27272a", "accent": "#d4d4d8", "bg": "#ffffff", "text": "#3f3f46"}',
        "html_structure": (
            '<div class="resume round-min">'
            '<div class="header"><h1>{{name}}</h1><p>{{email}} | {{phone}} | {{location}}</p></div>'
            '<div class="section"><h2>教育背景</h2>{{education_list}}</div>'
            '<div class="section"><h2>工作经历</h2>{{experience_list}}</div>'
            '<div class="section"><h2>项目经历</h2>{{projects_list}}</div>'
            '<div class="section"><h2>技能</h2>{{skills_list}}</div>'
            '<div class="section"><h2>自我评价</h2><p>{{self_evaluation}}</p></div>'
            '</div>'
        ),
        "css_rules": (
            '.resume.round-min{max-width:680px;margin:30px auto;padding:30px;font-family:"Microsoft YaHei",sans-serif}'
            '.header{text-align:center;padding:30px;border:1px solid #e4e4e7;border-radius:16px;margin-bottom:16px}'
            '.header h1{font-size:26px;color:#27272a;margin:0 0 6px}'
            '.header p{font-size:12px;color:#a1a1aa;margin:0}'
            '.section{padding:20px;margin-bottom:12px;border:1px solid #f4f4f5;border-radius:12px}'
            '.section h2{font-size:13px;color:#27272a;margin:0 0 10px;letter-spacing:1px}'
        ),
    },

    # =====================
    # 表格风格 (3个)
    # =====================
    {
        "name": "经典表格版",
        "category": "表格风格",
        "description": "使用HTML表格布局，信息排列整齐，适合数据密集的简历",
        "style_tags": '["表格", "整齐", "传统"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#1e293b", "accent": "#64748b", "bg": "#ffffff", "text": "#334155"}',
        "html_structure": (
            '<div class="resume table-classic">'
            '<h1>{{name}}</h1>'
            '<table class="info-table"><tr><td>{{email}}</td><td>{{phone}}</td><td>{{location}}</td></tr></table>'
            '<h2>教育背景</h2><table class="data-table">{{education_list}}</table>'
            '<h2>工作经历</h2><table class="data-table">{{experience_list}}</table>'
            '<h2>项目经历</h2><table class="data-table">{{projects_list}}</table>'
            '<h2>技能</h2><p>{{skills_list}}</p>'
            '<h2>自我评价</h2><p>{{self_evaluation}}</p>'
            '</div>'
        ),
        "css_rules": (
            '.resume.table-classic{max-width:780px;margin:0 auto;padding:30px;font-family:"Microsoft YaHei",sans-serif;'
            'color:#334155}'
            '.resume.table-classic h1{font-size:26px;color:#1e293b;text-align:center;margin:0 0 12px}'
            '.info-table{width:100%;text-align:center;margin-bottom:20px}'
            '.info-table td{font-size:13px;color:#64748b;padding:4px 8px}'
            '.data-table{width:100%;border-collapse:collapse;margin-bottom:16px}'
            '.data-table td,.data-table th{border:1px solid #e2e8f0;padding:8px 12px;font-size:13px;text-align:left}'
            '.data-table th{background:#f8fafc;font-weight:600;color:#1e293b}'
            '.resume.table-classic h2{font-size:15px;color:#1e293b;border-bottom:2px solid #e2e8f0;'
            'padding-bottom:5px;margin:20px 0 10px}'
        ),
    },
    {
        "name": "斑马线条纹",
        "category": "表格风格",
        "description": "交替行颜色表格，数据展示清晰，适合技术、数据岗位",
        "style_tags": '["表格", "数据", "清晰"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#0f172a", "accent": "#2563eb", "bg": "#f8fafc", "text": "#1e293b"}',
        "html_structure": (
            '<div class="resume zebra">'
            '<div class="head"><h1>{{name}}</h1>'
            '<p>{{email}} | {{phone}} | {{location}}</p></div>'
            '<h2>教育背景</h2><table class="zebra-table">{{education_list}}</table>'
            '<h2>工作经历</h2><table class="zebra-table">{{experience_list}}</table>'
            '<h2>项目经历</h2><table class="zebra-table">{{projects_list}}</table>'
            '<h2>技能</h2><p>{{skills_list}}</p>'
            '<h2>自我评价</h2><p>{{self_evaluation}}</p>'
            '</div>'
        ),
        "css_rules": (
            '.resume.zebra{max-width:800px;margin:0 auto;padding:30px;font-family:"Microsoft YaHei",sans-serif;'
            'color:#1e293b}'
            '.head{text-align:center;padding:20px;background:#f1f5f9;border-radius:8px;margin-bottom:20px}'
            '.head h1{font-size:26px;color:#0f172a;margin:0 0 6px}'
            '.head p{font-size:13px;color:#64748b}'
            '.zebra-table{width:100%;border-collapse:collapse;margin-bottom:18px}'
            '.zebra-table td,.zebra-table th{padding:8px 14px;font-size:13px;text-align:left}'
            '.zebra-table th{background:#0f172a;color:#f8fafc;font-weight:500}'
            '.zebra-table tr:nth-child(even){background:#f1f5f9}'
            '.zebra-table tr:nth-child(odd){background:#fff}'
            '.resume.zebra h2{font-size:15px;color:#0f172a;margin:18px 0 8px;border-left:4px solid #2563eb;'
            'padding-left:10px}'
        ),
    },
    {
        "name": "信息卡片表格",
        "category": "表格风格",
        "description": "表格+卡片混合布局，兼顾数据整齐和视觉美感",
        "style_tags": '["表格", "卡片", "现代"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价"]',
        "color_themes": '{"primary": "#18181b", "accent": "#14b8a6", "bg": "#f0fdfa", "text": "#1e293b"}',
        "html_structure": (
            '<div class="resume card-table">'
            '<div class="top-card"><h1>{{name}}</h1>'
            '<table class="contact-table"><tr><td>{{email}}</td><td>{{phone}}</td>'
            '<td>{{location}}</td></tr></table></div>'
            '<div class="card"><h2>教育背景</h2><table class="inner-table">{{education_list}}</table></div>'
            '<div class="card"><h2>工作经历</h2><table class="inner-table">{{experience_list}}</table></div>'
            '<div class="card"><h2>项目经历</h2><table class="inner-table">{{projects_list}}</table></div>'
            '<div class="card"><h2>技能</h2><p>{{skills_list}}</p></div>'
            '<div class="card"><h2>自我评价</h2><p>{{self_evaluation}}</p></div>'
            '</div>'
        ),
        "css_rules": (
            '.resume.card-table{max-width:800px;margin:0 auto;padding:20px;font-family:"Microsoft YaHei",sans-serif;'
            'background:#f0fdfa}'
            '.top-card{background:#fff;border-radius:12px;padding:24px;text-align:center;margin-bottom:16px;'
            'box-shadow:0 1px 4px rgba(0,0,0,0.06)}'
            '.top-card h1{font-size:26px;color:#18181b;margin:0 0 10px}'
            '.contact-table{margin:0 auto;border-collapse:collapse}'
            '.contact-table td{font-size:13px;color:#64748b;padding:2px 12px;border-right:1px solid #e2e8f0}'
            '.contact-table td:last-child{border-right:0}'
            '.card{background:#fff;border-radius:10px;padding:18px;margin-bottom:12px;'
            'box-shadow:0 1px 4px rgba(0,0,0,0.04)}'
            '.card h2{font-size:14px;color:#0f766e;margin:0 0 10px;padding-bottom:6px;'
            'border-bottom:2px solid #ccfbf1}'
            '.inner-table{width:100%;border-collapse:collapse}'
            '.inner-table td,.inner-table th{padding:6px 10px;font-size:13px;text-align:left}'
            '.inner-table th{color:#0f766e;font-weight:500}'
        ),
    },

    # =====================
    # 技术/程序员 (2个)
    # =====================
    {
        "name": "程序员专业版",
        "category": "技术/程序员",
        "description": "深色主题，技能进度条，GitHub风格，适合软件工程师岗位",
        "style_tags": '["技术", "程序员", "深色"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价", "技术栈"]',
        "color_themes": '{"primary": "#58a6ff", "accent": "#3fb950", "bg": "#0d1117", "text": "#c9d1d9"}',
        "html_structure": (
            '<div class="resume dev-pro">'
            '<div class="header"><h1>{{name}}</h1>'
            '<p class="gh-username">{{email}} | {{phone}} | {{location}}</p></div>'
            '<div class="section"><h2>## 教育背景</h2>{{education_list}}</div>'
            '<div class="section"><h2>## 工作经历</h2>{{experience_list}}</div>'
            '<div class="section"><h2>## 项目经历</h2>{{projects_list}}</div>'
            '<div class="section"><h2>## 技术栈</h2>{{skills_list}}</div>'
            '<div class="section"><h2>## 关于我</h2><p>{{self_evaluation}}</p></div>'
            '</div>'
        ),
        "css_rules": (
            '.resume.dev-pro{max-width:750px;margin:0 auto;padding:30px;font-family:"SF Mono","Consolas",'
            '"Microsoft YaHei",monospace;background:#0d1117;color:#c9d1d9;border:1px solid #30363d;'
            'border-radius:6px}'
            '.header{text-align:center;border-bottom:1px solid #30363d;padding-bottom:20px;margin-bottom:20px}'
            '.header h1{font-size:28px;color:#58a6ff;margin:0}'
            '.gh-username{font-size:12px;color:#8b949e;margin:8px 0 0}'
            '.section{margin-bottom:20px}'
            '.section h2{font-size:14px;color:#58a6ff;margin:0 0 10px}'
            '.section p{font-size:13px;color:#c9d1d9;line-height:1.6}'
        ),
    },
    {
        "name": "极客风",
        "category": "技术/程序员",
        "description": "终端风格设计，技能标签化展示，适合全栈/DevOps工程师",
        "style_tags": '["技术", "极客", "终端"]',
        "supported_sections": '["基本信息", "教育背景", "工作经历", "项目经历", "技能", "自我评价", "技术栈"]',
        "color_themes": '{"primary": "#00ff00", "accent": "#00cc00", "bg": "#0c0c0c", "text": "#cccccc"}',
        "html_structure": (
            '<div class="resume geek">'
            '<div class="terminal-header">$ cat ~/resume.txt</div>'
            '<div class="terminal-body">'
            '<div class="prompt">$ whoami</div><h1>{{name}}</h1>'
            '<div class="prompt">$ echo $CONTACT</div><p>{{email}} | {{phone}} | {{location}}</p>'
            '<div class="prompt">$ cat education.md</div>{{education_list}}'
            '<div class="prompt">$ cat experience.log</div>{{experience_list}}'
            '<div class="prompt">$ cat projects/</div>{{projects_list}}'
            '<div class="prompt">$ tech-stack --list</div>{{skills_list}}'
            '<div class="prompt">$ cat about.md</div><p>{{self_evaluation}}</p>'
            '<div class="prompt">$ <span class="cursor">_</span></div>'
            '</div></div>'
        ),
        "css_rules": (
            '.resume.geek{max-width:750px;margin:0 auto;font-family:"SF Mono","Consolas","Courier New",monospace;'
            'border:1px solid #333;border-radius:6px;overflow:hidden}'
            '.terminal-header{background:#2d2d2d;color:#999;padding:8px 16px;font-size:12px}'
            '.terminal-body{background:#0c0c0c;color:#ccc;padding:20px;line-height:1.7}'
            '.prompt{color:#00ff00;font-size:13px;margin:12px 0 4px}'
            '.prompt:first-child{margin-top:0}'
            '.terminal-body h1{font-size:24px;color:#fff;margin:4px 0}'
            '.terminal-body p{font-size:13px;color:#aaa;margin:4px 0}'
            '.cursor{display:inline-block;background:#00ff00;width:8px;height:16px;animation:blink 1s infinite}'
            '@keyframes blink{0%,50%{opacity:1}51%,100%{opacity:0}}'
        ),
    },
]


async def seed_templates():
    """向数据库写入30套模板（幂等）。"""
    from sqlalchemy import func, select
    from app.core.database import AsyncSessionLocal, engine
    from app.models.resume_template import ResumeTemplate

    print("=" * 60)
    print("  简历模板种子数据导入")
    print("=" * 60)

    # 确保表存在
    from app.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count()).select_from(ResumeTemplate).where(ResumeTemplate.is_builtin == True)
        )
        existing = result.scalar() or 0
        if existing >= 30:
            print(f"  已有 {existing} 套内置模板，跳过导入")
        else:
            # 先删除旧的内置模板（兼容旧10套模板）
            if existing > 0 and existing < 30:
                from sqlalchemy import delete
                await session.execute(
                    delete(ResumeTemplate).where(ResumeTemplate.is_builtin == True)
                )
                await session.commit()
                print(f"  已清除 {existing} 套旧模板，准备导入新模板...")

            for i, tpl in enumerate(TEMPLATES, 1):
                session.add(ResumeTemplate(
                    name=tpl["name"],
                    category=tpl["category"],
                    description=tpl["description"],
                    html_structure=tpl["html_structure"],
                    css_rules=tpl["css_rules"],
                    style_tags=tpl["style_tags"],
                    supported_sections=tpl["supported_sections"],
                    color_themes=tpl["color_themes"],
                    is_builtin=True,
                    is_public=True,
                    downloads=0,
                ))
            await session.commit()
            print(f"  完成，共导入 {len(TEMPLATES)} 套模板")

    await engine.dispose()
    print("\n模板导入完毕！")


if __name__ == "__main__":
    asyncio.run(seed_templates())
