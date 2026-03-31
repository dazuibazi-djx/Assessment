"""arXiv 检索工具。"""

from __future__ import annotations

from config import Settings
from src.schemas import PaperMetadata


def search_arxiv(query: str, settings: Settings, max_results: int = 5) -> list[PaperMetadata]:
    """检索 arXiv 论文。

    后续将在这里接入 arXiv API，并返回带有 `arxiv_id` 的论文列表。
    当前先保留清晰接口，不写完整业务逻辑。
    """
    raise NotImplementedError("arXiv 检索逻辑尚未实现。")
