"""本地存储工具。"""

from __future__ import annotations

import json
from pathlib import Path

from config import Settings
from src.schemas import PaperMetadata, PaperResult


def ensure_storage_dirs(settings: Settings) -> None:
    """确保项目所需的数据目录存在。"""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.pdf_dir.mkdir(parents=True, exist_ok=True)
    settings.meta_dir.mkdir(parents=True, exist_ok=True)
    settings.parsed_dir.mkdir(parents=True, exist_ok=True)
    settings.results_dir.mkdir(parents=True, exist_ok=True)


def paper_exists(arxiv_id: str, settings: Settings) -> bool:
    """检查论文是否已在本地保存过元数据。
    当前用 meta 文件判断是否已存在，后续也可以改成数据库去重。
    """
    return build_meta_path(arxiv_id, settings).exists()


def build_pdf_path(arxiv_id: str, settings: Settings) -> Path:
    """基于 arXiv ID 生成 PDF 文件路径。"""
    return settings.pdf_dir / f"{arxiv_id}.pdf"


def build_meta_path(arxiv_id: str, settings: Settings) -> Path:
    """基于 arXiv ID 生成元数据文件路径。"""
    return settings.meta_dir / f"{arxiv_id}.json"


def build_parsed_path(arxiv_id: str, settings: Settings) -> Path:
    """基于 arXiv ID 生成解析文本路径。"""
    return settings.parsed_dir / f"{arxiv_id}.txt"


def build_result_path(arxiv_id: str, settings: Settings) -> Path:
    """基于 arXiv ID 生成处理结果路径。"""
    return settings.results_dir / f"{arxiv_id}.json"


def save_metadata(paper: PaperMetadata, settings: Settings) -> Path:
    """保存论文元数据。"""
    ensure_storage_dirs(settings)
    target_path = build_meta_path(paper.arxiv_id, settings)
    target_path.write_text(paper.model_dump_json(indent=2), encoding="utf-8")
    return target_path


def save_parsed_text(arxiv_id: str, parsed_text: str, settings: Settings) -> Path:
    """保存解析后的正文文本。"""
    ensure_storage_dirs(settings)
    target_path = build_parsed_path(arxiv_id, settings)
    target_path.write_text(parsed_text, encoding="utf-8")
    return target_path


def save_result(result: PaperResult, settings: Settings) -> Path:
    """保存论文处理结果。

    当前使用 JSON 文件保存，后续可以再扩展 SQLite。
    """
    ensure_storage_dirs(settings)
    target_path = build_result_path(result.metadata.arxiv_id, settings)
    payload = result.model_dump(mode="json")
    target_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target_path
