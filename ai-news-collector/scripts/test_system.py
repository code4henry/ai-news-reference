"""
系统测试脚本
"""
import sys
import os
from pathlib import Path
import datetime

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent / "config"))
from settings import config

def test_config():
    """测试配置加载"""
    print("测试配置加载...")
    try:
        sources = config.news_sources
        rankings = config.llm_rankings
        notification = config.notification
        storage = config.storage
        
        print(f"✓ 加载了 {len(sources)} 个新闻来源")
        print(f"✓ 加载了 {len(rankings)} 个排行榜来源")
        print(f"✓ 通知状态: {'启用' if notification['enabled'] else '禁用'}")
        print(f"✓ 存储配置: {storage['format']} 格式, 最大保存 {storage['max_days']} 天")
        
        return True
    except Exception as e:
        print(f"✗ 配置加载失败: {str(e)}")
        return False

def test_directories():
    """测试目录结构"""
    print("\n测试目录结构...")
    try:
        # 检查必要目录
        directories = [config.get_data_dir(), config.get_log_file().parent, 
                      Path(config.storage['backup_dir'])]
        
        for dir_path in directories:
            if dir_path.exists():
                print(f"✓ 目录存在: {dir_path}")
            else:
                print(f"! 目录不存在，将自动创建: {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)
        
        return True
    except Exception as e:
        print(f"✗ 目录测试失败: {str(e)}")
        return False

def test_news_collector():
    """测试新闻收集器"""
    print("\n测试新闻收集器...")
    try:
        from news_collector import NewsCollector
        
        collector = NewsCollector()
        
        # 测试获取一个来源的RSS
        if config.news_sources:
            test_source = config.news_sources[0]
            print(f"测试获取: {test_source['name']}")
            
            articles = collector.fetch_rss_feed(test_source)
            print(f"✓ 成功获取 {len(articles)} 篇文章")
            
            # 测试保存功能
            if articles:
                test_date = datetime.datetime.now()
                collector.save_articles(articles[:1], test_date)  # 只保存第一篇文章用于测试
                print("✓ 文章保存测试成功")
            
            return True
        else:
            print("✗ 没有配置新闻来源")
            return False
            
    except Exception as e:
        print(f"✗ 新闻收集器测试失败: {str(e)}")
        return False

def test_ranking_collector():
    """测试排行榜收集器"""
    print("\n测试排行榜收集器...")
    try:
        from llm_ranking_collector import LLMRankingCollector
        
        collector = LLMRankingCollector()
        
        # 测试获取LMSYS数据
        ranking_data = collector.fetch_lmsys_arena()
        if ranking_data:
            print(f"✓ 成功获取LMSYS数据: {ranking_data['source']}")
            
            # 测试保存功能
            test_date = datetime.datetime.now()
            collector.save_ranking_data(ranking_data, test_date)
            print("✓ 排行榜数据保存测试成功")
            
            return True
        else:
            print("✗ LMSYS数据获取失败")
            return False
            
    except Exception as e:
        print(f"✗ 排行榜收集器测试失败: {str(e)}")
        return False

def test_scheduler():
    """测试定时任务调度器"""
    print("\n测试定时任务调度器...")
    try:
        from task_scheduler import TaskScheduler
        
        scheduler = TaskScheduler()
        
        # 测试数据清理任务
        print("测试数据清理任务...")
        scheduler.cleanup_old_data_task()
        print("✓ 数据清理任务测试成功")
        
        # 测试备份任务
        print("测试数据备份任务...")
        scheduler.backup_data_task()
        print("✓ 数据备份任务测试成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 定时任务调度器测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("开始测试AI技术资讯收集和推送系统...\n")
    
    tests = [
        ("配置加载", test_config),
        ("目录结构", test_directories),
        ("新闻收集器", test_news_collector),
        ("排行榜收集器", test_ranking_collector),
        ("定时任务调度器", test_scheduler)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name}测试异常: {str(e)}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "="*50)
    print("测试结果汇总:")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("\n🎉 所有测试通过！系统已准备就绪。")
        print("\n下一步:")
        print("1. 运行 'python main.py news' 测试新闻收集")
        print("2. 运行 'python main.py rankings' 测试排行榜收集")
        print("3. 运行 'setup_tasks.bat' 设置定时任务")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息并修复问题。")

if __name__ == "__main__":
    main()