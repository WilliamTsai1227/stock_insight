import boto3
import json
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import BulkWriteError
import os
from datetime import datetime, timezone
import time



db_user = os.getenv('mongodb_user')
db_password = os.getenv('mongodb_password')

uri = f"mongodb+srv://{db_user}:{db_password}@stock-main.kbyokcd.mongodb.net/?retryWrites=true&w=2&appName=stock-main"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Log error to MongoDB
def log_error(log_type:str, message: str, additional_info: dict = None, source: str = None, db:str = None, collection:str = None):
    try:
        # Get current time
        current_time = datetime.now(timezone.utc)  # datetime UTC+0 with timezone=UTC
        current_time = int(time.time())
        # Prepare log entry
        log_entry = {
            "log_type": log_type,
            "message": message,
            "timestamp": current_time,
            "additional_info": additional_info or {},
            "source":source,
            "db":db,
            "collection":collection
        }
        # Insert log entry into MongoDB
        db = client["stock_insight"]
        collection = db["log"]
        collection.insert_one(log_entry)
        print(f"Error Log inserted into mongodb db:{db.name}/collection:{collection.name}")
    except Exception as e:
        print(f"Error logging to MongoDB an unexpected error occurred: {e}")
        raise e
    
# Log success to MongoDB
def log_success(log_type: str, message: str , additional_info: dict = None, source:str =None, db:str = None, collection:str = None):

    try:
        # Get current time
        current_time = datetime.now(timezone.utc)  # datetime UTC+0 with timezone=UTC
        current_time = int(time.time())
        # Prepare log entry
        log_entry = {
            "log_type": log_type,
            "source":source,
            "message": message,
            "timestamp": current_time,
            "additional_info": additional_info or None,
            "db":db,
            "collection":collection
        }
        # Insert log entry into MongoDB
        db = client["stock_insight"]
        collection = db["log"]
        collection.insert_one(log_entry)
        print(f"Success Log inserted into mongodb db:{db.name}/collection:{collection.name}")
    except Exception as e:
        print(f"Success logging to MongoDB an unexpected error occurred: {e}")
        raise e

def insert_data_mongodb(data_list: list[dict], insert_db:str, insert_collection:str, source:str):
    if not insert_db or not insert_collection:
        error_message = "No db and collection parameters were provided to the insert_data_mongodb() module"
        print(error_message)
        return
    if not isinstance(insert_db,str) or not isinstance(insert_collection,str):
        error_message = "The insert_db or insert_collection parameter passed to insert_data_mongodb() is not str data type"
        print(error_message)
        return
    try:
        db = client[insert_db]
        collection = db[insert_collection]
        if data_list:
            try:
                result = collection.insert_many(data_list, ordered=False)
                inserted_count = len(result.inserted_ids)  #The number of entries that were actually successfully inserted   
            except BulkWriteError as bwe:
                inserted_count = bwe.details.get('nInserted', 0)
                error_message = f"Bulk write warning: {bwe.details}"
            # Regardless of whether there is a unique key conflict, there will be correct log records
            success_message = f"成功將 {inserted_count} 筆資料插入 MongoDB 的 {insert_db}.{insert_collection} 集合。"
            print(success_message)
            log_success('news_insert_success',message=success_message, source=source, db=insert_db, collection=insert_collection) 
            
    except Exception as e:
        error_message = f"Insert mongodb fail: {e}"
        log_error('news_insert_error', message=error_message,db=insert_db,collection=insert_collection)
        raise e
   


def get_latest_s3_file(bucket_name, prefix):
    """
    從 S3 指定路徑下，取得最新建立的檔案。

    Args:
        bucket_name (str): S3 儲存桶名稱。
        prefix (str): 檔案路徑前綴 (例如: 'anue/headline/2025-09-10/')。

    Returns:
        str: 最新檔案的 Key（完整路徑），如果找不到則回傳 None。
    """
    s3_client = boto3.client('s3')

    # 列出所有符合前綴的物件
    response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix=prefix
    )

    # 如果沒有檔案，回傳 None
    if 'Contents' not in response:
        return None

    # 依據 'LastModified' 時間排序，取得最新檔案
    all_files = response['Contents']
    latest_file = max(all_files, key=lambda x: x['LastModified'])
    
    return latest_file['Key']


def process_and_insert_news():
    """
    這個函數負責整個流程：從 S3 讀取最新新聞並寫入 MongoDB。
    """
    # 定義你的 S3 儲存桶
    S3_BUCKET_NAME = "stock-insight-original-news-datalake"
    
    # 建立一個包含當天日期的前綴，用於搜尋當天資料夾
    today_prefix = f"anue/headline/{datetime.now().strftime('%Y-%m-%d')}/"

    try:
        # 找到當天最新的 S3 檔案路徑
        latest_file_key = get_latest_s3_file(S3_BUCKET_NAME, today_prefix)
        
        if not latest_file_key:
            errormessage = "當天沒有找到任何新聞檔案，無需處理。"
            print(errormessage)
            log_error(log_type="find_latest_news_error", message = errormessage)
            return
        success_message = f"找到當天最新的檔案: {latest_file_key}"
        print(f"找到當天最新的檔案: {latest_file_key}")
        log_success('find_latest_news_success',message=success_message, source="s3") 

        # 讀取這個最新檔案的內容
        s3_client = boto3.client('s3')
        obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=latest_file_key)
        data = obj['Body'].read().decode('utf-8')
        
        # 將 JSON 字串轉換為 Python 物件
        news_data_list = json.loads(data)
        
        print(f"成功讀取 {len(news_data_list)} 筆新聞資料。")
        
       
        insert_data_mongodb(
            news_data_list, 
            insert_db="stock_insight", 
            insert_collection="news", 
            source="anue"
        )
        
        print("資料處理與寫入 MongoDB 成功！")

    except Exception as e:
        print(f"處理 S3 檔案或寫入 MongoDB 時發生錯誤: {e}")
        raise # 重新拋出異常，讓 Lambda 知道執行失敗

def lambda_handler(event, context):
    """
    Lambda 服務的進入點
    """
    try:
        process_and_insert_news()
        return {
            "statusCode": 200,
            "body": "新聞資料S3 檔案寫入 MongoDB處理成功"
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"處理失敗: {str(e)}"
        }

# 如果在本地端執行，可以使用這個區塊
if __name__ == "__main__":
    process_and_insert_news()