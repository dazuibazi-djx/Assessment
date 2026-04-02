"""命令行入口。"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from config import ConfigError, load_config
from src.agent import build_agent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="科研助手")
    parser.add_argument("--query", required=True, help="检索关键词。")
    parser.add_argument("--max-results", type=int, default=3, help="最多处理多少篇论文。")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="如果本地已存在对应论文，则跳过。",
    )
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="输出当前已注册的工具。",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    _configure_stdout()

    try:
        agent = build_agent(load_config())

        if args.list_tools:
            print("[agent] tools:")
            for name in agent.list_tools():
                print(f"- {name}")

        results = agent.invoke(
            query=args.query,
            max_results=args.max_results,
            skip_existing=args.skip_existing,
        )
    except (ConfigError, ValueError, RuntimeError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    _print_summary(results)
    print(json.dumps(results, ensure_ascii=False, indent=2))


def _print_summary(results: list[dict[str, Any]]) -> None:
    success_count = sum(1 for item in results if item.get("status") == "success")
    skipped_count = sum(1 for item in results if item.get("status") == "skipped")
    failed_count = sum(1 for item in results if item.get("status") == "failed")
    print(
        "[main] "
        f"total={len(results)} "
        f"success={success_count} "
        f"skipped={skipped_count} "
        f"failed={failed_count}"
    )


def _configure_stdout() -> None:
    if not hasattr(sys.stdout, "reconfigure"):
        return

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


if __name__ == "__main__":
    main()
