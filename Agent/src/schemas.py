"""项目数据结构定义。"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class PaperMetadata(BaseModel):
    """论文基础元数据。"""

    arxiv_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: str = ""
    published: str = ""
    pdf_url: str = ""
    source: str = "arXiv"


class PaperContent(BaseModel):
    """论文文件路径与解析内容。"""

    arxiv_id: str
    pdf_path: Path | None = None
    text_path: Path | None = None
    extracted_text: str = ""


class PaperSummary(BaseModel):
    """论文结构化总结结果。"""

    arxiv_id: str
    summary: str = ""
    key_points: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class PaperReview(BaseModel):
    """论文审稿式评价结果。"""

    arxiv_id: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    score: float | None = None
    verdict: str = ""


class PaperResult(BaseModel):
    """单篇论文的完整处理结果。"""

    metadata: PaperMetadata
    content: PaperContent | None = None
    summary: PaperSummary | None = None
    review: PaperReview | None = None
