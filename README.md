# ai-news-reference

March 的 OpenClaw workspace — 内含 **AI 技术资讯收集和推送系统 (v2)** 子项目。

子项目在 [`src/ai_news_collector/`](src/ai_news_collector/)，完整文档见 [src/ai_news_collector/README.md](src/ai_news_collector/README.md)。

## 快速链接

- 📰 [子项目代码](src/ai_news_collector/) — Python 3.10+，RSS + 排行榜 + QQ 推送
- 📋 [v2 变更说明](src/ai_news_collector/README.md#v2-重大变更对比-v1)
- 🧪 [冒烟测试](src/ai_news_collector/scripts/test_system.py)
- ⚙️ [Windows 任务计划注册](src/ai_news_collector/setup_tasks.bat)

## March 工作区文件

- `AGENTS.md` / `IDENTITY.md` / `SOUL.md` / `USER.md` / `TOOLS.md` — March 自身配置
- `HEARTBEAT.md` — 心跳任务占位
- `memory/` — 会话日志
- `.openclaw/workspace-state.json` — OpenClaw 状态

## 关于本仓库

代码上提到根（`src/ai_news_collector/`）是 v2 重构的一部分——以前是嵌套的 `ai-news-collector/` 子目录，结构不符合 Python 包规范。v2 改用标准 `src/` layout，让 `pip install -e .` 和 `python -m ai_news_collector.main` 能正常工作。
