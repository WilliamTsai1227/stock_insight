import os
import json
import boto3
import re
import argparse # 新增：導入 argparse 函式庫
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime
"""
檢查S3儲存桶裡面的物件是否齊全，與本地的股票list比對少了哪些股票,年份,季度
"""
# 載入 .env 檔案中的環境變數
load_dotenv()

# --- 配置區塊 ---
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
S3_BUCKET_NAME = os.environ.get('Financial_Report_S3_BUCKET_NAME')
S3_RAW_DATA_PREFIX = os.environ.get('Financial_Report_S3_RAW_DATA_PREFIX', 'raw-data/cash_flow/') # 確保以斜線結尾

# S3 憑證 (請確保這些變數在您的 .env 檔案中正確設定)
AWS_S3_ACCESS_KEY_ID = os.getenv('aws_s3_access_key_id')
AWS_S3_SECRET_ACCESS_KEY = os.getenv('aws_s3_secret_access_key')

COMPANIES_FILE_PATH = 'companies_list_source.json'
OUTPUT_MISSING_FILE_PATH = 'missing_cash_flow_data_v3.json'

# 移除硬編碼的 START_YEAR_ROC 和 END_YEAR_ROC，它們將由參數傳入
QUARTERS = [1, 2, 3, 4]

def get_s3_client():
    """獲取 S3 客戶端實例"""
    if not all([AWS_REGION, AWS_S3_ACCESS_KEY_ID, AWS_S3_SECRET_ACCESS_KEY]):
        print("錯誤：S3 相關環境變數未設置。請檢查 .env 檔案或系統環境變數。")
        exit(1)
    
    return boto3.client(
        's3',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_S3_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_S3_SECRET_ACCESS_KEY
    )

