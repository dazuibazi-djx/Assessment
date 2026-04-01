"""arXiv 论文检索工具。"""

from __future__ import annotations

from typing import Any

from langchain.tools import tool

try:
    import arxiv
except ImportError:  # pragma: no cover - 依赖缺失时由运行时提示
    arxiv = None


class ArxivSearchError(RuntimeError):
    """arXiv 检索异常。"""


def search_arxiv(query: str, max_results: int = 5, **_: Any) -> list[dict[str, Any]]:
    """检索 arXiv 论文。

    这个函数给 pipeline 直接调用，返回值是 `list[dict]`，
    每个字典都只保留后续流程真正会用到的核心字段。
    """
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("query 不能为空，请输入论文主题或关键词。")

    if max_results <= 0:
        raise ValueError("max_results 必须大于 0。")

    if arxiv is None:
        raise ArxivSearchError("未安装 arxiv 库，请先执行 `pip install arxiv`。")

    search = arxiv.Search(
        query=cleaned_query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.LastUpdatedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    # Client 会负责发请求
    client = arxiv.Client(
        page_size=min(max_results, 100),
        delay_seconds=3.0,
        num_retries=3,
    )

    try:
        papers = [_format_result(result) for result in client.results(search)]
    except Exception as exc:  # noqa: BLE001
        raise ArxivSearchError(f"arXiv 检索失败: {exc}") from exc

    return papers


@tool("arxiv_search")
def arxiv_search_tool(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """LangChain tool: 根据关键词检索 arXiv 论文。"""
    return search_arxiv(query=query, max_results=max_results)


def _format_result(result: Any) -> dict[str, Any]:
    """把 arxiv 返回的结果对象整理成普通字典。
    这样做的好处是：
    1. pipeline 不需要了解 arxiv 库内部对象结构
    2. 后续保存到 JSON 或传给其他模块会更方便
    """
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
    """优先提取短 arXiv ID，例如 `2501.00001v1`。"""
    short_id_getter = getattr(result, "get_short_id", None)
    if callable(short_id_getter):
        return short_id_getter()

    entry_id = getattr(result, "entry_id", "") or ""
    if entry_id:
        return entry_id.rsplit("/", 1)[-1]

    return ""


def _format_datetime(value: Any) -> str:
    """把时间对象转成 ISO 字符串，便于后续保存。"""
    if value is None:
        return ""
    return value.isoformat()


def _clean_text(text: str) -> str:
    """清理多余空白，让标题和摘要更适合直接展示。"""
    return " ".join(text.split())
