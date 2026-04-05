"""本地存储工具。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain.tools import tool

from config import Settings, load_config
from src.schemas import PaperMetadata, PaperResult


class StorageError(RuntimeError):
    """本地存储异常。"""


def ensure_storage_dirs(settings: Settings) -> None:

    for directory in (
        settings.data_dir,
        settings.pdf_dir,
        settings.meta_dir,
        settings.parsed_dir,
        settings.results_dir,
    ):
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(f"无法创建目录: {directory}") from exc


def paper_exists(arxiv_id: str, settings: Settings) -> bool:
    return build_meta_path(arxiv_id, settings).exists()


def build_pdf_path(arxiv_id: str, settings: Settings) -> Path:
    return settings.pdf_dir / f"{arxiv_id}.pdf"


def build_meta_path(arxiv_id: str, settings: Settings) -> Path:
    return settings.meta_dir / f"{arxiv_id}.json"


def build_parsed_path(arxiv_id: str, settings: Settings) -> Path:
    return settings.parsed_dir / f"{arxiv_id}.txt"


def build_result_path(arxiv_id: str, settings: Settings) -> Path:
    return settings.results_dir / f"{arxiv_id}.json"


def save_metadata(paper: PaperMetadata | dict[str, Any], settings: Settings) -> Path:
    ensure_storage_dirs(settings)
    metadata = _coerce_metadata(paper)
    target_path = build_meta_path(metadata.arxiv_id, settings)
    _write_json(target_path, metadata.model_dump(mode="json"))
    return target_path


def save_parsed_text(arxiv_id: str, parsed_text: str, settings: Settings) -> Path:
    ensure_storage_dirs(settings)
    target_path = build_parsed_path(arxiv_id, settings)
    try:
        target_path.write_text(parsed_text, encoding="utf-8")
    except OSError as exc:
        raise StorageError(f"无法写入解析文本文件: {target_path}") from exc
    return target_path


def save_result(result: PaperResult | dict[str, Any], settings: Settings) -> Path:
    ensure_storage_dirs(settings)
    paper_result = _coerce_result(result)
    target_path = build_result_path(paper_result.metadata.arxiv_id, settings)
    _write_json(target_path, paper_result.model_dump(mode="json"))
    return target_path


@tool("save_metadata")
def save_metadata_tool(metadata: dict[str, Any]) -> str:
    """LangChain tool: 保存论文元数据到本地。"""
    settings = load_config()
    saved_path = save_metadata(metadata, settings)
    return str(saved_path)


@tool("save_result")
def save_result_tool(result: dict[str, Any]) -> str:
    """LangChain tool: 保存最终分析结果到本地。"""
    settings = load_config()
    saved_path = save_result(result, settings)
    return str(saved_path)


def _coerce_metadata(paper: PaperMetadata | dict[str, Any]) -> PaperMetadata:
    try:
        if isinstance(paper, PaperMetadata):
            return paper
        return PaperMetadata.model_validate(paper)
    except Exception as exc: 
        raise StorageError(f"元数据格式不正确，无法保存: {exc}") from exc


def _coerce_result(result: PaperResult | dict[str, Any]) -> PaperResult:
    try:
        if isinstance(result, PaperResult):
            return result
        return PaperResult.model_validate(result)
    except Exception as exc: 
        raise StorageError(f"最终结果格式不正确，无法保存: {exc}") from exc


def _write_json(target_path: Path, payload: dict[str, Any]) -> None:
    try:
        target_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise StorageError(f"无法写入 JSON 文件: {target_path}") from exc
