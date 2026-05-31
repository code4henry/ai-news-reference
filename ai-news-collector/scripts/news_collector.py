"""
AI技术资讯收集脚本
"""
import requests
import feedparser
from datetime import datetime, timedelta
import time
import logging
from pathlib import Path
import json
import re
from typing import List, Dict, Optional
import hashlib

# 添加父目录到路径
import sys
sys.path.append(str(Path(__file__).parent.parent / "config"))
from settings import config

class NewsCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI-News-Collector/1.0'
        })
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger('NewsCollector')
        logger.setLevel(logging.INFO)
        
        # 文件处理器
        log_file = config.get_log_file()
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _generate_id(self, url: str, title: str) -> str:
        """生成文章唯一ID"""
        content = f"{url}{title}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
    
    def _clean_html(self, html: str) -> str:
        """清理HTML标签"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html)
    
    def _extract_content(self, entry) -> Dict:
        """提取文章内容"""
        article_id = self._generate_id(entry.get('link', ''), entry.get('title', ''))
        
        article = {
            'id': article_id,
            'title': entry.get('title', '无标题'),
            'link': entry.get('link', ''),
            'summary': entry.get('summary', entry.get('description', '')),
            'content': '',
            'published': entry.get('published', ''),
            'updated': entry.get('updated', ''),
            'source': entry.get('source', {}).get('title', '未知来源'),
            'category': '',
            'language': 'en',
            'tags': []
        }
        
        # 尝试获取内容
        try:
            response = self.session.get(article['link'], timeout=10)
            if response.status_code == 200:
                # 这里可以添加更复杂的内容提取逻辑
                article['content'] = response.text[:5000]  # 限制内容长度
        except Exception as e:
            self.logger.warning(f"获取文章内容失败: {article['link']}, 错误: {str(e)}")
        
        return article
    
    def fetch_rss_feed(self, source: Dict) -> List[Dict]:
        """获取RSS feed"""
        articles = []
        
        try:
            self.logger.info(f"正在获取 {source['name']} 的RSS feed...")
            
            response = self.session.get(source['url'], timeout=30)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                self.logger.warning(f"RSS feed解析警告: {source['name']}")
            
            for entry in feed.entries:
                article = self._extract_content(entry)
                article['category'] = source['category']
                article['language'] = source['language']
                articles.append(article)
                
            self.logger.info(f"从 {source['name']} 获取到 {len(articles)} 篇文章")
            
        except Exception as e:
            self.logger.error(f"获取RSS feed失败: {source['name']}, 错误: {str(e)}")
            
        return articles
    
    def save_articles(self, articles: List[Dict], date: datetime):
        """保存文章到文件"""
        if not articles:
            self.logger.info("没有文章需要保存")
            return
        
        # 确保数据目录存在
        data_dir = config.get_data_dir(date)
        data_dir.mkdir(exist_ok=True)
        
        # 按日期保存
        daily_file = config.get_daily_file(date)
        
        # 生成Markdown内容
        md_content = self._generate_markdown(articles, date)
        
        # 保存文件
        with open(daily_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        self.logger.info(f"保存了 {len(articles)} 篇文章到 {daily_file}")
        
        # 保存JSON格式以便后续处理
        json_file = data_dir / f"ai_news_{date.strftime('%Y-%m-%d')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
    
    def _generate_markdown(self, articles: List[Dict], date: datetime) -> str:
        """生成Markdown格式内容"""
        # 生成日期标题
        content = f"# AI技术资讯 - {date.strftime('%Y-%m-%d')}\n\n"
        content += f"*收集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        # 按来源分组
        sources = {}
        for article in articles:
            source_name = article['source']
            if source_name not in sources:
                sources[source_name] = []
            sources[source_name].append(article)
        
        # 生成内容
        for source_name, source_articles in sources.items():
            content += f"## {source_name}\n\n"
            
            for article in source_articles:
                content += f"### [{article['title']}]({article['link']})\n\n"
                content += f"**发布时间:** {article['published']}\n"
                content += f"**分类:** {article['category']}\n"
                content += f"**语言:** {article['language']}\n\n"
                
                # 摘要
                if article['summary']:
                    content += f"**摘要:**\n{self._clean_html(article['summary'])}\n\n"
                
                # 内容预览
                if article['content']:
                    content += f"**内容预览:**\n{self._clean_html(article['content'][:500])}...\n\n"
                
                content += "---\n\n"
        
        return content
    
    def collect_daily_news(self, date: datetime = None):
        """收集每日新闻"""
        if date is None:
            date = datetime.now()
        
        self.logger.info(f"开始收集 {date.strftime('%Y-%m-%d')} 的AI技术资讯...")
        
        all_articles = []
        
        # 收集所有来源的新闻
        for source in config.news_sources:
            if source['type'] == 'rss':
                articles = self.fetch_rss_feed(source)
                all_articles.extend(articles)
                time.sleep(1)  # 避免请求过快
        
        # 保存文章
        self.save_articles(all_articles, date)
        
        # 发送通知
        if all_articles and config.notification['enabled']:
            self.send_notification(all_articles, date)
        
        self.logger.info(f"完成收集，共获取 {len(all_articles)} 篇文章")
        
        return len(all_articles)
    
    def send_notification(self, articles: List[Dict], date: datetime):
        """发送通知"""
        # 这里可以集成QQ通知或其他通知方式
        self.logger.info("准备发送通知...")
        
        # 示例：简单的日志通知
        summary = f"AI技术资讯收集完成 - {date.strftime('%Y-%m-%d')}\n"
        summary += f"共收集到 {len(articles)} 篇文章\n"
        
        # 统计来源
        sources = {}
        for article in articles:
            source = article['source']
            sources[source] = sources.get(source, 0) + 1
        
        summary += "\n来源统计:\n"
        for source, count in sources.items():
            summary += f"- {source}: {count} 篇\n"
        
        self.logger.info(summary)

def main():
    """主函数"""
    collector = NewsCollector()
    
    # 获取命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='AI技术资讯收集器')
    parser.add_argument('--date', help='指定日期 (YYYY-MM-DD)')
    args = parser.parse_args()
    
    # 解析日期
    date = None
    if args.date:
        try:
            date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"日期格式错误: {args.date}")
            return
    
    # 执行收集
    article_count = collector.collect_daily_news(date)
    print(f"收集完成，共获取 {article_count} 篇文章")

if __name__ == "__main__":
    main()