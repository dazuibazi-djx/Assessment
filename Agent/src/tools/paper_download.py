from __future__ import annotations
from pathlib import Path

import httpx
from langchain.tools import tool

from config import load_config


class PaperDownloadError(RuntimeError):
    """PDF 下载异常。"""


def download_paper_pdf(
    arxiv_id: str,
    pdf_url: str,
    skip_existing: bool = True,
    pdf_dir: str | Path | None = None,
    timeout: float = 60.0,
) -> Path:
    cleaned_arxiv_id = arxiv_id.strip()
    cleaned_pdf_url = pdf_url.strip()

    if not cleaned_arxiv_id:
        raise ValueError("arxiv_id 不能为空。")

    if not cleaned_pdf_url:
        raise ValueError("pdf_url 不能为空。")

    resolved_pdf_dir = _resolve_pdf_dir(pdf_dir)
    resolved_pdf_dir.mkdir(parents=True, exist_ok=True)
    target_path = resolved_pdf_dir / f"{cleaned_arxiv_id}.pdf"

    if skip_existing and target_path.exists():
        return target_path

    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "research-assistant-agent/0.1"},
        ) as client:
            response = client.get(cleaned_pdf_url)
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise PaperDownloadError(f"下载超时: {cleaned_pdf_url}") from exc
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        raise PaperDownloadError(f"下载失败，HTTP 状态码 {status_code}: {cleaned_pdf_url}") from exc
    except httpx.HTTPError as exc:
        raise PaperDownloadError(f"网络异常，无法下载 PDF: {cleaned_pdf_url}") from exc


    if not response.content.startswith(b"%PDF"):
        raise PaperDownloadError(f"下载内容不是合法的 PDF 文件: {cleaned_pdf_url}")

    try:
        target_path.write_bytes(response.content)
    except OSError as exc:
        raise PaperDownloadError(f"无法写入本地 PDF 文件: {target_path}") from exc

    return target_path


@tool("paper_download")
def paper_download_tool(arxiv_id: str, pdf_url: str, skip_existing: bool = True) -> str:
    """LangChain tool: 下载论文 PDF 到本地。"""
    local_path = download_paper_pdf(
        arxiv_id=arxiv_id,
        pdf_url=pdf_url,
        skip_existing=skip_existing,
    )
    return str(local_path)


def _resolve_pdf_dir(pdf_dir: str | Path | None) -> Path:
    if pdf_dir is None:
        return load_config().pdf_dir

    candidate = Path(pdf_dir).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    return candidate.resolve(strict=False)
