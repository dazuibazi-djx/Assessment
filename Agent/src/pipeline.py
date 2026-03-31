"""固定流程的论文处理主线。"""

from __future__ import annotations

from typing import Any

from config import Settings
from src.schemas import PaperContent, PaperResult
from src.tools.arxiv_search import search_arxiv
from src.tools.paper_download import download_paper_pdf
from src.tools.pdf_parse import extract_pdf_text
from src.tools.review import review_paper
from src.tools.storage import (
    ensure_storage_dirs,
    paper_exists,
    save_metadata,
    save_parsed_text,
    save_result,
)
from src.tools.summarize import summarize_paper


PIPELINE_STEPS = ["search", "download", "parse", "summarize", "review", "save"]


def run_pipeline(
    query: str,
    settings: Settings,
    max_results: int = 3,
    skip_existing: bool = False,
) -> dict[str, Any]:
    """执行固定流程的论文处理链路。

    固定流程：
    search -> download -> parse -> summarize -> review -> save
    """
    ensure_storage_dirs(settings)

    try:
        papers = search_arxiv(query=query, settings=settings, max_results=max_results)
    except NotImplementedError:
        return {
            "mode": "pipeline-skeleton",
            "query": query,
            "pipeline": PIPELINE_STEPS,
            "message": "固定流程已经确定，但检索工具尚未实现。",
            "storage": {
                "pdf_dir": str(settings.pdf_dir),
                "meta_dir": str(settings.meta_dir),
                "parsed_dir": str(settings.parsed_dir),
                "results_dir": str(settings.results_dir),
            },
        }

    processed: list[dict[str, Any]] = []
    skipped: list[str] = []

    for paper in papers:
        if skip_existing and paper_exists(paper.arxiv_id, settings):
            skipped.append(paper.arxiv_id)
            continue

        save_metadata(paper, settings)

        try:
            pdf_path = download_paper_pdf(paper, settings)
            parsed_text = extract_pdf_text(pdf_path)
            text_path = save_parsed_text(paper.arxiv_id, parsed_text, settings)
            summary = summarize_paper(paper, parsed_text, settings)
            review = review_paper(paper, parsed_text, settings)
        except NotImplementedError:
            processed.append(
                {
                    "arxiv_id": paper.arxiv_id,
                    "status": "pending",
                    "message": "部分工具仍为占位实现，流程结构已固定。",
                }
            )
            continue

        result = PaperResult(
            metadata=paper,
            content=PaperContent(
                arxiv_id=paper.arxiv_id,
                pdf_path=pdf_path,
                text_path=text_path,
                extracted_text=parsed_text,
            ),
            summary=summary,
            review=review,
        )
        save_result(result, settings)
        processed.append(result.model_dump(mode="json"))

    return {
        "mode": "tool-orchestrated-agent",
        "query": query,
        "pipeline": PIPELINE_STEPS,
        "processed_count": len(processed),
        "skipped_count": len(skipped),
        "processed": processed,
        "skipped": skipped,
    }
