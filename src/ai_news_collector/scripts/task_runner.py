"""
数据生命周期管理：备份 / 清理
- 由 main.py 命令直接调用
- 也可被外部调度（Windows 任务计划 / cron）独立调用
"""
from __future__ import annotations

import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from ai_news_collector.config.settings import DATA_DIR, config

logger = logging.getLogger("task_runner")


def cleanup_old_data(max_days: int | None = None) -> int:
    """删除早于 max_days 的月份目录。返回清理的目录数。"""
    if max_days is None:
        max_days = int(config.storage.get("max_days", 30))
    cutoff = config.now().replace(tzinfo=None) - timedelta(days=max_days)
    removed = 0
    if not DATA_DIR.exists():
        logger.info("数据目录不存在，跳过清理: %s", DATA_DIR)
        return 0
    for month_dir in DATA_DIR.iterdir():
        if not month_dir.is_dir():
            continue
        try:
            year, month = month_dir.name.split("-")
            dir_month_start = datetime(int(year), int(month), 1)
        except ValueError:
            continue
        if dir_month_start < cutoff:
            logger.info("清理旧数据: %s", month_dir)
            shutil.rmtree(month_dir)
            removed += 1
    logger.info("清理完成，删除 %d 个月份目录", removed)
    return removed


def backup_data(backup_dir: Path | None = None) -> Path:
    """打包 DATA_DIR 为 tar.gz 到 backup_dir。返回归档文件路径。"""
    if not config.storage.get("backup_enabled", True):
        logger.info("备份已禁用（storage.backup_enabled=false）")
        return Path()
    if backup_dir is None:
        backup_dir = Path(config.storage.get("backup_dir", "./backup")).resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)
    if not DATA_DIR.exists() or not any(DATA_DIR.iterdir()):
        logger.warning("数据目录为空，跳过备份")
        return Path()
    stamp = config.now().strftime("%Y%m%d_%H%M%S")
    archive_base = backup_dir / f"ai_news_backup_{stamp}"
    archive_path = shutil.make_archive(str(archive_base), "gztar", root_dir=DATA_DIR.parent, base_dir=DATA_DIR.name)
    logger.info("备份完成: %s", archive_path)
    return Path(archive_path)
