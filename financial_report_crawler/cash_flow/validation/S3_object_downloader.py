import os
import json
import boto3
import re
import argparse
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime

# 載入 .env 檔案中的環境變數
load_dotenv()

# --- 配置區塊 ---
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
S3_BUCKET_NAME = os.environ.get('Financial_Report_S3_BUCKET_NAME')
S3_RAW_DATA_PREFIX = os.environ.get('Financial_Report_S3_RAW_DATA_PREFIX', 'raw-data/cash_flow/') # 確保以斜線結尾

# S3 憑證 (請確保這些變數在您的 .env 檔案中正確設定)
AWS_S3_ACCESS_KEY_ID = os.getenv('aws_s3_access_key_id')
AWS_S3_SECRET_ACCESS_KEY = os.getenv('aws_s3_secret_access_key')

# --- 函式區塊 ---
def list_s3_objects_sorted_by_date(bucket_name, prefix=None, top_n=1000):
    """
    列出 S3 儲存桶中指定前綴下的物件，並依據最後修改時間從最新到最舊排序，
    只返回前 N 個物件。
    """
    s3_client = boto3.client(
        's3',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_S3_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_S3_SECRET_ACCESS_KEY
    )
    objects = []

    # 遍歷所有物件 (處理分頁)
    paginator = s3_client.get_paginator('list_objects_v2')
    
    # 構建分頁參數
    pagination_params = {'Bucket': bucket_name}
    if prefix:
        pagination_params['Prefix'] = prefix

    pages = paginator.paginate(**pagination_params)

    for page in pages:
        if "Contents" in page:
            for obj in page["Contents"]:
                # 排除資料夾本身 (S3 將空資料夾視為一個 0-byte 物件，其 Key 以 / 結尾)
                if obj['Key'].endswith('/'):
                    continue
                objects.append(obj)

    # 根據 LastModified 時間排序，從最新到最舊
    # obj['LastModified'] 是一個 datetime 物件，可以直接比較
    sorted_objects = sorted(objects, key=lambda x: x['LastModified'], reverse=True)

    # 只取前 N 個物件
    top_n_objects = sorted_objects[:top_n]

    print(f"S3 儲存桶 '{bucket_name}' (前綴: '{prefix if prefix else '無'}' ) 中最新上傳的 {len(top_n_objects)} 個物件:")
    print("-" * 70)
    for obj in top_n_objects:
        key = obj['Key']
        last_modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S') # 格式化時間
        size_kb = obj['Size'] / 1024 if obj['Size'] else 0 # 轉換為 KB
        print(f"名稱: {key:<60} 最後修改: {last_modified} 大小: {size_kb:8.2f} KB")
    print("-" * 70)

# --- 使用範例 ---
if __name__ == "__main__":
    if not S3_BUCKET_NAME:
        print("錯誤：請在 .env 檔案中設定 'Financial_Report_S3_BUCKET_NAME'。")
    elif not AWS_S3_ACCESS_KEY_ID or not AWS_S3_SECRET_ACCESS_KEY:
        print("錯誤：請在 .env 檔案中設定 'aws_s3_access_key_id' 和 'aws_s3_secret_access_key'。")
    else:
        print(f"正在連線至 AWS 區域: {AWS_REGION}")
        list_s3_objects_sorted_by_date(
            bucket_name=S3_BUCKET_NAME,
            prefix=S3_RAW_DATA_PREFIX, # 使用您定義的前綴
            top_n=10 # 限制為前 1000 個
        )