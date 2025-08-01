from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDBConnectionPool:
    _instance = None
    _client = None
    _db_name = "stock_insight"  # 固定使用 stock_insight 資料庫

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnectionPool, cls).__new__(cls)
            cls._instance._initialize_client()
        return cls._instance

    def _initialize_client(self):
        if self._client is None:
            db_user = os.getenv('mongodb_user')
            db_password = os.getenv('mongodb_password')
            url = f"mongodb+srv://{db_user}:{db_password}@stock-main.kbyokcd.mongodb.net/?retryWrites=true&w=majority&appName=stock-main"
            
            self._client = MongoClient(
                url,
                maxPoolSize=20,
                minPoolSize=5,
                serverSelectionTimeoutMS=5000
            )

    def get_collection(self, collection_name: str):
        """
        獲取指定的 collection
        
        Args:
            collection_name (str): collection 名稱
            
        Returns:
            Collection: MongoDB collection 物件
        """
        return self._client[self._db_name][collection_name]

    def get_database(self):
        """
        獲取資料庫實例
        
        Returns:
            Database: MongoDB database 物件
        """
        return self._client[self._db_name]

# 創建一個全局的連接池實例
mongodb_pool = MongoDBConnectionPool()

def get_news_data_db():
    return mongodb_pool.get_database()

def get_log_data_db():
    return mongodb_pool.get_database()

def get_ai_news_analysis_db():
    return mongodb_pool.get_database()