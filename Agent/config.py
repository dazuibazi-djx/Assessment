"""项目配置模块。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    """集中管理项目运行时配置。"""

    project_root: Path
    data_dir: Path
    pdf_dir: Path
    meta_dir: Path
    parsed_dir: Path
    results_dir: Path
    prompts_dir: Path
    examples_dir: Path
    arxiv_base_url: str
    openai_api_key: str | None
    model_name: str
    request_timeout: int


def load_config() -> Settings:
    """加载项目基础配置。

   仅仅负责提供默认路径和基础参数，后续再接入 `.env`。
    """
    project_root = Path(__file__).resolve().parent
    data_dir = project_root / "data"
    return Settings(
        project_root=project_root,
        data_dir=data_dir,
        pdf_dir=data_dir / "pdf",
        meta_dir=data_dir / "meta",
        parsed_dir=data_dir / "parsed",
        results_dir=data_dir / "results",
        prompts_dir=project_root / "prompts",
        examples_dir=project_root / "examples",
        arxiv_base_url=os.getenv("ARXIV_BASE_URL", "http://export.arxiv.org/api/query"),
        openai_api_key=os.getenv("sk-45e45dd391b040ddb1e2f17df46b13dd"),
        model_name=os.getenv("MODEL_NAME", "deepseek-chat"),
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "60")),
    )
