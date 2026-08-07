"""统一 AI 提供商抽象层。

支持所有兼容 OpenAI 接口格式的 AI 服务商：
- DeepSeek (深度求索)
- OpenAI (GPT 系列)
- Moonshot (月之暗面 / Kimi)
- Zhipu (智谱 / GLM)
- Qwen (通义千问)
- 自定义兼容服务

用户可在前端选择/添加自己的 AI 提供商和 API Key。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx


class AIProviderError(Exception):
    """AI 提供商调用异常。"""

    pass


# ===== 内置 AI 提供商预设 =====
BUILTIN_PROVIDERS = {
    "openai": {
        "name": "OpenAI (GPT 系列)",
        "base_url": "https://api.openai.com",
        "models": ["gpt-4.1", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini"],
        "default_model": "gpt-4o",
        "website": "https://platform.openai.com",
        "description": "业界标杆，综合能力最强。GPT-4.1 最新旗舰",
    },
    "deepseek": {
        "name": "DeepSeek (深度求索)",
        "base_url": "https://api.deepseek.com",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "default_model": "deepseek-chat",
        "website": "https://platform.deepseek.com",
        "description": "高性价比，擅长中文理解和代码生成，推荐首选",
    },
    "moonshot": {
        "name": "月之暗面 (Kimi)",
        "base_url": "https://api.moonshot.cn",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "default_model": "moonshot-v1-8k",
        "website": "https://platform.moonshot.cn",
        "description": "超长上下文，适合处理大量文本",
    },
    "zhipu": {
        "name": "智谱 AI (GLM)",
        "base_url": "https://open.bigmodel.cn/api/paas",
        "models": ["glm-4", "glm-4-air", "glm-4-flash", "glm-4-flashx"],
        "default_model": "glm-4-flash",
        "website": "https://open.bigmodel.cn",
        "description": "国产大模型，免费额度充足",
    },
    "qwen": {
        "name": "通义千问 (Qwen)",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode",
        "models": ["qwen3-max", "qwen-plus", "qwen-turbo"],
        "default_model": "qwen-plus",
        "website": "https://dashscope.console.aliyun.com",
        "description": "阿里云出品，Qwen3-Max 中文最强之一",
    },
    "baichuan": {
        "name": "百川智能 (Baichuan)",
        "base_url": "https://api.baichuan-ai.com",
        "models": ["Baichuan4-Turbo", "Baichuan3-Turbo"],
        "default_model": "Baichuan4-Turbo",
        "website": "https://platform.baichuan-ai.com",
        "description": "搜增强生成，知识面广",
    },
    "yi": {
        "name": "零一万物 (Yi)",
        "base_url": "https://api.lingyiwanwu.com",
        "models": ["yi-large", "yi-medium", "yi-spark"],
        "default_model": "yi-medium",
        "website": "https://platform.lingyiwanwu.com",
        "description": "李开复创办，中英双语强",
    },
    "claude": {
        "name": "Anthropic Claude",
        "base_url": "https://api.anthropic.com",
        "models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
        "default_model": "claude-sonnet-4-20250514",
        "website": "https://console.anthropic.com",
        "description": "长文本理解与写作顶尖，适合简历优化",
        "headers": {"x-api-key": "{api_key}", "anthropic-version": "2023-06-01"},
        "api_style": "anthropic",
    },
    "gemini": {
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com",
        "models": ["gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-pro"],
        "default_model": "gemini-2.0-flash",
        "website": "https://aistudio.google.com",
        "description": "免费额度大，多模态能力最强",
        "api_style": "gemini",
    },
    "doubao": {
        "name": "豆包 (字节跳动)",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "models": ["doubao-pro-32k", "doubao-lite-32k"],
        "default_model": "doubao-pro-32k",
        "website": "https://console.volcengine.com/ark",
        "description": "中文优化，响应速度快，字节出品",
    },
    "custom": {
        "name": "自定义服务商",
        "base_url": "",
        "models": [],
        "default_model": "",
        "website": "",
        "description": "填写任意兼容 OpenAI 接口的服务地址",
    },
}


class AIProviderClient:
    """统一的 AI 提供商客户端。

    所有兼容 OpenAI /v1/chat/completions 接口的服务商均可使用。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        provider_id: str = "custom",
    ) -> None:
        if not api_key:
            raise AIProviderError("API Key 不能为空，请先配置您的 AI 密钥")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.provider_id = provider_id
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(90.0, connect=15.0),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """调用 /v1/chat/completions 接口。"""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if response_format:
            payload["response_format"] = response_format

        try:
            response = await self.client.post("/v1/chat/completions", json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_body = e.response.text[:500] if e.response else ""
            raise AIProviderError(
                f"AI 服务返回错误 {e.response.status_code}: {error_body}"
            ) from e
        except httpx.RequestError as e:
            raise AIProviderError(f"AI 服务请求失败: {e}") from e

        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Any:
        """调用 AI 并解析 JSON 响应。"""
        content = await self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 某些服务商不支持 response_format，尝试从文本中提取 JSON
            import re

            match = re.search(r"\{[\s\S]*\}", content)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            raise AIProviderError(f"AI 返回的内容无法解析为 JSON: {content[:300]}")

    async def test_connection(self) -> Dict[str, Any]:
        """测试 API 连接是否正常。"""
        try:
            result = await self.chat(
                messages=[
                    {"role": "user", "content": "请回复：连接成功"},
                ],
                temperature=0.0,
                max_tokens=20,
            )
            return {
                "success": True,
                "message": "连接测试成功",
                "response": result[:100],
            }
        except AIProviderError as e:
            return {"success": False, "message": str(e)}

    # ===== 简历定制生成 =====
    async def generate_resume(
        self,
        user_profile: Dict[str, Any],
        job_description: str,
        extra_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """根据用户档案和目标岗位生成定制化简历。"""
        system_prompt = (
            "你是一位资深的简历定制专家。请根据用户的教育背景、技能、经历和目标岗位要求，"
            "生成一份高度匹配的定制化简历。要求：\n"
            "1. 突出与目标岗位匹配的能力和经历\n"
            "2. 用 STAR 法则描述项目经历\n"
            "3. 技能列表按相关度排序\n"
            "4. 自我评价简洁有力，针对岗位定制\n"
            "5. 必须返回合法的 JSON 格式\n\n"
            "返回 JSON 结构：\n"
            "{\n"
            '  "basic_info": {"name": "", "phone": "", "email": ""},\n'
            '  "education": [{"school": "", "major": "", "degree": "", "period": ""}],\n'
            '  "experience": [{"company": "", "role": "", "period": "", "description": ""}],\n'
            '  "projects": [{"name": "", "role": "", "description": "", "tech_stack": ""}],\n'
            '  "skills": ["技能1", "技能2"],\n'
            '  "self_evaluation": "针对岗位的自我评价",\n'
            '  "raw_markdown": "完整的 Markdown 格式简历"\n'
            "}"
        )

        user_message = (
            f"## 用户档案\n{json.dumps(user_profile, ensure_ascii=False, indent=2)}\n\n"
            f"## 目标岗位描述\n{job_description}\n"
        )
        if extra_info:
            user_message += (
                f"\n## 额外补充信息\n"
                f"{json.dumps(extra_info, ensure_ascii=False, indent=2)}\n"
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        return await self.chat_json(messages, temperature=0.7, max_tokens=4096)

    # ===== 行业分析 =====
    async def analyze_industry_recommendation(
        self,
        major: str,
        industry_stats: Dict[str, Any],
        user_skills: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """行业分析 + 职业规划推荐。"""
        system_prompt = (
            "你是一位资深的职业规划顾问。请根据用户的专业背景、技能和当前行业市场数据，"
            "生成个性化的职业规划建议。要求返回合法 JSON，包含：\n"
            "- summary: 总体分析\n"
            "- recommendations: 推荐的 3-5 个行业方向（含 match_score/reasons/prospects/skill_gaps）\n"
            "- skill_suggestions: 建议学习的技能\n"
            "- action_plan: 行动计划"
        )

        user_message = (
            f"## 用户专业\n{major}\n\n"
            f"## 用户技能\n{json.dumps(user_skills or [], ensure_ascii=False)}\n\n"
            f"## 当前行业市场数据\n{json.dumps(industry_stats, ensure_ascii=False, indent=2)}\n"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        return await self.chat_json(messages, temperature=0.7, max_tokens=4096)

    # ===== 面试技巧生成 =====
    async def generate_interview_tips(self, job_category: str) -> str:
        """为指定岗位类别生成面试技巧（Markdown 格式）。"""
        system_prompt = (
            "你是一位资深面试辅导专家。请为指定岗位类别生成一份全面的面试技巧指南，"
            "使用 Markdown 格式，包含：岗位概述、常见面试题、技术重点、HR 面技巧、准备清单、加分项。"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请为「{job_category}」岗位类别生成面试技巧指南。"},
        ]

        return await self.chat(messages, temperature=0.7, max_tokens=4096)
