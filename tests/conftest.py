"""
conftest.py - 共用測試配置及fixture
此檔案通常放在tests目錄下，提供共用測試設定和fixture供所有測試使用
"""
import pytest
from pymongo import MongoClient
import logging
from datetime import datetime

# 全域測試配置
def pytest_configure(config):
    """測試開始前的全域設定"""
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler()
        ]
    )

@pytest.fixture(scope="session")
def mongodb_client():
    """建立MongoDB連接，整個測試會話只建立一次"""
    client = MongoClient('mongodb://localhost:27017/')
    yield client
    client.close()

@pytest.fixture(scope="session")
def stock_insight_db(mongodb_client):
    """取得stock_insight資料庫"""
    return mongodb_client['stock_insight']

@pytest.fixture(scope="session")
def ai_news_collection(stock_insight_db):
    """取得AI_news_analysis集合"""
    return stock_insight_db['AI_news_analysis']

@pytest.fixture(scope="session")
def ai_news_documents(ai_news_collection):
    """取得所有AI新聞分析文檔"""
    return list(ai_news_collection.find())