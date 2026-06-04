"""
AI 资讯 RSS 收集器（v2）
- RSS 拉取：feedparser（HTTP 用 requests）
- 全文抓取：aiohttp + asyncio.Semaphore 并发
- 去重：URL 规范化（去 utm_* 等 tracking 参数）
- 时区：统一走 config.timezone
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import feedparser
import requests
from bs4 import BeautifulSoup

from ai_news_collector.config.settings import config
from ai_news_collector.notifications.qq import build_notifier, format_news_summary
from ai_news_collector.scripts.utils import dedupe_by_link, setup_logger

DEFAULT_HEADERS = {"User-Agent": "AI-News-Collector/2.0"}


class NewsCollector:
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or setup_logger("NewsCollector", log_file=str(config.get_log_file()))
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    # ---- 工具 ----
    @staticmethod
    def _make_id(url: str, title: str) -> str:
        return hashlib.md5(f"{url}|{title}".encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _clean_html(text: str) -> str:
        if not text:
            return ""
        # 用 BS4 兜底（更鲁棒），失败时退回 regex
        try:
            soup = BeautifulSoup(text, "html.parser")
            return soup.get_text(separator=" ", strip=True)
        except Exception:
            return re.sub(r"<[^>]+>", "", text).strip()

    def _parse_published(self, entry) -> Optional[datetime]:
        for key in ("published_parsed", "updated_parsed"):
            t = entry.get(key)
            if t:
                try:
                    return datetime(*t[:6])
                except Exception:
                    continue
        return None

    # ---- RSS 拉取 ----
    def fetch_rss_feed(self, source: Dict) -> List[Dict]:
        articles: List[Dict] = []
        try:
            self.logger.info("正在拉取 %s ...", source.get("name", "?"))
            r = self.session.get(source["url"], timeout=30, headers=DEFAULT_HEADERS)
            r.raise_for_status()
            feed = feedparser.parse(r.content)
            if feed.bozo and not feed.entries:
                self.logger.warning("RSS 解析失败: %s err=%s", source.get("name"), getattr(feed, "bozo_exception", ""))
                return articles

            for entry in feed.entries:
                link = entry.get("link", "")
                title = entry.get("title", "").strip()
                if not link or not title:
                    continue
                article = {
                    "id": self._make_id(link, title),
                    "title": title,
                    "link": link,
                    "summary": self._clean_html(entry.get("summary") or entry.get("description") or ""),
                    "content": "",  # 后续 async 抓全文
                    "published_raw": entry.get("published", ""),
                    "published_at": self._parse_published(entry).isoformat() if self._parse_published(entry) else None,
                    "source": source.get("name", "未知来源"),
                    "category": source.get("category", ""),
                    "language": source.get("language", "en"),
                    "tags": [t.get("term", "") for t in entry.get("tags", []) if t.get("term")],
                }
                articles.append(article)
            self.logger.info("  ✓ %s → %d 篇", source.get("name"), len(articles))
        except requests.RequestException as e:
            self.logger.error("拉取失败: %s err=%s", source.get("name"), e)
        return articles

    # ---- 全文并发抓取 ----
    async def _fetch_one_full_text(self, session: aiohttp.ClientSession, article: Dict, sem: asyncio.Semaphore,
                                   timeout: int, max_chars: int) -> None:
        async with sem:
            try:
                async with session.get(article["link"], timeout=aiohttp.ClientTimeout(total=timeout),
                                        headers=DEFAULT_HEADERS) as resp:
                    if resp.status != 200:
                        return
                    text = await resp.text()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                return
            # 提取正文文本（很粗略，但够摘要用）
            try:
                soup = BeautifulSoup(text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()
                body = soup.get_text(separator=" ", strip=True)
            except Exception:
                body = text
            article["content"] = body[:max_chars]

    async def _enrich_with_full_text(self, articles: List[Dict]) -> List[Dict]:
        fetch_cfg = (config._raw.get("fetch") or {})
        concurrency = int(fetch_cfg.get("full_text_concurrency", 10))
        timeout = int(fetch_cfg.get("full_text_per_request_timeout", 10))
        max_chars = int(fetch_cfg.get("full_text_max_chars", 2000))
        sem = asyncio.Semaphore(concurrency)
        async with aiohttp.ClientSession() as session:
            await asyncio.gather(*(self._fetch_one_full_text(session, a, sem, timeout, max_chars) for a in articles))
        return articles

    # ---- 保存 ----
    def save_articles(self, articles: List[Dict], date: datetime) -> Dict[str, Path]:
        if not articles:
            self.logger.info("无文章，跳过保存")
            return {}
        date = config.to_local_date(date)
        data_dir = config.get_data_dir(date)
        data_dir.mkdir(parents=True, exist_ok=True)
        md_path = config.get_daily_md_file(date)
        json_path = config.get_daily_json_file(date)
        md_path.write_text(self._to_markdown(articles, date), encoding="utf-8")
        json_path.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
        self.logger.info("已保存: %s / %s", md_path, json_path)
        return {"md": md_path, "json": json_path}

    def _to_markdown(self, articles: List[Dict], date: datetime) -> str:
        head = f"# AI 技术资讯 - {date.strftime('%Y-%m-%d')}\n\n*收集时间: {config.now().isoformat(timespec='seconds')}*\n\n"
        body = []
        by_source: Dict[str, List[Dict]] = {}
        for a in articles:
            by_source.setdefault(a.get("source", "未知来源"), []).append(a)
        for source, items in by_source.items():
            body.append(f"## {source} ({len(items)})\n")
            for a in items:
                body.append(f"### [{a['title']}]({a['link']})\n")
                if a.get("published_raw"):
                    body.append(f"**发布时间:** {a['published_raw']}  ")
                if a.get("category"):
                    body.append(f"**分类:** {a['category']}  ")
                if a.get("language"):
                    body.append(f"**语言:** {a['language']}\n")
                if a.get("summary"):
                    body.append(f"\n**摘要:**\n{a['summary']}\n")
                if a.get("content"):
                    preview = a["content"][:500].replace("\n", " ")
                    body.append(f"\n**内容预览:**\n{preview}...\n")
                body.append("\n---\n")
        return head + "\n".join(body)

    # ---- 通知 ----
    def _notify(self, articles: List[Dict], date: datetime) -> None:
        if not (articles and config.notification.get("enabled")):
            return
        try:
            notifier = build_notifier(config.notification, logger=self.logger)
            date_str = config.to_local_date(date).strftime("%Y-%m-%d")
            msg = format_news_summary(articles, date_str)
            notifier.send(msg, title="AI 资讯日报")
        except Exception as e:
            self.logger.error("通知发送失败: %s", e)

    # ---- 入口 ----
    def collect_daily_news(self, date: Optional[datetime] = None) -> int:
        if date is None:
            date = config.now()
        date_naive = config.to_local_date(date)
        self.logger.info("开始收集 %s 的 AI 资讯 ...", date_naive.strftime("%Y-%m-%d"))

        all_articles: List[Dict] = []
        for source in config.news_sources:
            if source.get("type", "rss") == "rss":
                all_articles.extend(self.fetch_rss_feed(source))

        before = len(all_articles)
        all_articles = dedupe_by_link(all_articles)
        self.logger.info("去重: %d → %d", before, len(all_articles))

        # 异步抓全文
        try:
            all_articles = asyncio.run(self._enrich_with_full_text(all_articles))
        except Exception as e:
            self.logger.error("全文抓取失败（继续保存）: %s", e)

        self.save_articles(all_articles, date_naive)
        self._notify(all_articles, date_naive)
        self.logger.info("完成: %d 篇", len(all_articles))
        return len(all_articles)


if __name__ == "__main__":
    import sys
    from ai_news_collector.main import build_parser, main
    sys.exit(main(["news"]))
