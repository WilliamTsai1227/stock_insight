import urllib.request
import json
import datetime
import time
import boto3

# 這個是放在本身 function 裡的 Tidy
# from local_module.tidy_data import Tidy
from local_module.tidy_data import Tidy

# 這個是放在 Lambda Layer 裡的共用 insert_data / logger
from crawler_module.insert_data import insert_data_mongodb
from crawler_module.logger import log_error, LogType

S3_BUCKET_NAME = "stock-insight-original-news-datalake"
base_url = "https://api.cnyes.com/media/api/v1/newslist/category/headline"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Origin": "https://news.cnyes.com"
}
limit = 30

def crawl_news():
    page = 1
    actual_count = 0
    
    db_all_news = []

    # Try to get the last_page and total number 
    try:
        url = f"{base_url}?page={page}&limit={limit}&showOutsource=1"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                last_page = data["items"]["last_page"]
                pages_to_crawl = (last_page + 2) // 3   # Get the first 1/3 of the page
                total_from_api = data["items"]["total"]
            else:
                raise Exception(f"Unexpected status code: {response.status}")
    except Exception as e:
        raise Exception(f"[錯誤] 無法取得初始頁面資料：{e}")
    
    # into page process
    while page <= pages_to_crawl:
        url = f"{base_url}?page={page}&limit={limit}&showOutsource=1"
        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req) as response:
                if response.status != 200:
                    raise Exception(f"Unexpected status code: {response.status}")
                page_data = json.loads(response.read().decode())
        except Exception as e:
            print(f"[錯誤] 第 {page} 頁獲取失敗：{e}")
            page += 1
            continue

        try:
            news_items = page_data["items"]["data"]
        except KeyError:
            print(f"[錯誤] 第 {page} 頁資料格式不正確")
            page += 1
            continue

        db_news = Tidy.db_news_items(news_items)
        db_all_news.extend(db_news)

        actual_count += len(db_news)
        page += 1
        time.sleep(0.3)

    # insert news in mongodb
    try:
        # insert_data_mongodb(db_all_news, insert_db="stock_insight", insert_collection="news", source="anue")
        news_json_string = json.dumps(db_all_news, ensure_ascii=False, indent=2)

        # 建立 S3 檔案路徑，建議加上日期和時間，以避免覆蓋
        now = datetime.datetime.now()
        file_path = f"anue/headline/{now.strftime('%Y/%m/%d')}/{now.strftime('%H-%M-%S')}.json"
        
        # 建立 S3 客戶端
        s3_client = boto3.client("s3")
        
        # 上傳檔案至 S3
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_path,
            Body=news_json_string.encode("utf-8"),
            ContentType="application/json"
        )
        print(f"成功將資料上傳至 S3: s3://{S3_BUCKET_NAME}/{file_path}")
    except Exception as e:
        error_message = f"insert_data_mongodb() module fail: {e}"
        log_error(log_type=LogType.CRAWLER_ERROR, error_message=error_message, source="crawler_anue/headline_news")
        raise

def lambda_handler(event, context):
    try:
        crawl_news()
        success_message = "Anue鉅亨網爬蟲執行成功"
        print(success_message)
        return {
            "statusCode": 200,
            "body": "爬蟲執行成功"
        }
    except Exception as e:
        error_message = f"Anue鉅亨網爬蟲執行失敗: {e}"
        print(error_message)
        return {
            "statusCode": 500,
            "body": f"爬蟲執行失敗: {str(e)}"
        }


if __name__ == "__main__":
    crawl_news()
