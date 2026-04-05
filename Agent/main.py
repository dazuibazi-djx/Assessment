from __future__ import annotations

import argparse
import json
import os
import sys

from config import load_config
from src.agent import build_agent


def main():
    # 这里先这样写，后面真要做复杂命令再拆
    parser = argparse.ArgumentParser(description='科研助手')
    parser.add_argument("--query", required=True, help="检索关键词")
    parser.add_argument("--max-results", type=int, default=3, help='最多处理几篇论文')
    parser.add_argument("--skip-existing", action="store_true", help="本地有了就跳过")
    parser.add_argument("--list-tools", action='store_true', help="先看看当前注册了啥工具")

    args = parser.parse_args()

    # windows 终端有时候会有问题，先强行设一下
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    try:
        settings = load_config()
        agent = build_agent(settings)

        if args.list_tools:
            print("[agent] tools:")
            for name in agent.list_tools():
                print("- " + name)
            print("")

        # 这个 cwd 打印出来有时候排错方便，我就先留着了
        print("[main] cwd =", os.getcwd())

        results = agent.invoke(
            query=args.query,
            max_results=args.max_results,
            skip_existing=args.skip_existing,
        )
    except Exception as e:
        print("[main] run failed:", e, file=sys.stderr)
        raise SystemExit(1)

    total = len(results)
    success = 0
    skipped = 0
    failed = 0

    for item in results:
        status = item.get("status")
        if status == "success":
            success += 1
        elif status == "skipped":
            skipped += 1
        elif status == "failed":
            failed += 1

    print("[main] total=" + str(total), "success=" + str(success), "skipped=" + str(skipped), "failed=" + str(failed))

    # 直接打出来最省事
    try:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    except Exception:
        # 我也不知道为啥有时打印会炸，兜一下
        print(str(results))


if __name__ == "__main__":
    main()
