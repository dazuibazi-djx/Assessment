"""PDF 文本提取工具。"""

from __future__ import annotations

from pathlib import Path


def extract_pdf_text(pdf_path: Path) -> str:
    """从 PDF 中提取文本内容。

    后续解析结果会配合 `storage.py` 保存到 `data/parsed/`。
    """
    raise NotImplementedError("PDF 解析逻辑尚未实现。")
