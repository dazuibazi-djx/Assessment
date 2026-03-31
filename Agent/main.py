"""项目命令行入口。"""

from __future__ import annotations

import argparse
import json

from config import load_config
from src.pipeline import run_pipeline

"""构建命令行参数解析器。"""
def build_parser() -> argparse.ArgumentParser:
    
    parser = argparse.ArgumentParser(
        description="科研助手 Agent"
    )
    parser.add_argument("--query", required=True, help="待检索的论文主题或关键词。")
    parser.add_argument("--max-results", type=int, default=3, help="最多处理多少篇论文。")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="如果本地已经存在同一 arXiv 论文，则跳过重复处理。",
    )
    return parser


def main() -> None:
    """程序主入口。"""
    parser = build_parser()
    args = parser.parse_args()
    settings = load_config()

    result = run_pipeline(
        query=args.query,
        settings=settings,
        max_results=args.max_results,
        skip_existing=args.skip_existing,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
