"""
系统测试脚本 - 简化版
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
        
        print(f"[OK] 加载了 {len(sources)} 个新闻来源")
        print(f"[OK] 加载了 {len(rankings)} 个排行榜来源")
        print(f"[OK] 通知状态: {'启用' if notification['enabled'] else '禁用'}")
        print(f"[OK] 存储配置: {storage['format']} 格式, 最大保存 {storage['max_days']} 天")
        
        return True
    except Exception as e:
        print(f"[ERROR] 配置加载失败: {str(e)}")
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
                print(f"[OK] 目录存在: {dir_path}")
            else:
                print(f"[INFO] 目录不存在，将自动创建: {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)
        
        return True
    except Exception as e:
        print(f"[ERROR] 目录测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("开始测试AI技术资讯收集和推送系统...\n")
    
    # 测试配置
    config_ok = test_config()
    
    # 测试目录
    dir_ok = test_directories()
    
    # 汇总结果
    print("\n" + "="*50)
    print("测试结果汇总:")
    print("="*50)
    
    tests = [
        ("配置加载", config_ok),
        ("目录结构", dir_ok)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "[OK] 通过" if result else "[ERROR] 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(tests)} 项测试通过")
    
    if passed == len(tests):
        print("\n[SUCCESS] 基础测试通过！系统已准备就绪。")
        print("\n下一步:")
        print("1. 运行 'python main.py news' 测试新闻收集")
        print("2. 运行 'python main.py rankings' 测试排行榜收集")
        print("3. 运行 'setup_tasks.bat' 设置定时任务")
    else:
        print("\n[WARNING] 部分测试失败，请检查错误信息并修复问题。")

if __name__ == "__main__":
    main()