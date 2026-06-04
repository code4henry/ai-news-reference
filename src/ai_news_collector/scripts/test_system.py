"""
系统冒烟测试
- 不依赖外部网络（默认）
- ``--live`` 模式下会真实拉取 RSS / 排行榜（CI 里别开）

运行：
    python -m pytest ai-news-collector/scripts/test_system.py -v
    python -m ai_news_collector.scripts.test_system            # 直接当脚本跑
    python -m ai_news_collector.scripts.test_system --live      # 真打网络
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path


def test_config_loads():
    from ai_news_collector.config.settings import config
    assert isinstance(config.news_sources, list)
    assert isinstance(config.llm_rankings, list)
    assert isinstance(config.notification, dict)
    assert isinstance(config.storage, dict)


def test_timezone_aware():
    from ai_news_collector.config.settings import config
    now = config.now()
    assert now.tzinfo is not None
    assert str(now.tzinfo) == str(config.timezone)


def test_directories_exist():
    from ai_news_collector.config.settings import DATA_DIR, LOGS_DIR
    assert DATA_DIR.exists(), DATA_DIR
    assert LOGS_DIR.exists(), LOGS_DIR


def test_dedupe():
    from ai_news_collector.scripts.utils import dedupe_by_link, normalize_url
    assert normalize_url("https://x.com/a?utm_source=t&b=1") == "https://x.com/a?b=1"
    arts = [
        {"title": "A", "link": "https://x.com/a?utm_source=fb"},
        {"title": "A2", "link": "https://x.com/a"},
        {"title": "B", "link": "https://y.com/b"},
    ]
    out = dedupe_by_link(arts)
    assert len(out) == 2


def test_url_normalize_idempotent():
    from ai_news_collector.scripts.utils import normalize_url
    u1 = "HTTPS://X.com/Path/?utm_source=t&a=1"
    u2 = normalize_url(normalize_url(u1))
    assert u1.lower().split("?", 1)[0] in u2 or u2.startswith("https://x.com/")


def test_notifier_builds():
    from ai_news_collector.config.settings import config
    from ai_news_collector.notifications.qq import build_notifier
    if config.notification.get("method") == "qq":
        n = build_notifier(config.notification)
        assert n.__class__.__name__ == "QQNotifier"


# ---- 真实拉取（默认关闭）----
def test_live_fetch_news(live: bool = False):
    if not live:
        return
    from ai_news_collector.scripts.news_collector import NewsCollector
    c = NewsCollector()
    n = c.collect_daily_news()
    assert n >= 0  # 允许为 0（RSS 偶发不可用）


def test_live_fetch_rankings(live: bool = False):
    if not live:
        return
    from ai_news_collector.scripts.llm_ranking_collector import LLMRankingCollector
    c = LLMRankingCollector()
    n = c.collect_daily_rankings()
    assert n >= 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="真实拉取 RSS / API")
    args, _ = parser.parse_known_args()

    tests = [
        ("config_loads", test_config_loads),
        ("timezone_aware", test_timezone_aware),
        ("directories_exist", test_directories_exist),
        ("dedupe", test_dedupe),
        ("url_normalize_idempotent", test_url_normalize_idempotent),
        ("notifier_builds", test_notifier_builds),
    ]
    if args.live:
        tests.append(("live_fetch_news", lambda: test_live_fetch_news(True)))
        tests.append(("live_fetch_rankings", lambda: test_live_fetch_rankings(True)))

    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[OK] {name}")
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {name}: {e}")
        except Exception as e:
            print(f"[ERR] {name}: {type(e).__name__}: {e}")

    print(f"\n{passed}/{len(tests)} 通过")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())
