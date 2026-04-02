"""论文审稿式评价。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from langchain.tools import tool
from langchain_openai import ChatOpenAI

from config import Settings, load_config
from src.schemas import PaperReview


DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com"
TEXT_LIMIT = 12000


class ReviewError(RuntimeError):
    """审稿生成异常。"""


def review_paper(
    title: str,
    abstract: str,
    paper_text: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    title = title.strip()
    abstract = abstract.strip()
    paper_text = _trim_text(paper_text)
    settings = settings or load_config()

    if not title:
        raise ValueError("title 不能为空。")
    if not abstract and not paper_text:
        raise ValueError("abstract 和 paper_text 不能同时为空。")

    llm = _build_llm(settings)
    system_prompt = _read_prompt("system_prompt.txt", required=False)
    review_prompt = _read_prompt("review_prompt.txt", required=True)

    raw_text = _call_model(
        llm=llm,
        system_prompt=system_prompt,
        review_prompt=review_prompt,
        title=title,
        abstract=abstract,
        paper_text=paper_text,
    )
    return _parse_review(raw_text)


@tool("review_paper")
def review_paper_tool(title: str, abstract: str, paper_text: str) -> dict[str, Any]:
    """生成论文审稿结果。"""
    return review_paper(title=title, abstract=abstract, paper_text=paper_text)


def _build_llm(settings: Settings) -> ChatOpenAI:
    base_url = settings.openai_base_url
    if not base_url and "deepseek" in settings.model_name.lower():
        base_url = DEEPSEEK_DEFAULT_BASE_URL

    kwargs: dict[str, Any] = {
        "api_key": settings.openai_api_key,
        "model": settings.model_name,
        "temperature": 0.1,
        "timeout": 60,
        "max_retries": 2,
    }
    if base_url:
        kwargs["base_url"] = base_url

    return ChatOpenAI(**kwargs)


def _read_prompt(filename: str, required: bool) -> str:
    path = Path(__file__).resolve().parents[2] / "prompts" / filename
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        if required:
            raise ReviewError(f"无法读取 prompt 文件: {path}") from exc
        return ""


def _call_model(
    llm: ChatOpenAI,
    system_prompt: str,
    review_prompt: str,
    title: str,
    abstract: str,
    paper_text: str,
) -> str:
    prompt = "\n\n".join(part.strip() for part in (system_prompt, review_prompt) if part.strip())
    payload = (
        f"title:\n{title}\n\n"
        f"abstract:\n{abstract or '论文未提供摘要'}\n\n"
        f"content:\n{paper_text or '正文为空，请仅基于摘要谨慎审稿。'}"
    )

    try:
        response = llm.invoke([("system", prompt), ("human", payload)])
    except Exception as exc:  # noqa: BLE001
        raise ReviewError(f"模型调用失败: {exc}") from exc

    return _stringify_response(response)


def _stringify_response(response: Any) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
            else:
                text = getattr(item, "text", None)
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()
    return str(content).strip()


def _trim_text(text: str, limit: int = TEXT_LIMIT) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit]


def _parse_review(raw_text: str) -> dict[str, Any]:
    data = _extract_json(raw_text)
    if not isinstance(data, dict):
        data = {}

    review = PaperReview()
    payload = review.model_dump()

    payload["summary"] = _text(data.get("summary"), payload["summary"])
    payload["strengths"] = _text_list(data.get("strengths"))
    payload["weaknesses"] = _text_list(data.get("weaknesses"))
    payload["score"] = _score(data.get("overall_score", data.get("score")), payload["score"])
    payload["confidence"] = _score(
        data.get("confidence_score", data.get("confidence")),
        payload["confidence"],
    )
    payload["recommendation"] = _text(
        data.get("verdict", data.get("recommendation")),
        payload["recommendation"],
    )
    payload["novelty_score"] = _score(data.get("novelty_score"), payload["novelty_score"])
    payload["technical_quality_score"] = _score(
        data.get("technical_quality_score"),
        payload["technical_quality_score"],
    )
    payload["clarity_score"] = _score(data.get("clarity_score"), payload["clarity_score"])
    payload["main_reasons"] = _text_list(data.get("main_reasons"))
    payload["suggestions"] = _text_list(data.get("suggestions"))
    return payload


def _extract_json(raw_text: str) -> Any:
    text = raw_text.strip()
    if not text:
        return {}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return {}


def _text(value: Any, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _text_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _score(value: Any, default: float) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(10.0, score))
