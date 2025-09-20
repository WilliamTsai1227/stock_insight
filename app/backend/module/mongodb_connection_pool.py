from pymongo import MongoClient
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from pymongo.read_preferences import SecondaryPreferred
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDBConnectionPool:
    _instance = None
    _client = None
    _db_name = "stock_insight" 

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
                serverSelectionTimeoutMS=5000,
                read_preference=SecondaryPreferred()
            )

    def get_collection(self, collection_name: str):
        """    
        Args:
            collection_name (str): collection 名稱            
        Returns:
            Collection: MongoDB collection 物件
        """
        return self._client[self._db_name].get_collection(
            collection_name,
            write_concern=WriteConcern(w=1)   #
        )

    def get_database(self):
        """
        Returns:
            Database: MongoDB database 物件
        """
        return self._client.get_database(
            self._db_name,
            write_concern=WriteConcern(w=1)   #
        )

# 創建一個全局的連接池實例
mongodb_pool = MongoDBConnectionPool()

def get_news_data_db():
    return mongodb_pool.get_database()

def get_log_data_db():
    return mongodb_pool.get_database()

def get_ai_news_analysis_db():
    return mongodb_pool.get_database()