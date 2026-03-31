"""论文分析与审稿工具。"""

from __future__ import annotations

from config import Settings
from src.schemas import PaperMetadata, PaperReview


def review_paper(paper: PaperMetadata, paper_text: str, settings: Settings) -> PaperReview:
    """生成审稿式评价与评分。

    后续输出重点包括：
    - 优点
    - 缺点
    - 综合评分
    - 接收建议
    """
    raise NotImplementedError("论文审稿逻辑尚未实现。")
