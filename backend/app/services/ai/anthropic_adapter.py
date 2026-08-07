"""Anthropic Claude Messages API 适配器。

将 OpenAI 格式的 messages 转换为 Anthropic Messages API 格式。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx


class AnthropicAdapter:
    """Anthropic Messages API 适配器。"""

    ANTHROPIC_VERSION = "2023-06-01"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self._client = httpx.AsyncClient(
            base_url="https://api.anthropic.com",
            headers={
                "x-api-key": api_key,
                "anthropic-version": self.ANTHROPIC_VERSION,
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(90.0, connect=15.0),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """发送对话到 Anthropic Messages API。

        将 OpenAI 格式 messages 转换为 Anthropic 格式：
        - system 消息提取为顶层 system 参数
        - user/assistant 消息保持原样
        """
        system_prompt = ""
        anthropic_messages: List[Dict[str, Any]] = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                system_prompt = content
            elif role in ("user", "assistant"):
                anthropic_messages.append({"role": role, "content": content})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            resp = await self._client.post("/v1/messages", json=payload)
            resp.raise_for_status()
            data = resp.json()
            # Anthropic 返回 content[0].text
            return data["content"][0]["text"]
        except httpx.HTTPStatusError as e:
            error_body = e.response.text[:500] if e.response else ""
            raise Exception(f"Claude API 错误: {e.response.status_code} {error_body}")
        except httpx.RequestError as e:
            raise Exception(f"Claude API 请求失败: {e}")

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Any:
        """调用 Claude 并解析 JSON 响应。"""
        content = await self.chat(messages, temperature, max_tokens)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{[\s\S]*\}", content)
            if match:
                return json.loads(match.group())
            raise Exception(f"Claude 返回非 JSON: {content[:300]}")
