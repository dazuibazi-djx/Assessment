"""项目数据结构定义。"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class PaperMetadata(BaseModel):
    arxiv_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: str = ""
    published: str = ""
    updated: str = ""
    pdf_url: str = ""
    primary_category: str = ""
    source: str = "arXiv"


class PaperContent(BaseModel):

    arxiv_id: str
    pdf_path: Path | None = None
    text_path: Path | None = None
    extracted_text: str = ""


class PaperSummary(BaseModel):
    problem: str = "文中未明确说明"
    background: str = "文中未明确说明"
    method: str = "文中未明确说明"
    experiment: str = "文中未明确说明"
    results: str = "文中未明确说明"
    contribution: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class MethodAnalysis(BaseModel):

    strength: str = "文中未明确说明"
    weakness: str = "文中未明确说明"
    technical_rationality: str = "文中未明确说明"


class ExperimentAnalysis(BaseModel):

    adequacy: str = "文中未明确说明"
    missing_parts: list[str] = Field(default_factory=list)
    fairness: str = "文中未明确说明"


class ResultAnalysis(BaseModel):

    main_findings: str = "文中未明确说明"
    credibility: str = "文中未明确说明"
    generalization: str = "文中未明确说明"


class PaperAnalysis(BaseModel):

    research_value: str = "文中未明确说明"
    method_analysis: MethodAnalysis = Field(default_factory=MethodAnalysis)
    experiment_analysis: ExperimentAnalysis = Field(default_factory=ExperimentAnalysis)
    result_analysis: ResultAnalysis = Field(default_factory=ResultAnalysis)
    paper_positioning: str = "文中未明确说明"
    overall_analysis: str = "文中未明确说明"


class PaperReview(BaseModel):

    summary: str = "文中未明确说明"
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    score: float = 5.0
    confidence: float = 5.0
    recommendation: str = "borderline"
    novelty_score: float = 5.0
    technical_quality_score: float = 5.0
    clarity_score: float = 5.0
    main_reasons: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class PaperResult(BaseModel):

    metadata: PaperMetadata
    content: PaperContent | None = None
    summary: PaperSummary | None = None
    analysis: PaperAnalysis | None = None
    review: PaperReview | None = None
