import os
import re
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


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
            print("成功連線到 MongoDB！")
        except Exception as e:
            print(f"MongoDB 連線失敗: {e}")
            _mongo_client = None # 重置客戶端以避免使用損壞的連線
            raise ConnectionError(f"無法建立 MongoDB 連線: {e}")
    return _mongo_client

def remove_invalid_keywords_from_ai_news(keywords_to_remove: list, db_name: str, collection_name: str) -> int:
    """
    查詢 MongoDB 中 AI 新聞相關文件，並從指定欄位內容中移除不合法的關鍵字。
    
    Args:
        keywords_to_remove (list): 包含要移除的「不合法」關鍵字的列表。
        db_name (str): 資料庫名稱。
        collection_name (str): 集合名稱。

    Returns:
        int: 被更新的文件數量。
    """
    client = None
    updated_count = 0
    try:
        client = get_mongo_client()
        db = client[db_name]
        collection = db[collection_name]

        or_conditions = []
        for keyword in keywords_to_remove:
            or_conditions.extend([
                {"summary": {"$regex": keyword, "$options": "i"}},
                {"important_news": {"$regex": keyword, "$options": "i"}},
                {"potential_stocks_and_industries": {"$regex": keyword, "$options": "i"}},
                {"sentiment": {"$regex": keyword, "$options": "i"}}
            ])
        
        query = {"$or": or_conditions} if or_conditions else {}
        if not query:
            print("沒有提供關鍵字進行查詢。")
            return 0

        print(f"正在查詢符合 '{', '.join(keywords_to_remove)}' 關鍵字的文件...")
        cursor = collection.find(query)

        for doc in cursor:
            doc_id = doc.get('_id')
            if not doc_id:
                print(f"警告：跳過沒有 _id 的文件: {doc}")
                continue

            update_fields = {}
            fields_to_check = ["summary", "important_news", "potential_stocks_and_industries", "sentiment"]

            for field in fields_to_check:
                if field in doc and isinstance(doc[field], str):
                    original_text = doc[field]
                    new_text = original_text
                    
                    for keyword in keywords_to_remove:
                        new_text = re.sub(re.escape(keyword), "", new_text, flags=re.IGNORECASE)
                    
                    if new_text != original_text:
                        update_fields[field] = new_text.strip() 

            if update_fields:
                result = collection.update_one(
                    {"_id": doc_id},
                    {"$set": update_fields}
                )
                if result.modified_count > 0:
                    updated_count += 1
                    print(f"文件 ID: {doc_id} 已更新。")
                else:
                    print(f"文件 ID: {doc_id} 未被修改 (可能在處理期間被其他操作更改或無實際變化)。")

    except ConnectionError as e: # 捕獲我們自定義的連線錯誤
        print(f"資料庫連線錯誤: {e}")
        return 0
    except Exception as e:
        print(f"操作時發生錯誤: {e}")
        return 0
    finally:
        if client:
            print("關閉 MongoDB 連線。") 
            client.close() 
    return updated_count



### **`lambda_handler` 函數 (Lambda 的入口點)**


def lambda_handler(event, context):
    """
    AWS Lambda 函數的入口點。
    """
    # 從 Lambda 環境變數中獲取資料庫和集合名稱
    database_name = os.getenv("DB_NAME")
    collection_name = os.getenv("COLLECTION_NAME")

    if not database_name or not collection_name:
        print("錯誤：環境變數 DB_NAME 或 COLLECTION_NAME 未設置。")
        return {
            'statusCode': 500,
            'body': 'Required environment variables are not set.'
        }

    
    # 可從 event 或其他來源獲取
    invalid_keywords_to_remove = ["建議關注", "持續關注", "值得關注", "推薦", "關注"]
    
    # 執行核心邏輯
    total_updated = remove_invalid_keywords_from_ai_news(
        invalid_keywords_to_remove, 
        database_name, 
        collection_name
    )

    if total_updated > 0:
        message = f"成功更新了 {total_updated} 個文件，移除了不合法關鍵字。"
        status_code = 200
    else:
        message = "沒有文件需要更新，或沒有找到符合條件的文件。"
        status_code = 200 

    print(message)
    return {
        'statusCode': status_code,
        'body': message
    }