"""
⚠️ 已弃用 (deprecated)

历史说明：早期版本用 ``schedule`` 库 + while True 做 in-process 调度。
问题：进程崩溃即丢任务；无法跨重启恢复；与 setup_tasks.bat 双重调度冲突。
v2.0 起统一由操作系统调度（Windows 任务计划 / Linux cron），
通过以下命令单次执行：

    python -m ai_news_collector.main news
    python -m ai_news_collector.main rankings
    python -m ai_news_collector.main backup
    python -m ai_news_collector.main cleanup

本文件保留仅作为兼容壳，运行 --daemon 时直接报错并提示。
"""
from __future__ import annotations

import argparse
import logging
import sys

logger = logging.getLogger("task_scheduler")


def main() -> int:
    parser = argparse.ArgumentParser(description="[DEPRECATED] in-process scheduler 已弃用")
    parser.add_argument("--daemon", action="store_true", help="保留兼容，但已禁用")
    args = parser.parse_args()

    print(
        "ERROR: in-process scheduler 已弃用。\n"
        "请改用操作系统级调度：\n"
        "  Windows: 运行 setup_tasks.bat 注册任务计划\n"
        "  Linux:   在 crontab 里执行 python -m ai_news_collector.main news 等\n",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
