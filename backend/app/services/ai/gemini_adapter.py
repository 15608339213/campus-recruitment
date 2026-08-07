"""Google Gemini API 适配器。

Gemini 支持 OpenAI 兼容端点，此适配器封装了认证逻辑。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx


class GeminiAdapter:
    """Gemini API 适配器（通过 OpenAI 兼容端点）。"""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self.api_key = api_key
        self.model = model
        self._client = httpx.AsyncClient(
            base_url="https://generativelanguage.googleapis.com/v1beta",
            headers={"Content-Type": "application/json"},
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
        """调用 Gemini API。"""
        # 将 OpenAI 格式转换为 Gemini 格式
        contents = []
        system_instruction = ""
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                system_instruction = msg.get("content", "")
            else:
                contents.append({
                    "role": "user" if role == "user" else "model",
                    "parts": [{"text": msg.get("content", "")}],
                })

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        url = f"/models/{self.model}:generateContent?key={self.api_key}"
        try:
            resp = await self._client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except httpx.HTTPStatusError as e:
            error_body = e.response.text[:500] if e.response else ""
            raise Exception(f"Gemini API 错误: {e.response.status_code} {error_body}")
        except (KeyError, IndexError):
            raise Exception(f"Gemini 响应格式异常: {json.dumps(data)[:300]}")
        except httpx.RequestError as e:
            raise Exception(f"Gemini API 请求失败: {e}")

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Any:
        """调用 Gemini 并解析 JSON 响应。"""
        # Gemini 需要显式要求 JSON 输出
        json_instruction = " 请只返回合法的 JSON 格式，不要包含任何其他文字。"
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += json_instruction
        content = await self.chat(messages, temperature, max_tokens)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{[\s\S]*\}", content)
            if match:
                return json.loads(match.group())
            raise Exception(f"Gemini 返回非 JSON: {content[:300]}")
