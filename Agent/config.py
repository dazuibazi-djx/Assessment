from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    pass


@dataclass(slots=True)
class Settings:
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
        # 默认就按当前项目根目录找 .env
        root = Path(__file__).resolve().parent
        dotenv_path = env_file or (root / ".env")
        load_dotenv(dotenv_path=dotenv_path, override=False)

        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        model_name = os.getenv("MODEL_NAME", "").strip()
        openai_base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None

        if not openai_api_key:
            raise ConfigError("缺少配置项 `OPENAI_API_KEY`，请在 .env 中设置。")
        if not model_name:
            raise ConfigError("缺少配置项 `MODEL_NAME`，请在 .env 中设置。")

        # 这里故意不拆太细，项目里看着直观点
        data_raw = os.getenv("DATA_DIR", "data").strip() or "data"
        if os.path.isabs(data_raw):
            data_dir = Path(data_raw)
        else:
            data_dir = Path(os.path.join(root, data_raw))

        pdf_raw = os.getenv("PDF_DIR", "").strip()
        if pdf_raw:
            if os.path.isabs(pdf_raw):
                pdf_dir = Path(pdf_raw)
            else:
                pdf_dir = Path(os.path.join(root, pdf_raw))
        else:
            pdf_dir = data_dir / "pdf"

        meta_raw = os.getenv("META_DIR", "").strip()
        if meta_raw:
            if os.path.isabs(meta_raw):
                meta_dir = Path(meta_raw)
            else:
                meta_dir = Path(os.path.join(root, meta_raw))
        else:
            meta_dir = data_dir / "meta"

        results_raw = os.getenv("RESULTS_DIR", "").strip()
        if results_raw:
            if os.path.isabs(results_raw):
                results_dir = Path(results_raw)
            else:
                results_dir = Path(os.path.join(root, results_raw))
        else:
            results_dir = data_dir / "results"

        parsed_dir = data_dir / "parsed"

        # resolve 一下，免得后面路径奇奇怪怪
        try:
            data_dir = data_dir.resolve(strict=False)
            pdf_dir = pdf_dir.resolve(strict=False)
            meta_dir = meta_dir.resolve(strict=False)
            parsed_dir = parsed_dir.resolve(strict=False)
            results_dir = results_dir.resolve(strict=False)
        except OSError as exc:
            raise ConfigError("路径配置有问题，请检查 DATA_DIR / PDF_DIR / META_DIR / RESULTS_DIR。") from exc

        settings = cls(
            openai_api_key=openai_api_key,
            model_name=model_name,
            openai_base_url=openai_base_url,
            data_dir=data_dir,
            pdf_dir=pdf_dir,
            meta_dir=meta_dir,
            parsed_dir=parsed_dir,
            results_dir=results_dir,
        )
        settings.ensure_directories()
        return settings

    def ensure_directories(self) -> None:
        # 这些目录反正都要用到，启动时顺手建掉
        for path in [self.data_dir, self.pdf_dir, self.meta_dir, self.parsed_dir, self.results_dir]:
            try:
                os.makedirs(path, exist_ok=True)
            except OSError as exc:
                raise ConfigError(f"无法创建目录: {path}") from exc


def load_config() -> Settings:
    return Settings.from_env()
