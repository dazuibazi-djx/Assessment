"""arXiv 检索。"""

from __future__ import annotations

import re
from typing import Any

from langchain.tools import tool

try:
    import arxiv
except ImportError:  # pragma: no cover
    arxiv = None


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9\-\+]{2,}")
STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "in",
    "of",
    "on",
    "the",
    "to",
    "with",
}
CATEGORY_HINTS = {
    "cs.CV": {"vision", "image", "images", "video", "videos", "object", "segmentation", "detection"},
    "cs.CL": {"language", "text", "llm", "bert", "gpt", "translation", "summarization"},
    "cs.LG": {"learning", "neural", "network", "networks", "diffusion", "transformer", "graph"},
    "cs.AI": {"agent", "planning", "reasoning", "reinforcement"},
    "cs.RO": {"robot", "robotics", "slam", "navigation"},
}


class ArxivSearchError(RuntimeError):
    """检索失败。"""


def search_arxiv(query: str, max_results: int = 5, **_: Any) -> list[dict[str, Any]]:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("query 不能为空，请输入关键词。")
    if max_results <= 0:
        raise ValueError("max_results 必须大于 0。")
    if arxiv is None:
        raise ArxivSearchError("未安装 arxiv 库，请先执行 `pip install arxiv`。")

    tokens = _query_tokens(cleaned_query)
    search = arxiv.Search(
        query=_build_search_query(cleaned_query, tokens),
        max_results=_candidate_count(max_results),
        sort_by=arxiv.SortCriterion.LastUpdatedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    client = arxiv.Client(
        page_size=min(_candidate_count(max_results), 50),
        delay_seconds=3.0,
        num_retries=3,
    )

    try:
        papers = [_format_result(item) for item in client.results(search)]
    except Exception as exc:  # noqa: BLE001
        raise ArxivSearchError(f"arXiv 检索失败: {exc}") from exc

    ranked = _rerank_papers(cleaned_query, papers)
    return ranked[:max_results]


@tool("arxiv_search")
def arxiv_search_tool(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """根据关键词检索 arXiv 论文。"""
    return search_arxiv(query=query, max_results=max_results)


def _candidate_count(max_results: int) -> int:
    return min(max(max_results * 4, max_results), 20)


def _build_search_query(query: str, tokens: list[str]) -> str:
    category_hints = _category_hints(tokens)
    clauses = [f'all:"{query}"']

    if tokens:
        token_clause = " AND ".join(f"all:{token}" for token in tokens[:5])
        clauses.append(token_clause)

    search_clause = " OR ".join(f"({item})" for item in clauses)
    if not category_hints:
        return search_clause

    category_clause = " OR ".join(f"cat:{category}" for category in sorted(category_hints))
    return f"({search_clause}) AND ({category_clause})"


def _rerank_papers(query: str, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query_text = query.lower().strip()
    tokens = _query_tokens(query)
    category_hints = _category_hints(tokens)

    def score(paper: dict[str, Any]) -> tuple[float, str]:
        title = str(paper.get("title", "")).lower()
        abstract = str(paper.get("abstract", "")).lower()
        category = str(paper.get("primary_category", ""))
        combined = f"{title} {abstract}"

        value = 0.0
        if query_text and query_text in title:
            value += 10.0
        if query_text and query_text in abstract:
            value += 4.0

        token_hits = 0
        for token in tokens:
            if token in title:
                value += 3.0
                token_hits += 1
            elif token in abstract:
                value += 1.0
                token_hits += 1

        if tokens and token_hits == len(tokens):
            value += 3.0
        elif tokens and token_hits >= max(1, len(tokens) // 2):
            value += 1.0

        if category in category_hints:
            value += 2.5

        # 没有命中任何主题词时，基本说明只是“碰巧被搜到”。
        if tokens and not any(token in combined for token in tokens):
            value -= 5.0

        updated = str(paper.get("updated", ""))
        return value, updated

    return sorted(papers, key=score, reverse=True)


def _query_tokens(query: str) -> list[str]:
    tokens: list[str] = []
    for match in TOKEN_PATTERN.findall(query.lower()):
        if match in STOPWORDS:
            continue
        if match not in tokens:
            tokens.append(match)
    return tokens


def _category_hints(tokens: list[str]) -> set[str]:
    matched: set[str] = set()
    token_set = set(tokens)
    for category, keywords in CATEGORY_HINTS.items():
        if token_set & keywords:
            matched.add(category)
    return matched


def _format_result(result: Any) -> dict[str, Any]:
    return {
        "arxiv_id": _extract_arxiv_id(result),
        "title": _clean_text(getattr(result, "title", "")),
        "authors": [author.name for author in getattr(result, "authors", [])],
        "abstract": _clean_text(getattr(result, "summary", "")),
        "published": _format_datetime(getattr(result, "published", None)),
        "updated": _format_datetime(getattr(result, "updated", None)),
        "pdf_url": getattr(result, "pdf_url", "") or "",
        "primary_category": getattr(result, "primary_category", "") or "",
    }


def _extract_arxiv_id(result: Any) -> str:
    getter = getattr(result, "get_short_id", None)
    if callable(getter):
        return getter()

    entry_id = getattr(result, "entry_id", "") or ""
    if entry_id:
        return entry_id.rsplit("/", 1)[-1]
    return ""


def _format_datetime(value: Any) -> str:
    if value is None:
        return ""
    return value.isoformat()


def _clean_text(text: str) -> str:
    return " ".join(text.split())
