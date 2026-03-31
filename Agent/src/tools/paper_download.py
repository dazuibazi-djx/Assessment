"""PDF 下载工具。"""

from __future__ import annotations

from pathlib import Path

from config import Settings
from src.schemas import PaperMetadata


def download_paper_pdf(paper: PaperMetadata, settings: Settings) -> Path:
    """下载论文 PDF 到本地目录。

    后续将统一使用 `arxiv_id.pdf` 作为文件名，保存到 `data/pdf/`。
    """
    raise NotImplementedError("PDF 下载逻辑尚未实现。")
