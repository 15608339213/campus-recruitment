from __future__ import annotations
"""DeepSeek API 封装。

直接通过 HTTP 调用 DeepSeek API（不使用 LangChain），实现：
1. 简历定制生成
2. 行业分析 + 职业规划
3. 面试技巧生成

DeepSeek API 兼容 OpenAI 接口格式：
POST {base_url}/v1/chat/completions
"""

import json
from typing import Optional, List, Dict, Any

import httpx

from app.core.config import settings


class DeepSeekError(Exception):
    """DeepSeek API 调用异常。"""

    pass


class DeepSeekClient:
    """DeepSeek API 客户端封装。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.base_url = (base_url or settings.DEEPSEEK_BASE_URL).rstrip("/")
        self.model = model or settings.DEEPSEEK_MODEL
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
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

    async def close(self) -> None:
        """关闭 HTTP 客户端。"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Dict[str, str] | None = None,
    ) -> str:
        """调用 DeepSeek Chat Completions 接口。

        Args:
            messages: 对话消息列表 [{"role": "system"/"user"/"assistant", "content": "..."}]
            temperature: 采样温度
            max_tokens: 最大生成 token 数
            response_format: 响应格式，如 {"type": "json_object"} 启用 JSON 模式

        Returns:
            AI 生成的文本内容

        Raises:
            DeepSeekError: API 调用失败时抛出。
        """
        if not self.api_key:
            raise DeepSeekError("未配置 DEEPSEEK_API_KEY，请在 .env 中设置")

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
            raise DeepSeekError(
                f"DeepSeek API 返回错误 {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise DeepSeekError(f"DeepSeek API 请求失败: {e}") from e

        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Any:
        """调用 DeepSeek 并解析 JSON 响应。"""
        content = await self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise DeepSeekError(f"AI 返回的内容无法解析为 JSON: {content[:200]}") from e

    # ===== 简历定制生成 =====
    async def generate_resume(
        self,
        user_profile: Dict[str, Any],
        job_description: str,
        extra_info: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """根据用户档案和目标岗位生成定制化简历。

        Args:
            user_profile: 用户档案信息（技能、经历、项目等）
            job_description: 目标岗位描述
            extra_info: 额外补充信息

        Returns:
            结构化的简历内容 JSON
        """
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

    # ===== 行业分析 + 职业规划 =====
    async def analyze_industry_recommendation(
        self,
        major: str,
        industry_stats: Dict[str, Any],
        user_skills: List[str] | None = None,
    ) -> Dict[str, Any]:
        """根据用户专业和行业数据生成职业规划推荐。

        Args:
            major: 用户专业
            industry_stats: 行业统计数据（岗位数、薪资分布等）
            user_skills: 用户已有技能

        Returns:
            推荐报告 JSON
        """
        system_prompt = (
            "你是一位资深的职业规划顾问。请根据用户的专业背景、技能和当前行业市场数据，"
            "生成个性化的职业规划建议。要求：\n"
            "1. 推荐 3-5 个最适合的行业方向\n"
            "2. 分析每个方向的匹配度和发展前景\n"
            "3. 给出技能提升建议\n"
            "4. 必须返回合法的 JSON 格式\n\n"
            "返回 JSON 结构：\n"
            "{\n"
            '  "summary": "总体分析",\n'
            '  "recommendations": [\n'
            '    {"industry": "", "match_score": 85, "reasons": [""], '
            '"prospects": "", "skill_gaps": [""]}\n'
            "  ],\n"
            '  "skill_suggestions": ["建议学习的技能"],\n'
            '  "action_plan": "短期/中期行动计划"\n'
            "}"
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
        """为指定岗位类别生成面试技巧（Markdown 格式）。

        Args:
            job_category: 岗位类别

        Returns:
            Markdown 格式的面试技巧内容
        """
        system_prompt = (
            "你是一位资深面试辅导专家。请为指定岗位类别生成一份全面的面试技巧指南。"
            "使用 Markdown 格式，包含以下内容：\n"
            "1. 岗位概述与核心能力要求\n"
            "2. 常见面试题型及答题技巧\n"
            "3. 技术面试重点知识点\n"
            "4. HR 面常见问题与应对\n"
            "5. 面试准备清单\n"
            "6. 加分项与避坑指南\n"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请为「{job_category}」岗位类别生成面试技巧指南。"},
        ]

        return await self.chat(messages, temperature=0.7, max_tokens=4096)


# 全局单例（延迟初始化）
_deepseek_client: Optional[DeepSeekClient] = None


def get_deepseek_client() -> DeepSeekClient:
    """获取 DeepSeek 客户端单例。"""
    global _deepseek_client
    if _deepseek_client is None:
        _deepseek_client = DeepSeekClient()
    return _deepseek_client
