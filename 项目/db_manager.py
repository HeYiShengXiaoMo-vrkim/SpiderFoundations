import os
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger("cnki_spider.db")

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """连接到数据库"""
        try:
            # 使用SQLite数据库
            db_path = self.config.get('path', 'cnki_documents.db')
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"已连接到SQLite数据库: {db_path}")
                
            self.cursor = self.conn.cursor()
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def create_tables(self):
        """创建必要的表结构"""
        try:
            # 文档表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                source TEXT,
                publish_date TEXT,
                file_path TEXT,
                file_type TEXT,
                url TEXT,
                download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER,
                status TEXT DEFAULT 'downloaded'
            )
            ''')
            
            # 关键词表，用于记录搜索历史
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                result_count INTEGER
            )
            ''')
            
            self.conn.commit()
            logger.info("数据库表结构已创建")
        except Exception as e:
            logger.error(f"创建表结构失败: {e}")
            raise
    
    def insert_document(self, doc_info):
        """
        将文档信息插入数据库
        doc_info: 包含文档信息的字典
        """
        try:
            # 提取文件类型和大小
            file_path = doc_info.get('local_path')
            file_type = None
            file_size = None
            
            if file_path and os.path.exists(file_path):
                file_ext = os.path.splitext(file_path)[1].lower()
                file_type = file_ext[1:] if file_ext.startswith('.') else file_ext
                file_size = os.path.getsize(file_path)
            
            # 准备SQL和参数
            sql = '''
            INSERT INTO documents 
            (title, authors, source, publish_date, url, file_path, file_type, file_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            params = (
                doc_info.get('title', ''),
                doc_info.get('authors', ''),
                doc_info.get('source', ''),
                doc_info.get('date', ''),
                doc_info.get('link', ''),
                file_path,
                file_type,
                file_size
            )
            
            self.cursor.execute(sql, params)
            self.conn.commit()
            logger.info(f"文档信息已添加到数据库: {doc_info.get('title')}")
            return True
        except Exception as e:
            logger.error(f"插入文档信息失败: {e}")
            self.conn.rollback()
            return False
    
    def get_all_documents(self):
        """获取所有文档记录"""
        try:
            self.cursor.execute("SELECT * FROM documents")
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"获取文档记录失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")