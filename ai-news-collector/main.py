"""
AI技术资讯收集和推送系统主程序
"""
import argparse
import sys
from pathlib import Path
import datetime

# 添加scripts目录到路径
sys.path.append(str(Path(__file__).parent / "scripts"))

def show_help():
    """显示帮助信息"""
    help_text = """
AI技术资讯收集和推送系统

使用方法:
    python main.py <command> [options]

命令:
    news              收集AI技术资讯
    rankings          收集LLM排行榜数据
    scheduler         启动定时任务调度器
    backup            备份数据
    cleanup           清理旧数据
    help              显示帮助信息

选项:
    --date YYYY-MM-DD 指定日期 (仅限news和rankings命令)

示例:
    python main.py news                           # 收集今天的资讯
    python main.py news --date 2026-05-31          # 收集指定日期的资讯
    python main.py rankings                       # 收集排行榜数据
    python main.py scheduler                       # 启动定时任务
    python main.py scheduler --daemon              # 以守护进程模式运行
    python main.py backup                         # 备份数据
    python main.py cleanup                        # 清理旧数据
"""
    print(help_text)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI技术资讯收集和推送系统', add_help=False)
    parser.add_argument('command', nargs='?', help='命令')
    parser.add_argument('--date', help='指定日期 (YYYY-MM-DD)')
    args = parser.parse_args()
    
    if not args.command or args.command == 'help':
        show_help()
        return
    
    try:
        if args.command == 'news':
            # 导入并执行新闻收集
            from news_collector import NewsCollector
            collector = NewsCollector()
            
            # 解析日期
            date = None
            if args.date:
                date = datetime.datetime.strptime(args.date, '%Y-%m-%d')
            
            article_count = collector.collect_daily_news(date)
            print(f"✓ 新闻收集完成，共获取 {article_count} 篇文章")
            
        elif args.command == 'rankings':
            # 导入并执行排行榜收集
            from llm_ranking_collector import LLMRankingCollector
            collector = LLMRankingCollector()
            
            # 解析日期
            date = None
            if args.date:
                date = datetime.datetime.strptime(args.date, '%Y-%m-%d')
            
            ranking_count = collector.collect_daily_rankings(date)
            print(f"✓ 排行榜收集完成，共获取 {ranking_count} 个排行榜数据")
            
        elif args.command == 'scheduler':
            # 导入并执行定时任务
            from task_scheduler import TaskScheduler
            scheduler = TaskScheduler()
            
            if len(sys.argv) > 2 and sys.argv[2] == '--daemon':
                scheduler.run_scheduler()
            else:
                print("使用 --daemon 参数以守护进程模式运行定时任务")
                print("或者使用以下命令立即执行各个任务:")
                print("  python main.py news")
                print("  python main.py rankings")
                print("  python main.py backup")
                print("  python main.py cleanup")
            
        elif args.command == 'backup':
            # 导入并执行备份
            from task_scheduler import TaskScheduler
            scheduler = TaskScheduler()
            scheduler.backup_data_task()
            print("✓ 数据备份完成")
            
        elif args.command == 'cleanup':
            # 导入并执行清理
            from task_scheduler import TaskScheduler
            scheduler = TaskScheduler()
            scheduler.cleanup_old_data_task()
            print("✓ 数据清理完成")
            
        else:
            print(f"未知命令: {args.command}")
            show_help()
            
    except Exception as e:
        print(f"执行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()