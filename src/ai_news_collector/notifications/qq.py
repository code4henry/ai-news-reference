"""
通知发送层
- 当前支持 QQ bot（基于 go-cqhttp / OneBot v11 协议）
- 通过 HTTP POST 推送到 bot 端点
- 配置从 config.news_sources.yaml 的 notification.qq 段读取
- token / endpoint 可通过环境变量覆盖：QQ_BOT_HTTP_API / QQ_BOT_TOKEN
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

import requests


class BaseNotifier:
    def send(self, message: str, *, title: Optional[str] = None) -> bool:
        raise NotImplementedError


class QQNotifier(BaseNotifier):
    """通过 go-cqhttp / OneBot v11 HTTP API 发送群消息 / 私聊消息。"""

    def __init__(self, cfg: Dict[str, Any], logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        # env 优先
        self.endpoint = (
            os.environ.get("QQ_BOT_HTTP_API")
            or cfg.get("endpoint", "http://127.0.0.1:5700")
        ).rstrip("/")
        self.access_token = os.environ.get("QQ_BOT_TOKEN") or cfg.get("access_token", "")
        self.bot_id = cfg.get("bot_id") or cfg.get("bot_qq") or os.environ.get("QQ_BOT_ID", "")
        self.group_id = cfg.get("group_id") or os.environ.get("QQ_GROUP_ID", "")
        self.user_id = cfg.get("user_id") or os.environ.get("QQ_USER_ID", "")
        self.timeout = int(cfg.get("timeout", 10))

    def _post(self, action: str, params: Dict[str, Any]) -> bool:
        url = f"{self.endpoint}/{action}"
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        try:
            r = requests.post(url, json=params, headers=headers, timeout=self.timeout)
            if r.status_code != 200:
                self.logger.error("QQ notifier HTTP %s: %s", r.status_code, r.text[:200])
                return False
            try:
                payload = r.json()
            except json.JSONDecodeError:
                self.logger.error("QQ notifier returned non-JSON: %s", r.text[:200])
                return False
            if payload.get("retcode", 0) != 0:
                self.logger.error("QQ notifier retcode=%s msg=%s", payload.get("retcode"), payload.get("msg"))
                return False
            return True
        except requests.RequestException as e:
            self.logger.error("QQ notifier request failed: %s", e)
            return False

    def send(self, message: str, *, title: Optional[str] = None) -> bool:
        if title:
            message = f"【{title}】\n{message}"

        if self.group_id:
            ok = self._post(
                "send_group_msg",
                {"group_id": int(self.group_id), "message": [{"type": "text", "data": {"text": message}}]},
            )
            if ok:
                self.logger.info("QQ group message sent to group_id=%s", self.group_id)
                return True
        if self.user_id:
            ok = self._post(
                "send_private_msg",
                {"user_id": int(self.user_id), "message": [{"type": "text", "data": {"text": message}}]},
            )
            if ok:
                self.logger.info("QQ private message sent to user_id=%s", self.user_id)
                return True

        self.logger.warning(
            "QQ notifier: neither group_id nor user_id configured; message not sent. "
            "Set notification.qq.group_id or .user_id in news_sources.yaml, "
            "or env QQ_GROUP_ID / QQ_USER_ID."
        )
        return False


def build_notifier(notification_cfg: Dict[str, Any], logger: Optional[logging.Logger] = None) -> BaseNotifier:
    """根据 notification.method 构造对应 notifier。"""
    method = (notification_cfg or {}).get("method", "qq").lower()
    if method == "qq":
        return QQNotifier(notification_cfg.get("qq", {}), logger=logger)
    # 留扩展点：method == "telegram" / "feishu" 时接对应实现
    raise ValueError(f"Unsupported notification method: {method}")


def format_news_summary(articles: List[Dict[str, Any]], date_str: str) -> str:
    """生成推送文本：按来源分组、列前 5 条标题+链接。"""
    if not articles:
        return f"📭 {date_str} 无新文章"

    by_source: Dict[str, List[Dict[str, Any]]] = {}
    for a in articles:
        by_source.setdefault(a.get("source", "未知来源"), []).append(a)

    lines = [f"📰 AI 资讯日报 - {date_str}", f"共 {len(articles)} 篇：", ""]
    for source, items in by_source.items():
        lines.append(f"▸ {source} ({len(items)})")
        for it in items[:5]:
            title = it.get("title", "").strip().replace("\n", " ")
            link = it.get("link", "")
            lines.append(f"  · {title}")
            if link:
                lines.append(f"    {link}")
        if len(items) > 5:
            lines.append(f"  · ... 还有 {len(items) - 5} 篇")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_rankings_summary(rankings: List[Dict[str, Any]], date_str: str) -> str:
    """生成排行榜推送文本：每个榜单的 top 5。"""
    if not rankings:
        return f"📊 {date_str} 无新排行榜数据"

    lines = [f"📊 LLM 排行榜更新 - {date_str}", ""]
    for r in rankings:
        source = r.get("source", "未知")
        lines.append(f"▸ {source}")
        rows = r.get("data")
        # 接受 list / dict-of-list / str 多种形状
        if isinstance(rows, list):
            iter_rows = rows
        elif isinstance(rows, dict):
            iter_rows = rows.get("results") or rows.get("data") or rows.get("leaderboard") or []
            if not isinstance(iter_rows, list):
                iter_rows = []
        else:
            iter_rows = []
        for i, row in enumerate(iter_rows[:5], 1):
            if not isinstance(row, dict):
                continue
            name = row.get("model") or row.get("name") or row.get("title") or "?"
            score = row.get("score") or row.get("rating") or row.get("elo")
            if score is not None:
                lines.append(f"  {i}. {name} — {score}")
            else:
                lines.append(f"  {i}. {name}")
        if not iter_rows:
            lines.append("  (无结构化数据，本次仅抓取页面快照)")
        lines.append("")
    return "\n".join(lines).rstrip()
