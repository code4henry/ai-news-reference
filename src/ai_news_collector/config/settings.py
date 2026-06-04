"""
系统配置加载器
- 读取 config/news_sources.yaml
- 暴露类型化访问（news_sources / llm_rankings / notification / storage）
- 提供路径/时区等运行时辅助
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

import yaml

# ---- 基础路径 ----
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
BACKUP_DIR = BASE_DIR / "backup"
CONFIG_FILE = CONFIG_DIR / "news_sources.yaml"

# 启动时确保运行时目录存在
for _d in (DATA_DIR, LOGS_DIR, BACKUP_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def _load_yaml() -> Dict[str, Any]:
    """从 yaml 读取全部配置；不存在时返回空 dict 让上层校验。"""
    if not CONFIG_FILE.exists():
        return {}
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class Config:
    """类型化配置访问。"""

    def __init__(self, raw: Optional[Dict[str, Any]] = None) -> None:
        self._raw = raw if raw is not None else _load_yaml()

    # ---- 顶层段 ----
    @property
    def news_sources(self) -> list[Dict[str, Any]]:
        return self._raw.get("news_sources", []) or []

    @property
    def llm_rankings(self) -> list[Dict[str, Any]]:
        return self._raw.get("llm_rankings", []) or []

    @property
    def notification(self) -> Dict[str, Any]:
        return self._raw.get("notification", {}) or {}

    @property
    def storage(self) -> Dict[str, Any]:
        return self._raw.get("storage", {}) or {}

    @property
    def timezone(self) -> ZoneInfo:
        """默认 Asia/Hong_Kong（Henry 在香港）。可用 env AI_NEWS_TZ 覆盖。"""
        tz_name = os.environ.get("AI_NEWS_TZ") or self._raw.get("timezone", "Asia/Hong_Kong")
        try:
            return ZoneInfo(tz_name)
        except Exception:
            return ZoneInfo("Asia/Hong_Kong")

    # ---- 时间辅助 ----
    def now(self) -> datetime:
        """时区感知的当前时间。"""
        return datetime.now(tz=self.timezone)

    def to_local_date(self, dt: datetime) -> datetime:
        """把任何 datetime 转成当前时区的 naive datetime（用于文件名）。"""
        if dt.tzinfo is None:
            return dt
        return dt.astimezone(self.timezone).replace(tzinfo=None)

    # ---- 路径辅助 ----
    def get_data_dir(self, date: Optional[datetime] = None) -> Path:
        if date is None:
            return DATA_DIR
        return DATA_DIR / date.strftime("%Y-%m")

    def get_log_file(self, date: Optional[datetime] = None) -> Path:
        if date is None:
            date = self.to_local_date(self.now())
        return LOGS_DIR / f"ai_news_{date.strftime('%Y-%m-%d')}.log"

    def get_daily_md_file(self, date: Optional[datetime] = None) -> Path:
        if date is None:
            date = self.to_local_date(self.now())
        return self.get_data_dir(date) / f"ai_news_{date.strftime('%Y-%m-%d')}.md"

    def get_daily_json_file(self, date: Optional[datetime] = None) -> Path:
        if date is None:
            date = self.to_local_date(self.now())
        return self.get_data_dir(date) / f"ai_news_{date.strftime('%Y-%m-%d')}.json"

    def get_ranking_json_file(self, source_slug: str, date: Optional[datetime] = None) -> Path:
        if date is None:
            date = self.to_local_date(self.now())
        return self.get_data_dir(date) / f"ranking_{source_slug}_{date.strftime('%Y-%m-%d')}.json"


# 全局单例
config = Config()
