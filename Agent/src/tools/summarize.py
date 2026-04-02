"""论文总结与分析。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from langchain.tools import tool
from langchain_openai import ChatOpenAI

from config import Settings, load_config
from src.schemas import PaperAnalysis, PaperSummary


DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com"
TEXT_LIMIT = 12000


class SummarizeError(RuntimeError):
    """模型总结异常。"""


def summarize_paper(
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
    system_prompt = _read_prompt("system_prompt.txt")

    summary_text = _call_model(
        llm=llm,
        system_prompt=system_prompt,
        task_prompt=_read_prompt("summary_prompt.txt"),
        title=title,
        abstract=abstract,
        paper_text=paper_text,
    )
    analysis_text = _call_model(
        llm=llm,
        system_prompt=system_prompt,
        task_prompt=_read_prompt("analysis_prompt.txt"),
        title=title,
        abstract=abstract,
        paper_text=paper_text,
    )

    return {
        "summary": _parse_summary(summary_text),
        "analysis": _parse_analysis(analysis_text),
    }


@tool("summarize_paper")
def summarize_paper_tool(title: str, abstract: str, paper_text: str) -> dict[str, Any]:
    """生成论文总结和分析结果。"""
    return summarize_paper(title=title, abstract=abstract, paper_text=paper_text)


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


def _read_prompt(filename: str) -> str:
    path = Path(__file__).resolve().parents[2] / "prompts" / filename
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SummarizeError(f"无法读取 prompt 文件: {path}") from exc


def _call_model(
    llm: ChatOpenAI,
    system_prompt: str,
    task_prompt: str,
    title: str,
    abstract: str,
    paper_text: str,
) -> str:
    prompt = "\n\n".join(part.strip() for part in (system_prompt, task_prompt) if part.strip())
    payload = (
        f"title:\n{title}\n\n"
        f"abstract:\n{abstract or '论文未提供摘要'}\n\n"
        f"content:\n{paper_text or '正文为空，请仅基于摘要谨慎作答。'}"
    )

    try:
        response = llm.invoke([("system", prompt), ("human", payload)])
    except Exception as exc:  # noqa: BLE001
        raise SummarizeError(f"模型调用失败: {exc}") from exc

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


def _parse_summary(raw_text: str) -> dict[str, Any]:
    data = _extract_json(raw_text)
    if not isinstance(data, dict):
        data = {}

    summary = PaperSummary()
    payload = summary.model_dump()
    payload["problem"] = _text(data.get("problem"), payload["problem"])
    payload["background"] = _text(data.get("background"), payload["background"])
    payload["method"] = _text(data.get("method"), payload["method"])
    payload["experiment"] = _text(data.get("experiment"), payload["experiment"])
    payload["results"] = _text(data.get("results"), payload["results"])
    payload["contribution"] = _text_list(data.get("contribution"))
    payload["limitations"] = _text_list(data.get("limitations"))
    payload["keywords"] = _text_list(data.get("keywords"))
    return payload


def _parse_analysis(raw_text: str) -> dict[str, Any]:
    data = _extract_json(raw_text)
    if not isinstance(data, dict):
        data = {}

    analysis = PaperAnalysis()
    payload = analysis.model_dump()
    payload["research_value"] = _text(data.get("research_value"), payload["research_value"])

    method = data.get("method_analysis", {})
    if isinstance(method, dict):
        payload["method_analysis"]["strength"] = _text(
            method.get("strength"),
            payload["method_analysis"]["strength"],
        )
        payload["method_analysis"]["weakness"] = _text(
            method.get("weakness"),
            payload["method_analysis"]["weakness"],
        )
        payload["method_analysis"]["technical_rationality"] = _text(
            method.get("technical_rationality"),
            payload["method_analysis"]["technical_rationality"],
        )

    experiment = data.get("experiment_analysis", {})
    if isinstance(experiment, dict):
        payload["experiment_analysis"]["adequacy"] = _text(
            experiment.get("adequacy"),
            payload["experiment_analysis"]["adequacy"],
        )
        payload["experiment_analysis"]["missing_parts"] = _text_list(experiment.get("missing_parts"))
        payload["experiment_analysis"]["fairness"] = _text(
            experiment.get("fairness"),
            payload["experiment_analysis"]["fairness"],
        )

    result = data.get("result_analysis", {})
    if isinstance(result, dict):
        payload["result_analysis"]["main_findings"] = _text(
            result.get("main_findings"),
            payload["result_analysis"]["main_findings"],
        )
        payload["result_analysis"]["credibility"] = _text(
            result.get("credibility"),
            payload["result_analysis"]["credibility"],
        )
        payload["result_analysis"]["generalization"] = _text(
            result.get("generalization"),
            payload["result_analysis"]["generalization"],
        )

    payload["paper_positioning"] = _text(data.get("paper_positioning"), payload["paper_positioning"])
    payload["overall_analysis"] = _text(data.get("overall_analysis"), payload["overall_analysis"])
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
