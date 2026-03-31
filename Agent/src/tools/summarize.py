"""论文总结工具。"""

from __future__ import annotations

from config import Settings
from src.schemas import PaperMetadata, PaperSummary


def summarize_paper(paper: PaperMetadata, paper_text: str, settings: Settings) -> PaperSummary:
    """生成结构化总结。

    后续输出重点包括摘要压缩、关键点提炼和局限性总结。
    """
    raise NotImplementedError("论文总结逻辑尚未实现。")
