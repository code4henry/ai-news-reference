"""
系统配置文件
"""
import os
import yaml
from datetime import datetime
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
SCRIPTS_DIR = BASE_DIR / "scripts"

# 确保目录存在
for dir_path in [DATA_DIR, LOGS_DIR, SCRIPTS_DIR]:
    dir_path.mkdir(exist_ok=True)

# 加载配置文件
def load_config():
    config_path = CONFIG_DIR / "news_sources.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# 通用配置
class Config:
    def __init__(self):
        self.config = load_config()
        
    @property
    def news_sources(self):
        return self.config['news_sources']
    
    @property
    def llm_rankings(self):
        return self.config['llm_rankings']
    
    @property
    def notification(self):
        return self.config['notification']
    
    @property
    def storage(self):
        return self.config['storage']
    
    def get_data_dir(self, date=None):
        if date:
            return DATA_DIR / date.strftime("%Y-%m")
        return DATA_DIR
    
    def get_log_file(self, date=None):
        if date is None:
            date = datetime.now()
        return LOGS_DIR / f"ai_news_{date.strftime('%Y-%m-%d')}.log"
    
    def get_daily_file(self, date=None):
        if date is None:
            date = datetime.now()
        return self.get_data_dir(date) / f"ai_news_{date.strftime('%Y-%m-%d')}.md"

# 全局配置实例
config = Config()