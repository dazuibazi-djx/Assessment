"""轻量工具编排型 Agent。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain.tools import tool

from config import Settings
from src.pipeline import run_pipeline
from src.tools.arxiv_search import search_arxiv
from src.tools.paper_download import download_paper_pdf
from src.tools.pdf_parse import extract_pdf_text
from src.tools.review import review_paper
from src.tools.storage import paper_exists, save_metadata, save_parsed_text, save_result
from src.tools.summarize import summarize_paper


@dataclass(slots=True)
class ToolOrchestratedAgent:
    """固定流程的轻量 Agent 包装器。"""

    settings: Settings
    tools: list[Any]

    def invoke(self, query: str, max_results: int = 3, skip_existing: bool = True) -> dict[str, Any]:
        """接收用户输入并执行固定流程。"""
        return run_pipeline(
            query=query,
            settings=self.settings,
            max_results=max_results,
            skip_existing=skip_existing,
        )


def build_agent(settings: Settings) -> ToolOrchestratedAgent:
    """构建工具编排型 Agent。

    这里不做复杂的自主决策，只做三件事：
    1. 注册工具
    2. 接收用户输入
    3. 按固定流程调用工具
    """

    @tool("arxiv_search")
    def arxiv_search_tool(query: str, max_results: int = 5) -> str:
        """检索 arXiv 论文列表。"""
        papers = search_arxiv(query=query, settings=settings, max_results=max_results)
        return f"找到 {len(papers)} 篇论文。"

    @tool("paper_download")
    def paper_download_tool(arxiv_id: str) -> str:
        """下载指定论文 PDF。"""
        return f"下载工具已注册，后续将根据 arXiv ID={arxiv_id} 下载 PDF。"

    @tool("pdf_parse")
    def pdf_parse_tool(arxiv_id: str) -> str:
        """解析指定论文 PDF 文本。"""
        return f"解析工具已注册，后续将处理 arXiv ID={arxiv_id}。"

    @tool("summarize")
    def summarize_tool(arxiv_id: str) -> str:
        """生成论文结构化总结。"""
        return f"总结工具已注册，后续将处理 arXiv ID={arxiv_id}。"

    @tool("review")
    def review_tool(arxiv_id: str) -> str:
        """生成审稿式评价。"""
        return f"评审工具已注册，后续将处理 arXiv ID={arxiv_id}。"

    @tool("storage")
    def storage_tool(arxiv_id: str) -> str:
        """保存论文及结果到本地。"""
        return f"存储工具已注册，后续将处理 arXiv ID={arxiv_id}。"

    registered_tools = [
        arxiv_search_tool,
        paper_download_tool,
        pdf_parse_tool,
        summarize_tool,
        review_tool,
        storage_tool,
    ]

    _ = (
        download_paper_pdf,
        extract_pdf_text,
        summarize_paper,
        review_paper,
        save_metadata,
        save_parsed_text,
        save_result,
        paper_exists,
    )

    return ToolOrchestratedAgent(settings=settings, tools=registered_tools)
