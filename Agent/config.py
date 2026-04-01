"""项目配置模块。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    """配置异常。"""


@dataclass(slots=True)
class Settings:
    """集中管理项目运行时配置。"""

    openai_api_key: str
    model_name: str
    openai_base_url: str | None
    data_dir: Path
    pdf_dir: Path
    meta_dir: Path
    parsed_dir: Path
    results_dir: Path

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "Settings":
        """从环境变量和 `.env` 文件中构建配置。"""
        project_root = Path(__file__).resolve().parent
        dotenv_path = env_file or (project_root / ".env")
        load_dotenv(dotenv_path=dotenv_path, override=False)

        data_dir = _resolve_path(os.getenv("DATA_DIR", "data"), project_root)
        pdf_dir = _resolve_path(os.getenv("PDF_DIR", str(data_dir / "pdf")), project_root)
        meta_dir = _resolve_path(os.getenv("META_DIR", str(data_dir / "meta")), project_root)
        results_dir = _resolve_path(os.getenv("RESULTS_DIR", str(data_dir / "results")), project_root)

        settings = cls(
            openai_api_key=_read_required_env("OPENAI_API_KEY"),
            model_name=_read_required_env("MODEL_NAME"),
            openai_base_url=_read_optional_env("OPENAI_BASE_URL"),
            data_dir=data_dir,
            pdf_dir=pdf_dir,
            meta_dir=meta_dir,
            parsed_dir=(data_dir / "parsed").resolve(strict=False),
            results_dir=results_dir,
        )
        settings.ensure_directories()
        return settings

    def ensure_directories(self) -> None:
        """确保数据目录存在。"""
        for directory in (self.data_dir, self.pdf_dir, self.meta_dir, self.parsed_dir, self.results_dir):
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise ConfigError(f"无法创建目录: {directory}") from exc


def load_config() -> Settings:
    """加载项目配置。"""
    return Settings.from_env()


def _read_required_env(name: str) -> str:
    """读取必填环境变量。"""
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(
            f"缺少必要配置项 `{name}`。"
            "请在系统环境变量或项目根目录 `.env` 文件中设置该值。"
        )
    return value


def _read_optional_env(name: str) -> str | None:
    """读取可选环境变量。"""
    value = os.getenv(name, "").strip()
    return value or None


def _resolve_path(raw_value: str, project_root: Path) -> Path:
    """将环境变量中的路径解析为绝对路径。"""
    candidate = Path(raw_value).expanduser()
    if not candidate.is_absolute():
        candidate = project_root / candidate

    try:
        return candidate.resolve(strict=False)
    except OSError as exc:
        raise ConfigError(f"无效的路径配置: {raw_value}") from exc
