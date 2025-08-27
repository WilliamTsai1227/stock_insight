import os
import json
from pymongo import MongoClient,UpdateOne
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta, timezone
import logging

# 設置日誌
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 全局 MongoDB 客戶端變數
_mongo_client = None

def get_mongo_client():
    """獲取 MongoDB 客戶端連線。如果已存在則重用，否則新建。"""
    global _mongo_client
    if _mongo_client is None:
        uri = os.getenv("MONGODB_STOCK_INSIGHT_PROJECT_URI")
        if not uri:
            raise ValueError("錯誤：環境變數 MONGODB_STOCK_INSIGHT_PROJECT_URI 未設置。")
        try:
            _mongo_client = MongoClient(uri, server_api=ServerApi('1'))
            # 測試連線
            _mongo_client.admin.command('ping')
            logger.info("成功連線到 MongoDB！")
        except Exception as e:
            logger.error(f"MongoDB 連線失敗: {e}")
            _mongo_client = None # 重置客戶端以避免使用損壞的連線
            raise ConnectionError(f"無法建立 MongoDB 連線: {e}")
    return _mongo_client


def lambda_handler(event, context):
    """
    Lambda 的主入口點。
    從檔案載入股票代碼對應表，查詢並校正過去三小時內的 MongoDB 資料。
    """
    try:
        # 載入 stock_symbols.json 檔案
        with open("stock_symbols.json", "r", encoding="utf-8") as f:
            stock_symbols = json.load(f)
        logger.info("成功載入 stock_symbols.json。")

        # 獲取 MongoDB 客戶端
        client = get_mongo_client()
        db = client['stock_insight']  # 請確保這是你的資料庫名稱
        collection = db['AI_news_analysis'] # 請替換成你的集合名稱

        # 設定查詢時間範圍：從現在起往前回溯三小時
        #current_time_utc = datetime.now(timezone.utc)
        current_time_utc = datetime(2025, 6, 20, 17, 0, 0, tzinfo=timezone.utc)
        three_hours_ago = current_time_utc - timedelta(hours=3)
        query = {
            "publishAt": {
                "$gte": int(three_hours_ago.timestamp())
            }
        }
        
        updates = []
        
        # 遍歷符合條件的文件
        for doc in collection.find(query):
            doc_id = doc['_id']
            stock_list = doc.get("stock_list", [])
            
            is_modified = False
            for item in stock_list:
                if len(item) == 3 and item[0] == "tw":
                    company_name = item[2]
                    original_symbol = item[1]
                    
                    if company_name in stock_symbols:
                        correct_symbol = stock_symbols[company_name]
                        
                        # 檢查股票代碼是否需要校正
                        if original_symbol != correct_symbol:
                            logger.warning(f"文件 ID: {doc_id} 的 '{company_name}' 股票代碼不符。")
                            logger.warning(f"原始代碼: {original_symbol}, 正確代碼: {correct_symbol}")
                            item[1] = correct_symbol
                            is_modified = True
            
            # 如果有任何修改，就將這份文件的更新操作加入批次更新列表
            if is_modified:
                updates.append(
                    pymongo.UpdateOne(
                        {"_id": doc_id},
                        {"$set": {"stock_list": stock_list}}
                    )
                )

        if updates:
            # 執行批次更新
            result = collection.bulk_write(updates)
            logger.info(f"成功更新 {result.modified_count} 份文件。")
        else:
            logger.info("沒有需要校正的文件。")

        return {
            'statusCode': 200,
            'body': json.dumps('校正腳本執行完成。')
        }

    except Exception as e:
        logger.error(f"發生未預期錯誤: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'腳本執行失敗: {e}')
        }