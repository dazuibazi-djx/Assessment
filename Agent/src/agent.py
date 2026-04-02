"""Agent 封装"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain.tools import tool

from config import Settings, load_config
from src.pipeline import run_pipeline
from src.tools.arxiv_search import arxiv_search_tool
from src.tools.paper_download import paper_download_tool
from src.tools.pdf_parse import pdf_parse_tool
from src.tools.review import review_paper_tool
from src.tools.storage import save_metadata_tool, save_result_tool
from src.tools.summarize import summarize_paper_tool


@dataclass(slots=True)
class ToolOrchestratedAgent:
    settings: Settings
    tools: list[Any]
    entry_tool: Any

    def invoke(
        self,
        query: str,
        max_results: int = 3,
        skip_existing: bool = True,
    ) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValueError("query 不能为空。")

        return self.entry_tool.invoke(
            {
                "query": query,
                "max_results": max_results,
                "skip_existing": skip_existing,
            }
        )

    def list_tools(self) -> list[str]:
        return [item.name for item in self.tools]


def build_agent(settings: Settings | None = None) -> ToolOrchestratedAgent:
    settings = settings or load_config()

    @tool("run_research_pipeline")
    def run_research_pipeline(
        query: str,
        max_results: int = 3,
        skip_existing: bool = True,
    ) -> list[dict[str, Any]]:
        """执行固定流程。"""
        return run_pipeline(
            query=query,
            max_results=max_results,
            settings=settings,
            skip_existing=skip_existing,
        )

    tools = [
        arxiv_search_tool,
        paper_download_tool,
        pdf_parse_tool,
        summarize_paper_tool,
        review_paper_tool,
        save_metadata_tool,
        save_result_tool,
        run_research_pipeline,
    ]

    return ToolOrchestratedAgent(settings=settings, tools=tools, entry_tool=run_research_pipeline)
