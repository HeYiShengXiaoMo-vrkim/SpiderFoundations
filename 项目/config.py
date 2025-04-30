import os
import json
import logging

logger = logging.getLogger("cnki_spider.config")

class Config:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        
        # 默认配置
        self.username = ""
        self.password = ""
        self.download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
        self.headless = False
        self.max_pages = 3
        self.max_downloads_per_keyword = 5
        self.search_filters = {
            "document_type": ["cjfq", "cdmd"]  # 期刊和学位论文
        }
        self.keywords_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keywords.txt")
        self.db_config = {
            "path": "cnki_documents.db"
        }
        
        # 尝试加载用户配置
        self.load_config()
    
    def load_config(self):
        """从配置文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # 更新配置
                for key, value in user_config.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                
                logger.info(f"已从{self.config_file}加载配置")
            else:
                self.create_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置文件"""
        try:
            config_data = {
                "username": self.username,
                "password": self.password,
                "download_dir": self.download_dir,
                "headless": self.headless,
                "max_pages": self.max_pages,
                "max_downloads_per_keyword": self.max_downloads_per_keyword,
                "search_filters": self.search_filters,
                "keywords_file": self.keywords_file,
                "db_config": self.db_config
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
                
            logger.info(f"已创建默认配置文件: {self.config_file}")
        except Exception as e:
            logger.error(f"创建默认配置文件失败: {e}")