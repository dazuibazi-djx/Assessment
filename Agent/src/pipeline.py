"""论文处理主流程。"""
"""论文处理主线。"""

from __future__ import annotations

from typing import Any

from config import Settings, load_config
from config import Settings, load_config
from src.schemas import PaperContent, PaperResult
from src.tools.arxiv_search import search_arxiv
from src.tools.paper_download import download_paper_pdf
from src.tools.pdf_parse import extract_pdf_text
from src.tools.review import review_paper
from src.tools.storage import ensure_storage_dirs, paper_exists, save_metadata, save_parsed_text, save_result
from src.tools.storage import ensure_storage_dirs, paper_exists, save_metadata, save_parsed_text, save_result
from src.tools.summarize import summarize_paper


STEPS = [
    "search",
    "save metadata",
    "download pdf",
    "parse pdf",
    "summarize",
    "analyze",
    "review",
    "save final result",
]
PIPELINE_STEPS = [
    "search",
    "save metadata",
    "download pdf",
    "parse pdf",
    "summarize",
    "analyze",
    "review",
    "save final result",
]


def run_pipeline(
    query: str,
    max_results: int = 5,
    settings: Settings | None = None,
    skip_existing: bool = True,
) -> list[dict[str, Any]]:
    if not query.strip():
        raise ValueError("query 不能为空。")
    if max_results <= 0:
        raise ValueError("max_results 必须大于 0。")

    settings = settings or load_config()
    max_results: int = 5,
    settings: Settings | None = None,
    skip_existing: bool = True,
) -> list[dict[str, Any]]:
    """执行固定流程的论文处理任务。"""
    if not query.strip():
        raise ValueError("query 不能为空。")
    if max_results <= 0:
        raise ValueError("max_results 必须大于 0。")

    settings = settings or load_config()
    ensure_storage_dirs(settings)

    print(f"[pipeline] query={query!r}, max_results={max_results}")
    print(f"[pipeline] steps: {' -> '.join(STEPS)}")

    papers = search_arxiv(query=query, max_results=max_results)
    print(f"[search] found {len(papers)} papers")

    results: list[dict[str, Any]] = []

    for index, paper in enumerate(papers, start=1):
        arxiv_id = str(paper.get("arxiv_id", "")).strip()
        title = str(paper.get("title", "")).strip()
        prefix = f"[paper {index}/{len(papers)}]"

        print(f"{prefix} {arxiv_id or 'unknown'} | {title or 'untitled'}")

        if not arxiv_id:
            print(f"{prefix} missing arxiv_id")
            results.append(
                {
                    "status": "failed",
                    "step": "search",
                    "error": "missing arxiv_id",
                    "metadata": paper,
    print(f"[pipeline] query={query!r}, max_results={max_results}")
    print(f"[pipeline] steps: {' -> '.join(PIPELINE_STEPS)}")

    papers = search_arxiv(query=query, max_results=max_results)
    print(f"[search] 找到 {len(papers)} 篇论文")

    results: list[dict[str, Any]] = []

    for index, paper in enumerate(papers, start=1):
        arxiv_id = str(paper.get("arxiv_id", "")).strip()
        title = str(paper.get("title", "")).strip()
        print(f"[paper {index}/{len(papers)}] 开始处理: {arxiv_id or 'unknown'} | {title or 'untitled'}")

        if not arxiv_id:
            print(f"[paper {index}/{len(papers)}] 缺少 arxiv_id，跳过")
            results.append(
                {
                    "status": "failed",
                    "step": "search",
                    "error": "缺少 arxiv_id",
                    "metadata": paper,
                }
            )
            continue

        try:
            if skip_existing and paper_exists(arxiv_id, settings):
                print(f"{prefix} skipped")
                results.append(
                    {
                        "status": "skipped",
                        "metadata": paper,
                        "reason": "already exists",
                    }
                )
                continue

            print(f"{prefix} save metadata")
            meta_path = save_metadata(paper, settings)

            print(f"{prefix} download")
            pdf_path = download_paper_pdf(
                arxiv_id=arxiv_id,
                pdf_url=str(paper.get("pdf_url", "")).strip(),
                skip_existing=skip_existing,
                pdf_dir=settings.pdf_dir,
            )

            print(f"{prefix} parse")
            parsed_text = extract_pdf_text(pdf_path, pages=5)
            if parsed_text.startswith("PDF 解析失败"):
                raise RuntimeError(parsed_text)

            text_path = save_parsed_text(arxiv_id, parsed_text, settings)

            print(f"{prefix} summarize")
            summary_result = summarize_paper(
                title=title,
                abstract=str(paper.get("abstract", "")).strip(),
                paper_text=parsed_text,
                settings=settings,
            )

            print(f"{prefix} review")
            review = review_paper(
                title=title,
                abstract=str(paper.get("abstract", "")).strip(),
                paper_text=parsed_text,
                settings=settings,
            )

            payload = PaperResult(
                metadata=paper,
                content=PaperContent(
                    arxiv_id=arxiv_id,
                    pdf_path=pdf_path,
                    text_path=text_path,
                    extracted_text=parsed_text,
                ),
                summary=summary_result["summary"],
                analysis=summary_result["analysis"],
                review=review,
            ).model_dump(mode="json")

            print(f"{prefix} save result")
            result_path = save_result(payload, settings)

            payload["status"] = "success"
            payload["meta_path"] = str(meta_path)
            payload["result_path"] = str(result_path)
            results.append(payload)
            print(f"{prefix} done")

        except Exception as exc:  # noqa: BLE001
            print(f"{prefix} failed: {exc}")
            results.append(
                {
                    "status": "failed",
                    "step": "pipeline",
                    "error": str(exc),
                    "metadata": paper,
                }
            )

    print(f"[pipeline] done: {len(results)} records")
    return results
        try:
            if skip_existing and paper_exists(arxiv_id, settings):
                print(f"[paper {index}/{len(papers)}] 本地已存在元数据，跳过重复处理")
                results.append(
                    {
                        "status": "skipped",
                        "metadata": paper,
                        "reason": "already exists",
                    }
                )
                continue

            print(f"[paper {index}/{len(papers)}] 保存元数据")
            meta_path = save_metadata(paper, settings)

            print(f"[paper {index}/{len(papers)}] 下载 PDF")
            pdf_path = download_paper_pdf(
                arxiv_id=arxiv_id,
                pdf_url=str(paper.get('pdf_url', '')).strip(),
                skip_existing=skip_existing,
                pdf_dir=settings.pdf_dir,
            )

            print(f"[paper {index}/{len(papers)}] 解析 PDF")
            parsed_text = extract_pdf_text(pdf_path, pages=5)
            if parsed_text.startswith("PDF 解析失败："):
                raise RuntimeError(parsed_text)

            text_path = save_parsed_text(arxiv_id, parsed_text, settings)

            print(f"[paper {index}/{len(papers)}] 生成总结")
            summary_and_analysis = summarize_paper(
                title=title,
                abstract=str(paper.get("abstract", "")).strip(),
                paper_text=parsed_text,
                settings=settings,
            )
            summary = summary_and_analysis["summary"]

            print(f"[paper {index}/{len(papers)}] 生成分析")
            analysis = summary_and_analysis["analysis"]

            print(f"[paper {index}/{len(papers)}] 生成审稿结果")
            review = review_paper(
                title=title,
                abstract=str(paper.get("abstract", "")).strip(),
                paper_text=parsed_text,
                settings=settings,
            )

            final_result = PaperResult(
                metadata=paper,
                content=PaperContent(
                    arxiv_id=arxiv_id,
                    pdf_path=pdf_path,
                    text_path=text_path,
                    extracted_text=parsed_text,
                ),
                summary=summary,
                analysis=analysis,
                review=review,
            ).model_dump(mode="json")

            print(f"[paper {index}/{len(papers)}] 保存最终结果")
            result_path = save_result(final_result, settings)

            final_result["status"] = "success"
            final_result["meta_path"] = str(meta_path)
            final_result["result_path"] = str(result_path)
            results.append(final_result)
            print(f"[paper {index}/{len(papers)}] 完成")

        except Exception as exc:  # noqa: BLE001
            print(f"[paper {index}/{len(papers)}] 失败: {exc}")
            results.append(
                {
                    "status": "failed",
                    "step": "pipeline",
                    "error": str(exc),
                    "metadata": paper,
                }
            )

    print(f"[pipeline] 结束。成功/跳过/失败共 {len(results)} 条记录")
    return results
