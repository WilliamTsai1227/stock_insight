import boto3
import datetime
import json

# 假設這是你原本的 MongoDB 寫入函數，你應該把它放在 Lambda Layer 或專案中
# 從 crawler_module.insert_data 匯入
def insert_data_mongodb(data_list, insert_db, insert_collection, source):
    """
    這個函數的實作細節需要由你提供。
    它會接收一個新聞字典的列表，並將其插入到指定的 MongoDB 資料庫和集合中。
    """
    # 這裡放你的 MongoDB 連接與寫入邏輯
    # 例如：
    # from pymongo import MongoClient
    # client = MongoClient('your_mongodb_connection_string')
    # db = client[insert_db]
    # collection = db[insert_collection]
    # collection.insert_many(data_list)
    print(f"成功將 {len(data_list)} 筆資料插入 MongoDB 的 {insert_db}.{insert_collection} 集合。")


def get_latest_s3_file(bucket_name, prefix):
    """
    從 S3 指定路徑下，取得最新建立的檔案。

    Args:
        bucket_name (str): S3 儲存桶名稱。
        prefix (str): 檔案路徑前綴 (例如: 'anue/headline/2025/09/10/')。

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
    today_prefix = f"anue/headline/{datetime.datetime.now().strftime('%Y/%m/%d')}/"

    try:
        # 1. 找到當天最新的 S3 檔案路徑
        latest_file_key = get_latest_s3_file(S3_BUCKET_NAME, today_prefix)
        
        if not latest_file_key:
            print("當天沒有找到任何新聞檔案，無需處理。")
            return
        
        print(f"找到當天最新的檔案: {latest_file_key}")
        
        # 2. 讀取這個最新檔案的內容
        s3_client = boto3.client('s3')
        obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=latest_file_key)
        data = obj['Body'].read().decode('utf-8')
        
        # 3. 將 JSON 字串轉換為 Python 物件
        news_data_list = json.loads(data)
        
        print(f"成功讀取 {len(news_data_list)} 筆新聞資料。")
        
        # 4. 呼叫你的 MongoDB 寫入函數
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
            "body": "新聞資料處理與寫入成功"
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"處理失敗: {str(e)}"
        }

# 如果在本地端執行，可以使用這個區塊
if __name__ == "__main__":
    process_and_insert_news()