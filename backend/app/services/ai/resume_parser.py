"""简历解析 AI 服务。

使用 AI 从简历文本中提取结构化字段，用于自动填充用户资料。
"""

from __future__ import annotations

from typing import Any, Dict

from app.services.ai.provider import AIProviderClient


class ResumeParserService:
    """简历解析服务 - 使用 AI 从文本中提取结构化信息。"""

    def __init__(self, client: AIProviderClient):
        self.client = client

    async def parse(self, resume_text: str) -> Dict[str, Any]:
        """使用 AI 解析简历文本。"""
        return await self.client.parse_resume(resume_text)

    async def extract_and_format(self, resume_text: str) -> Dict[str, Any]:
        """解析并格式化为可直接写入数据库的结构。"""
        raw = await self.parse(resume_text)

        # 格式化输出
        formatted = {
            "school": raw.get("school", ""),
            "major": raw.get("major", ""),
            "degree": raw.get("degree", ""),
            "graduation_year": str(raw.get("graduation_year", "")),
            "phone": raw.get("phone", ""),
            "city": raw.get("city", ""),
            "skills": ", ".join(raw.get("skills", [])) if isinstance(raw.get("skills"), list) else raw.get("skills", ""),
            "experience_json": raw.get("experience", []),
            "projects_json": raw.get("projects", []),
            "name": raw.get("name", ""),
            "email": raw.get("email", ""),
            "languages": raw.get("languages", []),
            "certificates": raw.get("certificates", []),
            # 保留原始解析结果
            "_raw_parsed": raw,
        }

        return formatted
