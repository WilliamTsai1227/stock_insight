import urllib.request
import json
import datetime
import time

# 這個是放在本身 function 裡的 Tidy
# from local_module.tidy_data import Tidy
from crawler_anue.local_module.tidy_data import Tidy

# 這個是放在 Lambda Layer 裡的共用 insert_data / logger
from crawler_module.insert_data import insert_data_mongodb
from crawler_module.logger import log_error, LogType

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
                total_from_api = data["items"]["total"]
            else:
                raise Exception(f"Unexpected status code: {response.status}")
    except Exception as e:
        raise Exception(f"[錯誤] 無法取得初始頁面資料：{e}")
    
    # into page process
    while page <= last_page:
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
        insert_data_mongodb(db_all_news, insert_db="news_data", insert_collection="headline_news", source="anue")
    except Exception as e:
        error_message = f"insert_data_mongodb() module fail: {e}"
        log_error(log_type=LogType.CRAWLER_ERROR, error_message=error_message, source="crawler_anue/headline_news")
        raise

def lambda_handler(event, context):
    try:
        crawl_news()
        success_message = "Anue鉅亨網爬蟲執行成功"
        print(success_message)# <=== 加這一行，讓 CloudWatch Log 有記錄
        return {
            "statusCode": 200,
            "body": "爬蟲執行成功"
        }
    except Exception as e:
        error_message = "Anue鉅亨網爬蟲執行失敗"
        print(error_message)# <=== 加這一行，讓 CloudWatch Log 有記錄
        return {
            "statusCode": 500,
            "body": f"爬蟲執行失敗: {str(e)}"
        }


if __name__ == "__main__":
    crawl_news()
