# AI技术资讯收集和推送系统

这是一个自动收集AI技术资讯和LLM排行榜数据的系统，支持定时任务自动执行。

## 功能特点

- **多源资讯收集**: 从多个AI技术网站获取最新资讯
- **LLM排行榜数据**: 收集各大LLM排行榜的实时数据
- **自动分类存储**: 按日期分类保存为Markdown和JSON格式
- **定时任务**: 支持自动定时执行收集任务
- **数据管理**: 自动清理旧数据和备份数据
- **通知推送**: 支持QQ通知推送（需要配置）

## 系统结构

```
ai-news-collector/
├── config/                 # 配置文件
│   ├── news_sources.yaml  # 新闻来源配置
│   └── settings.py         # 系统配置
├── scripts/               # 脚本文件
│   ├── news_collector.py  # 新闻收集脚本
│   ├── llm_ranking_collector.py  # 排行榜收集脚本
│   └── task_scheduler.py  # 定时任务管理脚本
├── data/                  # 数据存储目录
├── logs/                  # 日志文件目录
├── backup/                # 备份文件目录
├── main.py                # 主程序入口
├── requirements.txt       # Python依赖
├── setup_tasks.bat        # Windows定时任务设置脚本
└── README.md              # 说明文档
```

## 安装和使用

### 1. 环境准备

确保已安装Python 3.7+，然后安装依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置设置

编辑 `config/news_sources.yaml` 文件，配置新闻来源和通知设置：

```yaml
# 通知配置
notification:
  enabled: true
  method: "qq"
  qq:
    bot_id: "your_qq_bot_id"
    group_id: "your_qq_group_id"
    api_key: "your_qq_api_key"
```

### 3. 手动执行任务

```bash
# 收集今天的AI技术资讯
python main.py news

# 收集指定日期的资讯
python main.py news --date 2026-05-31

# 收集LLM排行榜数据
python main.py rankings

# 备份数据
python main.py backup

# 清理旧数据
python main.py cleanup

# 启动定时任务调度器
python main.py scheduler --daemon
```

### 4. 设置定时任务

运行Windows批处理文件自动设置定时任务：

```bash
setup_tasks.bat
```

这将创建以下定时任务：
- AI_News_Collector: 每天早上8点收集新闻
- AI_Ranking_Collector: 每天中午12点收集排行榜数据
- AI_Data_Cleanup: 每天凌晨2点清理旧数据
- AI_Data_Backup: 每周日凌晨3点备份数据

## 配置说明

### 新闻来源配置

在 `config/news_sources.yaml` 中添加或修改新闻来源：

```yaml
news_sources:
  - name: "AI News"
    url: "https://artificialintelligence-news.com/feed/"
    type: "rss"
    category: "general"
    language: "en"
```

### LLM排行榜配置

系统支持以下排行榜：
- LMSYS Chatbot Arena
- Hugging Face Open LLM Leaderboard
- Papers With Code Leaderboard

### 存储配置

```yaml
storage:
  base_dir: "./data"
  format: "markdown"
  max_days: 30
  backup_enabled: true
  backup_dir: "./backup"
```

## 数据格式

### Markdown格式示例

```markdown
# AI技术资讯 - 2026-05-31
*收集时间: 2026-05-31 17:43:00*

## MIT Technology Review AI

### [New AI Breakthrough in Natural Language Processing](https://www.technologyreview.com/article/new-ai-breakthrough/)
**发布时间:** 2026-05-31 10:30:00
**分类:** research
**语言:** en

**摘要:** 研究人员开发了新的自然语言处理模型，在多项基准测试中表现优异...

---
```

### JSON格式示例

```json
{
  "id": "abc1234567890abcd",
  "title": "New AI Breakthrough in Natural Language Processing",
  "link": "https://www.technologyreview.com/article/new-ai-breakthrough/",
  "summary": "研究人员开发了新的自然语言处理模型...",
  "published": "2026-05-31 10:30:00",
  "source": "MIT Technology Review AI",
  "category": "research",
  "language": "en"
}
```

## 日志查看

所有操作日志都会保存在 `logs/` 目录下，文件名格式为 `ai_news_YYYY-MM-DD.log`。

## 故障排除

### 1. 网络连接问题
确保网络连接正常，能够访问配置的新闻来源网站。

### 2. 依赖安装失败
尝试使用国内镜像源安装依赖：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 定时任务不执行
检查Windows任务计划程序中的任务状态，确保任务已启用且路径正确。

### 4. 权限问题
确保脚本有足够的权限访问数据目录和创建文件。

## 扩展功能

### 添加新的新闻来源
1. 在 `config/news_sources.yaml` 中添加新的RSS源
2. 确保RSS源格式正确
3. 重新运行收集脚本

### 自定义通知方式
1. 修改 `config/news_sources.yaml` 中的通知配置
2. 在相应的脚本中添加通知逻辑

### 数据处理和分析
可以使用 `data/` 目录下的JSON数据进行进一步的分析和处理。

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件