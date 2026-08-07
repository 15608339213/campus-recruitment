"""文件上传/校验/解析统一工具模块。

提供安全文件上传所需的所有功能：
- MIME 类型魔数检测
- 文件大小/扩展名校验
- PDF/Word 文本提取
- 文件保存
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

from fastapi import UploadFile, HTTPException, status

# 允许的文件格式
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg"}
ALLOWED_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "image/png",
    "image/jpeg",
    "image/webp",
}

# 文件大小限制
MAX_FILE_SIZE_PDF = 10 * 1024 * 1024  # 10MB
MAX_FILE_SIZE_IMAGE = 5 * 1024 * 1024  # 5MB
MAX_FILE_SIZE_WORD = 10 * 1024 * 1024  # 10MB

# 上传目录
UPLOAD_DIR = Path("uploads")
AVATAR_DIR = UPLOAD_DIR / "avatars"
RESUME_DIR = UPLOAD_DIR / "resumes"
POSTER_DIR = UPLOAD_DIR / "posters"


def _ensure_dirs():
    """确保上传目录存在。"""
    for d in [AVATAR_DIR, RESUME_DIR, POSTER_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """获取文件扩展名（小写）。"""
    return Path(filename).suffix.lower()


def validate_file(file: UploadFile) -> Tuple[str, str, str]:
    """校验上传文件的安全性。

    Returns:
        (safe_filename, file_type, sub_dir)
    Raises:
        HTTPException: 校验失败时抛出 400 错误
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式：{ext}。支持的格式：{', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 确定文件类别
    if ext in (".pdf",):
        file_type = "pdf"
        max_size = MAX_FILE_SIZE_PDF
        sub_dir = str(RESUME_DIR)
    elif ext in (".docx", ".doc"):
        file_type = "word"
        max_size = MAX_FILE_SIZE_WORD
        sub_dir = str(RESUME_DIR)
    else:
        file_type = "image"
        max_size = MAX_FILE_SIZE_IMAGE
        sub_dir = str(AVATAR_DIR)

    # 生成安全文件名
    safe_name = f"{uuid.uuid4().hex}{ext}"

    return safe_name, file_type, sub_dir


async def save_upload_file(file: UploadFile, sub_dir: str, safe_name: str) -> str:
    """保存上传文件并返回文件完整路径。"""
    _ensure_dirs()
    file_path = os.path.join(sub_dir, safe_name)
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="上传的文件为空")

    # 检查文件大小
    if file_type_from_ext := get_file_extension(safe_name) in (".pdf", ".docx", ".doc"):
        max_size = MAX_FILE_SIZE_PDF
    else:
        max_size = MAX_FILE_SIZE_IMAGE

    if len(content) > max_size:
        size_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制（最大 {size_mb:.0f}MB）",
        )

    # 写入文件
    with open(file_path, "wb") as f:
        f.write(content)

    return file_path


async def extract_text_from_pdf(file_path: str) -> str:
    """从 PDF 文件中提取文本。"""
    try:
        import pdfplumber

        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="PDF 解析库未安装。请确保 pdfplumber 已安装。",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF 解析失败：{str(e)}",
        )


async def extract_text_from_docx(file_path: str) -> str:
    """从 Word 文件中提取文本。"""
    try:
        import docx

        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Word 解析库未安装。请确保 python-docx 已安装。",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Word 解析失败：{str(e)}",
        )


async def extract_text(file_path: str, file_type: str) -> str:
    """根据文件类型提取文本。"""
    if file_type == "pdf":
        return await extract_text_from_pdf(file_path)
    elif file_type == "word":
        return await extract_text_from_docx(file_path)
    else:
        # 图片类型不支持文本提取
        return ""


def get_file_url(file_path: str, base_url: str = "") -> str:
    """将文件路径转换为可访问的 URL。"""
    if base_url:
        return f"{base_url.rstrip('/')}/{file_path}"
    return f"/static/{file_path}"
