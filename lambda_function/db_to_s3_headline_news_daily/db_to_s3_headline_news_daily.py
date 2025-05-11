from lambda_layer.db_data_utils.fetch_data import get_news
from lambda_layer.log_utils.logger import log_error,log_success
import boto3
import json
import pandas as pd
from datetime import datetime,timedelta, timezone
import io
import re
import os

if os.getenv("AWS_EXECUTION_ENV") is None:
    from dotenv import load_dotenv
    load_dotenv()

def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id = os.getenv("aws_s3_access_key_id"),
        aws_secret_access_key = os.getenv("aws_s3_secret_access_key"),
        region_name="us-west-2"
    )

def get_today_max_version(bucket_name, prefix_date=None):
    """取得今天該 prefix 下最大的版本號"""
    s3 = get_s3_client()
    
    if prefix_date is None:
        prefix_date = datetime.now().strftime("headline_daily/headline_news_%Y%m%d")  # e.g., headline_news_20250501

    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix_date)
    max_version = 0

    if 'Contents' in response:
        for obj in response['Contents']:
            key = obj['Key']
            match = re.search(rf"{prefix_date}_v(\d+)\.json", key)
            if match:
                version = int(match.group(1))
                if version > max_version:
                    max_version = version
    return max_version  # 0 表示目前沒有任何檔案

def get_next_write_key(bucket_name):
    """產生今天該寫入的版本名稱（v1, v2, ...）"""
    prefix_date = datetime.now().strftime("headline_daily/headline_news_%Y%m%d")
    max_version = get_today_max_version(bucket_name, prefix_date)
    next_version = max_version + 1
    return f"{prefix_date}_v{next_version}.json"

def normalize_news(news_list: list[dict]) -> pd.DataFrame:
    df = pd.json_normalize(news_list)
    df["_id"] = df["_id"].astype(str)
    df.drop(columns=["news_id", "type","url"], inplace=True) #把原始新聞URL先移除，點擊跳轉到我的網站新聞頁面再顯示原始url
    return df

def news_to_json_and_upload(news_list: list[dict], bucket: str = None, key: str = None):
    df = normalize_news(news_list)
    # 將 DataFrame 轉為 JSON Lines 格式 (每行一筆 JSON)
    json_lines = df.to_dict(orient="records")
    json_str = "\n".join(json.dumps(line, ensure_ascii=False) for line in json_lines)
    
    buffer = io.BytesIO(json_str.encode("utf-8"))

    s3 = get_s3_client()
    s3.upload_fileobj(buffer, bucket, key)


def lambda_handler(event, context):
    try:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=4, minutes=10)

        start_ts = int(start_time.timestamp())
        end_ts = int(end_time.timestamp())
        news = get_news(start_ts, end_ts, db_name="news_data", collection_name="headline_news")

        key = get_next_write_key("stock-insight-news-datalake")
        news_to_json_and_upload(news, bucket="stock-insight-news-datalake", key=key)
        successful_message = f"共取得 {len(news)} 筆新聞資料，已上傳至 S3：{key}"
        result = {
            "statusCode": 200,
            "body": successful_message
        }
        log_success("db_to_s3_success","daily",successful_message,source="lambda_function/db_to_s3_headline_news_daily.py")
        return result
    except Exception as e:
        error_message = f"db to s3 daily error:{e}"
        log_error("db_to_s3_error","daily",error_message,source="lambda_function/db_to_s3_headline_news_daily.py")
        result = {
            "statusCode": 500,
            "body": error_message
        }
        print(result)
        return result
    



if __name__ == "__main__":
    result = lambda_handler({}, {})
    print(json.dumps(result, ensure_ascii=False, indent=2))


