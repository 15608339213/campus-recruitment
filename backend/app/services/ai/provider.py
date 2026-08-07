"""统一 AI 提供商抽象层 — v2.1 升级版。

支持 OpenAI 格式 + Anthropic Messages API + Gemini API 三大协议：
- OpenAI 格式（直通）：GPT-4.1, DeepSeek V4, Qwen3.8, Kimi K2.6, 豆包Seed2.1, ERNIE 4.5
- Anthropic Messages API（适配）：Claude Sonnet 4 / Opus 4.1
- Gemini API（兼容模式）：Gemini 2.5 Pro

用户可在前端选择/添加自己的 AI 提供商和 API Key。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx


class AIProviderError(Exception):
    """AI 提供商调用异常。"""
    pass


# ===== 内置 AI 提供商预设（2026年8月最新） =====
BUILTIN_PROVIDERS = {
    "openai": {
        "name": "OpenAI (GPT 系列)",
        "base_url": "https://api.openai.com",
        "models": ["gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o", "o3-mini"],
        "default_model": "gpt-4.1-mini",
        "website": "https://platform.openai.com",
        "description": "业界标杆，GPT-4.1 最新旗舰，百万token上下文",
        "tags": ["最强推理", "英文最强"],
    },
    "deepseek": {
        "name": "DeepSeek (深度求索)",
        "base_url": "https://api.deepseek.com",
        "models": ["deepseek-v4-flash", "deepseek-v4-pro"],
        "default_model": "deepseek-v4-flash",
        "website": "https://platform.deepseek.com",
        "description": "高性价比之王，100万上下文，代码能力强",
        "tags": ["推荐", "性价比之王", "代码最强"],
    },
    "claude": {
        "name": "Anthropic Claude",
        "base_url": "https://api.anthropic.com",
        "models": ["claude-sonnet-4-20250514", "claude-opus-4-1-20250806", "claude-haiku-4-5"],
        "default_model": "claude-sonnet-4-20250514",
        "website": "https://console.anthropic.com",
        "description": "长文本理解与写作最强，适合简历优化和深度分析",
        "headers": {"x-api-key": "{api_key}", "anthropic-version": "2023-06-01"},
        "api_style": "anthropic",
        "tags": ["最强写作", "长文本"],
    },
    "gemini": {
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com",
        "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
        "default_model": "gemini-2.5-flash",
        "website": "https://aistudio.google.com",
        "description": "免费额度慷慨，多模态能力最强",
        "api_style": "gemini",
        "tags": ["免费额度大", "多模态"],
    },
    "qwen": {
        "name": "通义千问 (Qwen3)",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode",
        "models": ["qwen3.8-max", "qwen3-max", "qwen-plus", "qwen-turbo"],
        "default_model": "qwen-plus",
        "website": "https://dashscope.console.aliyun.com",
        "description": "阿里出品，Qwen3.8-Max中文最强之一，2.4万亿参数",
        "tags": ["中文最强", "企业级"],
    },
    "kimi": {
        "name": "月之暗面 (Kimi K2.6)",
        "base_url": "https://api.moonshot.cn",
        "models": ["kimi-k2.6", "kimi-k2"],
        "default_model": "kimi-k2.6",
        "website": "https://platform.kimi.com",
        "description": "超长上下文256K，支持图片+视频输入",
        "tags": ["超长上下文", "多模态"],
    },
    "doubao": {
        "name": "豆包 Seed 2.1 (字节跳动)",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "models": ["doubao-seed-2.1-pro", "doubao-seed-2.1-turbo", "doubao-seed-2.1-lite"],
        "default_model": "doubao-seed-2.1-turbo",
        "website": "https://console.volcengine.com/ark",
        "description": "字节出品，中文优化极致，日均120万亿tokens",
        "tags": ["中文优化", "高并发"],
    },
    "zhipu": {
        "name": "智谱 AI (GLM)",
        "base_url": "https://open.bigmodel.cn/api/paas",
        "models": ["glm-4-plus", "glm-4-air", "glm-4-flash"],
        "default_model": "glm-4-flash",
        "website": "https://open.bigmodel.cn",
        "description": "国产大模型先驱，免费额度充足，API稳定",
        "tags": ["国产稳定", "免费额度"],
    },
    "ernie": {
        "name": "文心一言 (ERNIE 4.5)",
        "base_url": "https://qianfan.baidubce.com/v2",
        "models": ["ernie-4.5-turbo", "ernie-4.5", "ernie-x1"],
        "default_model": "ernie-4.5-turbo",
        "website": "https://qianfan.cloud.baidu.com",
        "description": "百度出品，ERNIE 4.5 Turbo 性价比极高",
        "tags": ["百度生态", "性价比"],
    },
    "baichuan": {
        "name": "百川智能 (Baichuan)",
        "base_url": "https://api.baichuan-ai.com",
        "models": ["Baichuan4-Turbo", "Baichuan4-Air"],
        "default_model": "Baichuan4-Turbo",
        "website": "https://platform.baichuan-ai.com",
        "description": "搜增强生成，知识面广",
        "tags": ["搜索增强"],
    },
    "yi": {
        "name": "零一万物 (Yi)",
        "base_url": "https://api.lingyiwanwu.com",
        "models": ["yi-large", "yi-medium", "yi-spark"],
        "default_model": "yi-medium",
        "website": "https://platform.lingyiwanwu.com",
        "description": "李开复创办，中英双语强",
        "tags": ["中英双语"],
    },
    "spark": {
        "name": "讯飞星火 (Spark)",
        "base_url": "https://spark-api-open.xf-yun.com/v1",
        "models": ["spark-lite", "spark-4.0-ultra", "spark-max"],
        "default_model": "spark-lite",
        "website": "https://xinghuo.xfyun.cn",
        "description": "Spark Lite 永久免费，适合轻量任务",
        "tags": ["永久免费", "语音识别强"],
    },
    "llama": {
        "name": "Llama 4 (Meta / 第三方)",
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["llama-4-scout", "llama-4-maverick"],
        "default_model": "llama-4-scout",
        "website": "https://groq.com",
        "description": "开源最强，通过Groq等第三方API调用，极速推理",
        "tags": ["开源", "第三方API"],
    },
    "custom": {
        "name": "自定义服务商",
        "base_url": "",
        "models": [],
        "default_model": "",
        "website": "",
        "description": "填写任意兼容 OpenAI 接口的服务地址",
        "tags": [],
    },
}


class AIProviderClient:
    """统一的 AI 提供商客户端 — v2.1 多协议支持。

    支持三种 API 风格：
    - openai (默认): 兼容 /v1/chat/completions 的所有服务商
    - anthropic: Claude Messages API 原生格式
    - gemini: Gemini API 通过 OpenAI 兼容端点
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        provider_id: str = "custom",
        api_style: str = "openai",
    ) -> None:
        if not api_key:
            raise AIProviderError("API Key 不能为空，请先配置您的 AI 密钥")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.provider_id = provider_id
        self.api_style = api_style
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {"Content-Type": "application/json"}
            if self.api_style == "anthropic":
                headers["x-api-key"] = self.api_key
                headers["anthropic-version"] = "2023-06-01"
            elif self.api_style == "gemini":
                # Gemini 用 key 参数，不需要 Authorization header
                headers["x-goog-api-key"] = self.api_key
                pass
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=httpx.Timeout(120.0, connect=15.0),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ===== 统一路由入口 =====
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """调用 AI 聊天接口，根据 api_style 自动路由。"""
        if self.api_style == "anthropic":
            return await self._chat_anthropic(messages, temperature, max_tokens)
        elif self.api_style == "gemini":
            return await self._chat_gemini(messages, temperature, max_tokens, response_format)
        else:
            return await self._chat_openai(messages, temperature, max_tokens, response_format)

    # ===== OpenAI 兼容格式调用（直通） =====
    async def _chat_openai(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """调用 OpenAI 兼容的 /v1/chat/completions 接口。"""
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

    # ===== Anthropic Messages API 调用（适配器） =====
    async def _chat_anthropic(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """调用 Anthropic Messages API。

        OpenAI messages 格式转换规则：
        - OpenAI system → Anthropic top-level system param
        - OpenAI user/assistant → Anthropic messages (role mapping)
        - 保留对话顺序
        """
        system_prompt = None
        anthropic_messages = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                system_prompt = content
            elif role in ("user", "assistant"):
                anthropic_messages.append({"role": role, "content": content})

        payload: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": anthropic_messages,
        }
        if system_prompt:
            payload["system"] = system_prompt
        if temperature > 0:
            payload["temperature"] = temperature

        try:
            response = await self.client.post("/v1/messages", json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_body = e.response.text[:500] if e.response else ""
            raise AIProviderError(
                f"Claude API 返回错误 {e.response.status_code}: {error_body}"
            ) from e
        except httpx.RequestError as e:
            raise AIProviderError(f"Claude API 请求失败: {e}") from e

        data = response.json()
        # Anthropic 返回 content 数组，取第一个 text block
        content_blocks = data.get("content", [])
        for block in content_blocks:
            if block.get("type") == "text":
                return block["text"]
        return ""

    # ===== Gemini API 调用（通过 generateContent 端点） =====
    async def _chat_gemini(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """调用 Gemini API (generateContent 端点)。

        OpenAI messages 转换：
        - system → 放入 systemInstruction
        - user/assistant → 交替放入 contents 数组
        """
        system_instruction = None
        contents = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})

        # 针对 DeepSeek 兼容的 Gemini 端点
        # 尝试 OpenAI 兼容端点 /v1beta/openai/chat/completions
        try:
            payload: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
            }
            if temperature > 0:
                payload["temperature"] = temperature
            if max_tokens:
                payload["max_tokens"] = max_tokens

            response = await self.client.post(
                "/v1beta/openai/chat/completions", json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (httpx.HTTPStatusError, httpx.RequestError):
            pass

        # 回退到原生 generateContent
        generation_config: Dict[str, Any] = {}
        if temperature > 0:
            generation_config["temperature"] = temperature
        if max_tokens:
            generation_config["maxOutputTokens"] = max_tokens

        payload: Dict[str, Any] = {"contents": contents}
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        if generation_config:
            payload["generationConfig"] = generation_config

        try:
            url = f"/v1beta/models/{self.model}:generateContent"
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_body = e.response.text[:500] if e.response else ""
            raise AIProviderError(
                f"Gemini API 返回错误 {e.response.status_code}: {error_body}"
            ) from e
        except httpx.RequestError as e:
            raise AIProviderError(f"Gemini API 请求失败: {e}") from e

        data = response.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                if "text" in part:
                    return part["text"]
        raise AIProviderError("Gemini 返回内容为空")

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Any:
        """调用 AI 并解析 JSON 响应。"""
        response_format = None
        if self.api_style == "openai":
            response_format = {"type": "json_object"}

        content = await self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )
        try:
            return json.loads(content)
        except json.JSONDecodeError:
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

    # ===== 简历解析 =====
    async def parse_resume(
        self,
        resume_text: str,
    ) -> Dict[str, Any]:
        """从简历文本中提取结构化字段。"""
        system_prompt = (
            "你是一位精准的简历解析专家。请从用户提供的简历文本中提取以下结构化信息。"
            "对于无法确定的字段，请使用空字符串或空数组。"
            "必须返回合法 JSON。\n\n"
            "返回 JSON 结构：\n"
            "{\n"
            '  "name": "姓名",\n'
            '  "phone": "手机号",\n'
            '  "email": "邮箱",\n'
            '  "city": "所在城市",\n'
            '  "school": "最高学历学校",\n'
            '  "major": "专业",\n'
            '  "degree": "学历（大专/本科/硕士/博士）",\n'
            '  "graduation_year": "毕业年份",\n'
            '  "skills": ["技能1", "技能2"],\n'
            '  "experience": [{"company": "公司", "position": "职位", "start_date": "开始", "end_date": "结束", "description": "工作描述"}],\n'
            '  "projects": [{"name": "项目名", "role": "角色", "description": "描述", "tech_stack": "技术栈"}],\n'
            '  "languages": ["语言1"],\n'
            '  "certificates": ["证书1"]\n'
            "}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"## 简历文本\n{resume_text[:8000]}"},
        ]

        return await self.chat_json(messages, temperature=0.1, max_tokens=2048)

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
