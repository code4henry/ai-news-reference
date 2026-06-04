"""
AI 技术资讯收集和推送系统 - 主程序入口
====================================

设计要点：
1. 调度**完全交给操作系统**（Windows 任务计划 / Linux cron），不再 in-process while-loop。
   setup_tasks.bat 已经存在；本程序只暴露"单次执行"子命令。
2. 通过 ``python -m ai_news_collector.main <command>`` 运行，避免 sys.path hack。
3. 所有时间相关逻辑用 config.now()，强制走 Asia/Hong_Kong 时区。

子命令：
    news              收集今日（or --date YYYY-MM-DD）RSS 资讯
    rankings          收集 LLM 排行榜
    backup            打包 data/ 到 backup/
    cleanup           删除超过 storage.max_days 的旧数据
    send-test         测试 QQ 通知是否通畅
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# 允许以脚本方式运行：python main.py <cmd>
# 同时也支持 python -m ai_news_collector.main <cmd>
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ai_news_collector.config.settings import config
    from ai_news_collector.scripts.news_collector import NewsCollector
    from ai_news_collector.scripts.llm_ranking_collector import LLMRankingCollector
    from ai_news_collector.scripts.task_runner import (
        backup_data,
        cleanup_old_data,
    )
    from ai_news_collector.notifications.qq import build_notifier, format_news_summary
else:
    from .config.settings import config
    from .scripts.news_collector import NewsCollector
    from .scripts.llm_ranking_collector import LLMRankingCollector
    from .scripts.task_runner import backup_data, cleanup_old_data
    from .notifications.qq import build_notifier, format_news_summary


def _setup_root_logger() -> None:
    log_file = config.get_log_file()
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


def _parse_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise SystemExit(f"日期格式错误: {s}，应为 YYYY-MM-DD")


def cmd_news(args: argparse.Namespace) -> int:
    date = _parse_date(args.date)
    collector = NewsCollector()
    article_count = collector.collect_daily_news(date)
    print(f"[OK] 新闻收集完成，共 {article_count} 篇")
    return 0


def cmd_rankings(args: argparse.Namespace) -> int:
    date = _parse_date(args.date)
    collector = LLMRankingCollector()
    count = collector.collect_daily_rankings(date)
    print(f"[OK] 排行榜收集完成，共 {count} 项")
    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    backup_data()
    print("[OK] 备份完成")
    return 0


def cmd_cleanup(args: argparse.Namespace) -> int:
    cleanup_old_data()
    print("[OK] 清理完成")
    return 0


def cmd_send_test(args: argparse.Namespace) -> int:
    notifier = build_notifier(config.notification)
    msg = f"🔔 March 测试通知 @ {config.now().isoformat(timespec='seconds')}\n如果你看到这条，QQ 推送链路通了。"
    ok = notifier.send(msg, title="连通性测试")
    print(f"[{'OK' if ok else 'FAIL'}] 通知发送: {ok}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ai-news-collector",
        description="AI 技术资讯收集和推送系统",
    )
    p.add_argument("command", choices=["news", "rankings", "backup", "cleanup", "send-test"])
    p.add_argument("--date", help="指定日期 YYYY-MM-DD（仅 news / rankings）")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    _setup_root_logger()
    parser = build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "news": cmd_news,
        "rankings": cmd_rankings,
        "backup": cmd_backup,
        "cleanup": cmd_cleanup,
        "send-test": cmd_send_test,
    }
    try:
        return handlers[args.command](args)
    except Exception as e:
        logging.exception("执行失败: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
