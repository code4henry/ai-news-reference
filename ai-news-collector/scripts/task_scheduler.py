"""
定时任务管理脚本
"""
import schedule
import time
import logging
from datetime import datetime, timedelta
import argparse
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent / "config"))
from settings import config

class TaskScheduler:
    def __init__(self):
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger('TaskScheduler')
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
    
    def collect_news_task(self):
        """新闻收集任务"""
        self.logger.info("开始执行新闻收集任务...")
        
        try:
            # 导入新闻收集器
            from news_collector import NewsCollector
            
            collector = NewsCollector()
            article_count = collector.collect_daily_news()
            
            self.logger.info(f"新闻收集任务完成，共获取 {article_count} 篇文章")
            
        except Exception as e:
            self.logger.error(f"新闻收集任务失败: {str(e)}")
    
    def collect_rankings_task(self):
        """排行榜收集任务"""
        self.logger.info("开始执行排行榜收集任务...")
        
        try:
            # 导入排行榜收集器
            from llm_ranking_collector import LLMRankingCollector
            
            collector = LLMRankingCollector()
            ranking_count = collector.collect_daily_rankings()
            
            self.logger.info(f"排行榜收集任务完成，共获取 {ranking_count} 个排行榜数据")
            
        except Exception as e:
            self.logger.error(f"排行榜收集任务失败: {str(e)}")
    
    def cleanup_old_data_task(self):
        """清理旧数据任务"""
        self.logger.info("开始执行数据清理任务...")
        
        try:
            # 计算清理截止日期
            max_days = config.storage.get('max_days', 30)
            cutoff_date = datetime.now() - timedelta(days=max_days)
            
            # 遍历数据目录
            data_dir = config.get_data_dir()
            if data_dir.exists():
                for year_month_dir in data_dir.iterdir():
                    if year_month_dir.is_dir():
                        # 检查是否需要清理该月的数据
                        try:
                            # 尝试解析目录名 (YYYY-MM)
                            year, month = year_month_dir.name.split('-')
                            dir_date = datetime(int(year), int(month), 1)
                            
                            if dir_date < cutoff_date:
                                self.logger.info(f"清理旧数据目录: {year_month_dir}")
                                
                                # 删除目录及其内容
                                import shutil
                                shutil.rmtree(year_month_dir)
                                
                        except ValueError:
                            # 目录名不是日期格式，跳过
                            continue
            
            self.logger.info("数据清理任务完成")
            
        except Exception as e:
            self.logger.error(f"数据清理任务失败: {str(e)}")
    
    def backup_data_task(self):
        """备份数据任务"""
        self.logger.info("开始执行数据备份任务...")
        
        try:
            backup_enabled = config.storage.get('backup_enabled', True)
            if not backup_enabled:
                self.logger.info("数据备份已禁用")
                return
            
            backup_dir = Path(config.storage.get('backup_dir', './backup'))
            backup_dir.mkdir(exist_ok=True)
            
            # 创建备份文件名
            backup_file = backup_dir / f"ai_news_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
            
            # 备份数据目录
            data_dir = config.get_data_dir()
            if data_dir.exists():
                import shutil
                
                # 创建临时备份目录
                temp_backup = Path(f"temp_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                shutil.copytree(data_dir, temp_backup)
                
                # 压缩备份
                shutil.make_archive(str(backup_file).replace('.tar.gz', ''), 'gztar', temp_backup)
                
                # 删除临时目录
                shutil.rmtree(temp_backup)
                
                self.logger.info(f"数据备份完成: {backup_file}")
            else:
                self.logger.warning("数据目录不存在，跳过备份")
                
        except Exception as e:
            self.logger.error(f"数据备份任务失败: {str(e)}")
    
    def setup_schedules(self):
        """设置定时任务"""
        # 每天早上8点收集新闻
        schedule.every().day.at("08:00").do(self.collect_news_task)
        
        # 每天中午12点收集排行榜数据
        schedule.every().day.at("12:00").do(self.collect_rankings_task)
        
        # 每天凌晨2点清理旧数据
        schedule.every().day.at("02:00").do(self.cleanup_old_data_task)
        
        # 每周日凌晨3点备份数据
        schedule.every().sunday.at("03:00").do(self.backup_data_task)
        
        self.logger.info("定时任务设置完成")
        self.logger.info("- 新闻收集: 每天 08:00")
        self.logger.info("- 排行榜收集: 每天 12:00")
        self.logger.info("- 数据清理: 每天 02:00")
        self.logger.info("- 数据备份: 每周日 03:00")
    
    def run_scheduler(self):
        """运行定时任务调度器"""
        self.logger.info("启动定时任务调度器...")
        
        # 设置定时任务
        self.setup_schedules()
        
        # 主循环
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
                
            except KeyboardInterrupt:
                self.logger.info("收到中断信号，停止调度器")
                break
            except Exception as e:
                self.logger.error(f"调度器运行错误: {str(e)}")
                time.sleep(60)
    
    def run_once(self, task_type):
        """立即执行指定任务"""
        self.logger.info(f"立即执行任务: {task_type}")
        
        if task_type == 'news':
            self.collect_news_task()
        elif task_type == 'rankings':
            self.collect_rankings_task()
        elif task_type == 'cleanup':
            self.cleanup_old_data_task()
        elif task_type == 'backup':
            self.backup_data_task()
        else:
            self.logger.error(f"未知任务类型: {task_type}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI资讯定时任务管理器')
    parser.add_argument('--run', choices=['news', 'rankings', 'cleanup', 'backup'], 
                       help='立即执行指定任务')
    parser.add_argument('--daemon', action='store_true', 
                       help='以守护进程模式运行定时任务')
    args = parser.parse_args()
    
    scheduler = TaskScheduler()
    
    if args.run:
        # 立即执行任务
        scheduler.run_once(args.run)
    elif args.daemon:
        # 守护进程模式
        scheduler.run_scheduler()
    else:
        print("请指定操作: --run [任务类型] 或 --daemon")

if __name__ == "__main__":
    main()