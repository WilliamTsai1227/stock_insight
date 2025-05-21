from pymongo import MongoClient
import os

db_user = os.getenv('mongodb_user')
db_password = os.getenv('mongodb_password')
url = f"mongodb+srv://{db_user}:{db_password }@stock-main.kbyokcd.mongodb.net/?retryWrites=true&w=majority&appName=stock-main"

client = MongoClient(
    url,
    maxPoolSize=20,  # 最大連線數（預設是100）
    minPoolSize=5,   # 最小連線數（可選）
    serverSelectionTimeoutMS=5000  # 選擇主機逾時時間（毫秒）
)


def get_news_data_db():
    return client["news_data"]

def get_log_data_db():
    return client["log_data"]

def get_ai_news_analysis_db():
    return client["AI_news_analysis"]