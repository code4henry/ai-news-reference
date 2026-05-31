"""
LLM API排行榜数据收集脚本
"""
import requests
import json
from datetime import datetime, timedelta
import time
import logging
from pathlib import Path
import re
from typing import List, Dict, Optional
import hashlib

# 添加父目录到路径
import sys
sys.path.append(str(Path(__file__).parent.parent / "config"))
from settings import config

class LLMRankingCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LLM-Ranking-Collector/1.0'
        })
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger('LLMRankingCollector')
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
    
    def _generate_id(self, name: str, date: str) -> str:
        """生成排行榜唯一ID"""
        content = f"{name}{date}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
    
    def fetch_lmsys_arena(self) -> Dict:
        """获取LMSYS Chatbot Arena数据"""
        try:
            self.logger.info("正在获取LMSYS Chatbot Arena数据...")
            
            url = "https://chat.lmsys.org/api/leaderboard"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 格式化数据
            ranking_data = {
                'id': self._generate_id('LMSYS_Arena', datetime.now().strftime('%Y-%m-%d')),
                'source': 'LMSYS Chatbot Arena',
                'type': 'arena',
                'collected_at': datetime.now().isoformat(),
                'data': data
            }
            
            self.logger.info(f"成功获取LMSYS Chatbot Arena数据，共 {len(data.get('data', []))} 个模型")
            return ranking_data
            
        except Exception as e:
            self.logger.error(f"获取LMSYS Chatbot Arena数据失败: {str(e)}")
            return None
    
    def fetch_huggingface_leaderboard(self) -> Dict:
        """获取Hugging Face Open LLM Leaderboard数据"""
        try:
            self.logger.info("正在获取Hugging Face Open LLM Leaderboard数据...")
            
            url = "https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard"
            
            # 获取页面内容
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 这里可以添加更复杂的数据提取逻辑
            # 简化版本：记录获取状态
            ranking_data = {
                'id': self._generate_id('HuggingFace_Leaderboard', datetime.now().strftime('%Y-%m-%d')),
                'source': 'Hugging Face Open LLM Leaderboard',
                'type': 'web',
                'collected_at': datetime.now().isoformat(),
                'status': 'page_retrieved',
                'url': url,
                'content_length': len(response.text)
            }
            
            self.logger.info(f"成功获取Hugging Face页面，内容长度: {len(response.text)} 字符")
            return ranking_data
            
        except Exception as e:
            self.logger.error(f"获取Hugging Face Leaderboard数据失败: {str(e)}")
            return None
    
    def fetch_paperswithcode_leaderboard(self) -> Dict:
        """获取Papers With Code Leaderboard数据"""
        try:
            self.logger.info("正在获取Papers With Code Leaderboard数据...")
            
            url = "https://paperswithcode.com/sota"
            
            # 获取页面内容
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 这里可以添加更复杂的数据提取逻辑
            # 简化版本：记录获取状态
            ranking_data = {
                'id': self._generate_id('PapersWithCode_Leaderboard', datetime.now().strftime('%Y-%m-%d')),
                'source': 'Papers With Code Leaderboard',
                'type': 'web',
                'collected_at': datetime.now().isoformat(),
                'status': 'page_retrieved',
                'url': url,
                'content_length': len(response.text)
            }
            
            self.logger.info(f"成功获取Papers With Code页面，内容长度: {len(response.text)} 字符")
            return ranking_data
            
        except Exception as e:
            self.logger.error(f"获取Papers With Code Leaderboard数据失败: {str(e)}")
            return None
    
    def save_ranking_data(self, ranking_data: Dict, date: datetime):
        """保存排行榜数据"""
        if not ranking_data:
            return
        
        # 确保数据目录存在
        data_dir = config.get_data_dir(date)
        data_dir.mkdir(exist_ok=True)
        
        # 保存JSON格式
        json_file = data_dir / f"llm_ranking_{date.strftime('%Y-%m-%d')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(ranking_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"保存了排行榜数据到 {json_file}")
    
    def collect_daily_rankings(self, date: datetime = None):
        """收集每日排行榜数据"""
        if date is None:
            date = datetime.now()
        
        self.logger.info(f"开始收集 {date.strftime('%Y-%m-%d')} 的LLM排行榜数据...")
        
        all_rankings = []
        
        # 收集所有排行榜数据
        for ranking_source in config.llm_rankings:
            try:
                if ranking_source['name'] == 'LMSYS Chatbot Arena':
                    ranking_data = self.fetch_lmsys_arena()
                elif ranking_source['name'] == 'Hugging Face Open LLM Leaderboard':
                    ranking_data = self.fetch_huggingface_leaderboard()
                elif ranking_source['name'] == 'Papers With Code Leaderboard':
                    ranking_data = self.fetch_paperswithcode_leaderboard()
                else:
                    self.logger.warning(f"未知的排行榜来源: {ranking_source['name']}")
                    continue
                
                if ranking_data:
                    all_rankings.append(ranking_data)
                
                # 避免请求过快
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"收集排行榜数据失败: {ranking_source['name']}, 错误: {str(e)}")
        
        # 保存数据
        for ranking in all_rankings:
            self.save_ranking_data(ranking, date)
        
        # 发送通知
        if all_rankings and config.notification['enabled']:
            self.send_notification(all_rankings, date)
        
        self.logger.info(f"完成收集，共获取 {len(all_rankings)} 个排行榜数据")
        
        return len(all_rankings)
    
    def send_notification(self, rankings: List[Dict], date: datetime):
        """发送通知"""
        self.logger.info("准备发送排行榜数据通知...")
        
        # 示例：简单的日志通知
        summary = f"LLM排行榜数据收集完成 - {date.strftime('%Y-%m-%d')}\n"
        summary += f"共收集到 {len(rankings)} 个排行榜数据\n"
        
        # 统计来源
        sources = {}
        for ranking in rankings:
            source = ranking['source']
            sources[source] = sources.get(source, 0) + 1
        
        summary += "\n来源统计:\n"
        for source, count in sources.items():
            summary += f"- {source}: {count} 个\n"
        
        self.logger.info(summary)

def main():
    """主函数"""
    collector = LLMRankingCollector()
    
    # 获取命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='LLM排行榜数据收集器')
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
    ranking_count = collector.collect_daily_rankings(date)
    print(f"收集完成，共获取 {ranking_count} 个排行榜数据")

if __name__ == "__main__":
    main()