def load_companies(file_path):
    """載入公司代碼列表"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"錯誤：找不到公司列表檔案 '{file_path}'。請確認檔案是否存在。")
        exit(1)
    except json.JSONDecodeError:
        print(f"錯誤：無法解析公司列表檔案 '{file_path}'。請確認其為有效的 JSON 格式。")
        exit(1)

def list_s3_objects(s3_client, bucket_name, prefix):
    """列出 S3 儲存桶中指定前綴的所有物件"""
    print(f"正在從 S3 儲存桶 '{bucket_name}' 的前綴 '{prefix}' 列出物件...")
    
    found_files = set()
    paginator = s3_client.get_paginator('list_objects_v2')
    
    try:
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    found_files.add(obj['Key'])
        print(f"S3 中找到 {len(found_files)} 個物件。")
    except Exception as e:
        print(f"錯誤：列出 S3 物件失敗。請確認 S3 儲存桶名稱、前綴和憑證是否正確。錯誤訊息：{e}")
        exit(1)
    
    return found_files

def parse_filename(filename, prefix):
    """從 S3 物件鍵中解析出股票代碼、年份和季度"""
    # 移除前綴
    if filename.startswith(prefix):
        filename = filename[len(prefix):]
    
    # 期望的格式：STOCKCODE_YYYYQ_cash_flow.json
    match = re.match(r'(\d+)_(\d{3,4})Q(\d)_cash_flow\.json', filename)
    if match:
        stock_code = match.group(1)
        year_roc = int(match.group(2))
        quarter = int(match.group(3))
        return stock_code, year_roc, quarter
    return None, None, None

def main():
    # --- 新增：使用 argparse 處理命令列參數 ---
    parser = argparse.ArgumentParser(description="檢查 S3 現金流量數據的完整性。")
    parser.add_argument('--start_year_roc', type=int, default=105,
                        help="開始檢查的民國年份 (預設: 105)")
    parser.add_argument('--end_year_roc', type=int, default=114,
                        help="結束檢查的民國年份 (預設: 114)")
    parser.add_argument('--start_quarter', type=int, default=1, choices=[1, 2, 3, 4],
                        help="開始檢查的季度 (1-4, 預設: 1)")
    parser.add_argument('--end_quarter', type=int, default=4, choices=[1, 2, 3, 4],
                        help="結束檢查的季度 (1-4, 預設: 4)")
    
    args = parser.parse_args()

    # 將參數值賦給變數
    start_year_roc = args.start_year_roc
    end_year_roc = args.end_year_roc
    start_quarter = args.start_quarter
    end_quarter = args.end_quarter

    # 輸入參數的驗證
    if start_year_roc > end_year_roc:
        print("錯誤：開始年份不能大於結束年份。")
        exit(1)
    if start_year_roc == end_year_roc and start_quarter > end_quarter:
        print("錯誤：在相同年份下，開始季度不能大於結束季度。")
        exit(1)

    print(f"S3 現金流量數據完整性檢查工具啟動...")
    print(f"檢查範圍: 民國 {start_year_roc}Q{start_quarter} 到 民國 {end_year_roc}Q{end_quarter}")
    
    s3_client = get_s3_client()
    all_companies = load_companies(COMPANIES_FILE_PATH)
    
    # 獲取 S3 中所有已存在的物件鍵
    s3_object_keys = list_s3_objects(s3_client, S3_BUCKET_NAME, S3_RAW_DATA_PREFIX)
    
    # 建立一個集合，用於快速查找已存在的數據組合
    existing_data_set = set() # 格式: "stock_code_year_quarter"
    for key in s3_object_keys:
        stock_code, year_roc, quarter = parse_filename(key, S3_RAW_DATA_PREFIX)
        if stock_code and year_roc and quarter:
            existing_data_set.add(f"{stock_code}_{year_roc}Q{quarter}")

    print("開始比對預期數據與 S3 中存在的數據...")
    missing_data_by_company_year = defaultdict(lambda: defaultdict(list)) # {stock_code: {year: [quarter, ... ]}}
    
    for stock_code in all_companies.keys():
        for year_roc in range(start_year_roc, end_year_roc + 1):
            # 根據年份調整季度的循環範圍
            current_quarters_to_check = []
            if year_roc == start_year_roc and year_roc == end_year_roc:
                # 僅單一年份，從 start_quarter 到 end_quarter
                current_quarters_to_check = [q for q in QUARTERS if start_quarter <= q <= end_quarter]
            elif year_roc == start_year_roc:
                # 開始年份，從 start_quarter 到 Q4
                current_quarters_to_check = [q for q in QUARTERS if q >= start_quarter]
            elif year_roc == end_year_roc:
                # 結束年份，從 Q1 到 end_quarter
                current_quarters_to_check = [q for q in QUARTERS if q <= end_quarter]
            else:
                # 中間年份，Q1 到 Q4
                current_quarters_to_check = QUARTERS
            
            for quarter in current_quarters_to_check:
                expected_key_format = f"{stock_code}_{year_roc}Q{quarter}"
                
                if expected_key_format not in existing_data_set:
                    missing_data_by_company_year[stock_code][year_roc].append(f"Q{quarter}")
    
    # 將 defaultdict 轉換為常規字典以進行 JSON 序列化，並確保年份排序
    formatted_missing_data = {}
    total_missing_count = 0
    for stock_code, years_data in missing_data_by_company_year.items():
        sorted_years_data = {}
        for year_roc in sorted(years_data.keys()):
            sorted_quarters = sorted(years_data[year_roc], key=lambda q: int(q.replace('Q', '')))
            sorted_years_data[str(year_roc)] = sorted_quarters # 將年份鍵轉換為字串
            total_missing_count += len(sorted_quarters)
        formatted_missing_data[stock_code] = sorted_years_data


    if total_missing_count == 0:
        print("\n太棒了！S3 中沒有發現任何缺少的現金流量數據。")
    else:
        print(f"\n發現 {total_missing_count} 筆缺少的現金流量數據。")
        print(f"詳細清單已保存到 '{OUTPUT_MISSING_FILE_PATH}'。")

    # 將結果保存到 JSON 檔案
    with open(OUTPUT_MISSING_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(formatted_missing_data, f, ensure_ascii=False, indent=4)
        
    print("檢查完成。")

if __name__ == "__main__":
    main() 


# 基本運行 (使用預設值：105Q1 到 114Q4):
# python s3_integrity_checker.py


# 指定特定範圍的檢查 (例如，只檢查 112 年到 113 年的數據):
# python s3_integrity_checker.py --start_year_roc 112 --end_year_roc 113



# 檢查單一年份的特定季度 (例如，只檢查 114 年的 Q1):
# python s3_integrity_checker.py --start_year_roc 114 --end_year_roc 114 --start_quarter 1 --end_quarter 1


# 檢查從 105 年 Q1 到 114 年 Q1 的數據：
# python s3_integrity_checker.py --start_year_roc 105 --start_quarter 1 --end_year_roc 114 --end_quarter 1
