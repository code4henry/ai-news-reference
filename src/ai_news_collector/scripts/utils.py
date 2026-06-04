"""
通用工具：URL 规范化、日志设置
"""
from __future__ import annotations

import logging
import re
from collections import OrderedDict
from typing import Dict, Iterable, List, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# 这些 utm_* 参数对内容去重毫无意义
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "ref", "ref_src", "ref_url", "mc_cid", "mc_eid",
    "_ga", "igshid",
}


def normalize_url(url: str) -> str:
    """去掉 utm / 跟踪参数；统一 host 小写、去掉 fragment、排序剩余 query。"""
    if not url:
        return ""
    try:
        p = urlparse(url.strip())
    except Exception:
        return url
    host = p.netloc.lower()
    # 过滤 tracking 参数
    pairs = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k not in _TRACKING_PARAMS]
    # 去掉空 fragment 和 trailing slash
    path = p.path.rstrip("/") or "/"
    new_q = urlencode(sorted(pairs), doseq=True)
    return urlunparse((p.scheme.lower(), host, path, p.params, new_q, ""))


def dedupe_by_link(articles: Iterable[Dict]) -> List[Dict]:
    """按规范化后的 link 去重；首次出现的优先。"""
    seen: "OrderedDict[str, Dict]" = OrderedDict()
    for a in articles:
        key = normalize_url(a.get("link", "")) or a.get("title", "")
        if key and key not in seen:
            seen[key] = a
    return list(seen.values())


def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # 避免重复 handler（多次实例化时）
    logger.setLevel(level)
    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    if log_file:
        from pathlib import Path
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    logger.propagate = False
    return logger
