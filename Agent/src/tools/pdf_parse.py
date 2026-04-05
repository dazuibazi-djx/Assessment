"""PDF 文本提取工具。"""

from __future__ import annotations

from pathlib import Path

import fitz
from langchain.tools import tool


def extract_pdf_text(pdf_path: str | Path, pages: int = 5) -> str:
   
    target_path = Path(pdf_path)

    if pages <= 0:
        return "PDF 解析失败：pages 必须大于 0。"

    if not target_path.exists():
        return f"PDF 解析失败：文件不存在 -> {target_path}"

    if target_path.stat().st_size == 0:
        return f"PDF 解析失败：文件为空 -> {target_path}"

    try:
        document = fitz.open(target_path)
    except Exception as exc: 
        return f"PDF 解析失败：无法打开文件 -> {exc}"

    try:
        if document.page_count == 0:
            return f"PDF 解析失败：PDF 没有可读取的页面 -> {target_path}"

        extracted_pages: list[str] = []
        page_limit = min(pages, document.page_count)

        for page_index in range(page_limit):
            page = document.load_page(page_index)
            page_text = page.get_text("text").strip()
            if page_text:
                extracted_pages.append(page_text)

        if not extracted_pages:
            return f"PDF 解析失败：前 {page_limit} 页没有提取到有效文本 -> {target_path}"

        return "\n\n".join(extracted_pages)
    except Exception as exc: 
        return f"PDF 解析失败：读取页面内容时出错 -> {exc}"
    finally:
        document.close()


@tool("pdf_parse")
def pdf_parse_tool(pdf_path: str, pages: int = 5) -> str:
    """LangChain tool: 解析本地 PDF 文本。"""
    return extract_pdf_text(pdf_path=pdf_path, pages=pages)
