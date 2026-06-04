"""
LLM 排行榜数据收集（v2）
- LMSYS Arena：拉 lmarena.ai 的 JSON 接口
- Hugging Face / Papers with Code：使用公开 JSON API
- 输出每日快照 + 与前一日对比的 diff（top-10 排名变化）
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests

from ai_news_collector.config.settings import config
from ai_news_collector.notifications.qq import build_notifier, format_rankings_summary
from ai_news_collector.scripts.utils import setup_logger

DEFAULT_HEADERS = {"User-Agent": "LLM-Ranking-Collector/2.0"}


class LLMRankingCollector:
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or setup_logger("LLMRankingCollector", log_file=str(config.get_log_file()))
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    # ---- 各源实现 ----
    def fetch_lmsys_arena(self) -> Optional[Dict]:
        """lmarena.ai 的 leaderboard 公开数据。"""
        try:
            self.logger.info("拉取 LMSYS Chatbot Arena ...")
            # 公开 HTML 页面包含嵌入 JSON；这里保守做：先尝试旧 JSON endpoint 兜底
            for url in (
                "https://lmarena.ai/api/leaderboard",
                "https://chat.lmsys.org/api/leaderboard",
            ):
                try:
                    r = self.session.get(url, timeout=30, headers=DEFAULT_HEADERS)
                    if r.status_code == 200 and r.headers.get("content-type", "").startswith("application/json"):
                        data = r.json()
                        return self._wrap("lmsys_arena", "LMSYS Chatbot Arena", "arena", data)
                except requests.RequestException:
                    continue
            # 兜底：标记为未取到
            self.logger.warning("LMSYS 接口当前不可用，跳过")
            return None
        except Exception as e:
            self.logger.error("LMSYS 抓取失败: %s", e)
            return None

    def fetch_hf_open_llm(self) -> Optional[Dict]:
        """Hugging Face Open LLM Leaderboard 公开 JSON。"""
        try:
            self.logger.info("拉取 Hugging Face Open LLM Leaderboard ...")
            url = "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard"
            r = self.session.get(url, timeout=30, headers=DEFAULT_HEADERS)
            r.raise_for_status()
            # 页面里有嵌入 JSON。简化处理：保存页面快照 + 标记可解析
            return self._wrap(
                "hf_open_llm",
                "Hugging Face Open LLM Leaderboard",
                "benchmark",
                {"raw_html_length": len(r.text), "source_url": url, "status": "page_snapshot"},
            )
        except Exception as e:
            self.logger.error("HF 抓取失败: %s", e)
            return None

    def fetch_paperswithcode_sota(self) -> Optional[Dict]:
        """Papers with Code SOTA 公开 API。"""
        try:
            self.logger.info("拉取 Papers With Code SOTA ...")
            r = self.session.get("https://paperswithcode.com/api/v1/sota-papers/?page=1&items_per_page=20",
                                  timeout=30, headers=DEFAULT_HEADERS)
            r.raise_for_status()
            data = r.json()
            rows = []
            for item in data.get("results", []) or []:
                rows.append({
                    "model": item.get("title") or item.get("paper", {}).get("title"),
                    "score": None,
                    "task": (item.get("task") or {}).get("name"),
                    "date": item.get("date"),
                    "link": item.get("paper", {}).get("url_abs"),
                })
            return self._wrap("paperswithcode_sota", "Papers With Code SOTA", "benchmark", rows)
        except Exception as e:
            self.logger.error("PWC 抓取失败: %s", e)
            return None

    def _wrap(self, slug: str, source: str, category: str, data) -> Dict:
        return {
            "slug": slug,
            "source": source,
            "category": category,
            "collected_at": config.now().isoformat(timespec="seconds"),
            "data": data,
        }

    # ---- 保存 + diff ----
    def save_ranking(self, ranking: Dict, date: datetime) -> Path:
        date_naive = config.to_local_date(date)
        path = config.get_ranking_json_file(ranking["slug"], date_naive)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(ranking, ensure_ascii=False, indent=2), encoding="utf-8")
        self.logger.info("保存: %s", path)
        return path

    def load_previous_ranking(self, slug: str, current_date: datetime) -> Optional[Dict]:
        """尝试加载前一天的快照，用于 diff。"""
        prev_date = config.to_local_date(current_date) - timedelta(days=1)
        path = config.get_ranking_json_file(slug, prev_date)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def compute_diff(self, slug: str, source: str, current_rows: List[Dict],
                      previous: Optional[Dict]) -> List[Dict]:
        """对 top 模型排名做 diff。current_rows 必须是 [{model, score}, ...] 列表。"""
        if not previous or not isinstance(previous.get("data"), list) or not isinstance(current_rows, list):
            return []
        prev_rows = previous["data"]
        prev_map = {r.get("model"): i for i, r in enumerate(prev_rows) if r.get("model")}
        diffs = []
        for i, r in enumerate(current_rows):
            if not isinstance(r, dict):
                continue
            m = r.get("model")
            if not m:
                continue
            prev_rank = prev_map.get(m)
            if prev_rank is None:
                diffs.append({"model": m, "current_rank": i, "delta": "new"})
            else:
                delta = prev_rank - i  # 正数 = 上升
                if delta != 0:
                    diffs.append({"model": m, "current_rank": i, "previous_rank": prev_rank, "delta": delta})
        diffs.sort(key=lambda x: (x["current_rank"]))
        return diffs[:10]

    # ---- 入口 ----
    def collect_daily_rankings(self, date: Optional[datetime] = None) -> int:
        if date is None:
            date = config.now()
        date_naive = config.to_local_date(date)
        self.logger.info("开始收集 %s 的 LLM 排行榜 ...", date_naive.strftime("%Y-%m-%d"))

        rankings: List[Dict] = []
        for source in config.llm_rankings:
            slug = source.get("slug", source.get("name", "").lower().replace(" ", "_"))
            try:
                if slug == "lmsys_arena":
                    r = self.fetch_lmsys_arena()
                elif slug == "hf_open_llm":
                    r = self.fetch_hf_open_llm()
                elif slug == "paperswithcode_sota":
                    r = self.fetch_paperswithcode_sota()
                else:
                    self.logger.warning("未知源: %s", source.get("name"))
                    continue
            except Exception as e:
                self.logger.error("%s 抓取异常: %s", source.get("name"), e)
                continue

            if not r:
                continue

            # diff（仅对 list 类型 data）
            if isinstance(r.get("data"), list):
                prev = self.load_previous_ranking(slug, date_naive)
                r["diff_vs_yesterday"] = self.compute_diff(slug, r["source"], r["data"], prev)

            self.save_ranking(r, date_naive)
            rankings.append(r)

        # 通知
        if rankings and config.notification.get("enabled"):
            try:
                notifier = build_notifier(config.notification, logger=self.logger)
                msg = format_rankings_summary(rankings, date_naive.strftime("%Y-%m-%d"))
                notifier.send(msg, title="LLM 排行榜更新")
            except Exception as e:
                self.logger.error("排行榜通知失败: %s", e)

        self.logger.info("完成: %d 项", len(rankings))
        return len(rankings)


if __name__ == "__main__":
    import sys
    from ai_news_collector.main import main
    sys.exit(main(["rankings"]))
