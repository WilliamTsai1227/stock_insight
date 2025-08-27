import json
import os
import re
import boto3
import psycopg2
from datetime import date
from io import BytesIO

# --- 環境變數設定 ---
# 在 ECS 上，環境變數會直接被注入
DB_CONFIG = {
    'host': os.getenv('PostgreSQL_DB_HOST'), 
    'database': os.getenv('PostgreSQL_DB_NAME'),
    'user': os.getenv('PostgreSQL_DB_USER'),
    'password': os.getenv('PostgreSQL_DB_PASSWORD'),
    'port': os.getenv('PostgreSQL_DB_PORT')
}

S3_BUCKET_NAME = os.getenv('Financial_Report_S3_BUCKET_NAME')
S3_REGION_NAME = os.getenv('AWS_REGION')




# --- 常量定義 ---
DATA_FIELD_MAPPING = {
    "營業收入合計": ("revenue", "revenue_pct"),
    "營業成本合計": ("cost_of_revenue", "cost_of_revenue_pct"),
    "營業毛利（毛損）淨額": ("gross_profit", "gross_profit_pct"),
    "推銷費用": ("sales_expenses", "sales_expenses_pct"),
    "管理費用": ("administrative_expenses", "administrative_expenses_pct"),
    "研究發展費用": ("research_and_development_expenses", "research_and_development_expenses_pct"),
    "營業費用合計": ("operating_expenses", "operating_expenses_pct"),
    "營業利益（損失）": ("operating_income", "operating_income_pct"),
    "稅前淨利（淨損）": ("pre_tax_income", "pre_tax_income_pct"),
    "本期淨利（淨損）": ("net_income", "net_income_pct"),
    "母公司業主（淨利／損）": ("net_income_attributable_to_parent", "net_income_attributable_to_parent_pct"),
    "基本每股盈餘": ("basic_eps", None),
    "稀釋每股盈餘": ("diluted_eps", None),
}


# --- 輔助函數 ---

def get_json_from_s3(bucket_name, s3_key, region_name):
    """
    從 S3 下載 JSON 檔案內容到記憶體並解析。
    使用 boto3 的預設憑證鏈，這在 ECS 上很常見。
    """
    s3 = boto3.client('s3', region_name=region_name)
    try:
        obj = s3.get_object(Bucket=bucket_name, Key=s3_key)
        json_data = json.loads(obj['Body'].read().decode('utf-8'))
        print(f"成功從 S3 讀取 {s3_key}")
        return json_data
    except Exception as e:
        print(f"從 S3 讀取 {s3_key} 失敗: {e}")
        return None

def parse_filename(filename):
    """
    解析 S3 檔案名稱，提取股票代碼、年份、季度、財報類型和資料類型。
    例如: '1101_104Q1_income_statement_accumulated.json'
    """
    match = re.match(r'(\d+)_(\d+)Q([1-4])_(income_statement)_(accumulated|quarterly)\.json', filename)
    if match:
        stock_code = match.group(1)
        year_roc = int(match.group(2))
        quarter = int(match.group(3))
        report_kind = match.group(4)
        data_type_from_filename = match.group(5)
        return stock_code, year_roc, quarter, report_kind, data_type_from_filename
    return None, None, None, None, None

def transform_income_statement_data(json_data, filename_info, company_id_map):
    """
    轉換 S3 JSON 財報資料為適合資料庫的格式。
    """
    stock_code, year_roc, quarter, report_kind, data_type_from_filename = filename_info
    company_id = company_id_map.get(stock_code)

    if not company_id:
        print(f"錯誤: 找不到股票代碼 {stock_code} 對應的 company_id。跳過此檔案。")
        return None

    if quarter == 1:
        report_type = 'quarterly'
    else:
        report_type = data_type_from_filename

    year_ad = year_roc + 1911

    db_record = {
        "company_id": company_id,
        "report_type": report_type,
        "year": year_ad,
        "quarter": quarter,
        "original_currency": "TWD",
    }

    for s3_field, db_fields in DATA_FIELD_MAPPING.items():
        if s3_field in json_data.get("data", {}):
            values = json_data["data"][s3_field]
            numerical_value = values[0]
            percentage_value = values[1] if len(values) > 1 else None

            if isinstance(numerical_value, str) and numerical_value.lower() == 'null':
                numerical_value = None
            if isinstance(percentage_value, str) and percentage_value.lower() == 'null':
                percentage_value = None

            db_record[db_fields[0]] = numerical_value
            if db_fields[1] and percentage_value is not None:
                db_record[db_fields[1]] = percentage_value

    return db_record

def insert_income_statement_to_db(db_config, record):
    """
    將單筆損益表記錄插入到 Income_Statements 表中。
    """
    conn = None
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()

        columns = ', '.join(record.keys())
        placeholders = ', '.join(['%s'] * len(record))
        insert_sql = f"INSERT INTO Income_Statements ({columns}) VALUES ({placeholders});"

        cur.execute(insert_sql, list(record.values()))
        conn.commit()
        print(f"成功插入 {record.get('company_id')} {record.get('year')}Q{record.get('quarter')} ({record.get('report_type')}) 損益表資料。")
        return True
    except (Exception, psycopg2.Error) as error:
        print(f"插入資料庫時發生錯誤: {error}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# --- 主流程 ---

def process_s3_financial_statements(s3_key_prefix, company_id_map):
    """
    處理 S3 中特定前綴下的財報檔案。
    Args:
        s3_key_prefix (str): S3 物件的前綴，用於篩選檔案。
        company_id_map (dict): 股票代碼到公司ID的映射字典。
    """
    if not company_id_map:
        print("公司ID映射為空，無法處理財報資料。請提供有效的 company_id_map。")
        return

    try:
        s3 = boto3.client('s3', region_name=S3_REGION_NAME)
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix=s3_key_prefix)
        
        found_files = False
        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    found_files = True
                    s3_key = obj['Key']
                    
                    if not s3_key.endswith('.json'):
                        continue

                    print(f"\n處理檔案: {s3_key}")
                    filename = os.path.basename(s3_key)
                    filename_info = parse_filename(filename)

                    if not all(filename_info):
                        print(f"錯誤: 無法解析檔案名稱 {filename}。跳過。")
                        continue

                    json_data = get_json_from_s3(S3_BUCKET_NAME, s3_key, S3_REGION_NAME)
                    
                    if json_data:
                        transformed_record = transform_income_statement_data(json_data, filename_info, company_id_map)
                        if transformed_record:
                            insert_income_statement_to_db(DB_CONFIG, transformed_record)
                        else:
                            print(f"檔案 {s3_key} 的資料轉換失敗。")
                    else:
                        print(f"跳過檔案 {s3_key}，因為無法讀取其內容。")
        
        if not found_files:
            print(f"S3 路徑 '{s3_key_prefix}' 下沒有找到任何可處理的檔案。")

    except Exception as e:
        print(f"列出或處理 S3 物件時發生錯誤: {e}")


# --- 執行範例 ---
if __name__ == "__main__":
    print("開始處理 S3 財報資料...")

    # 你的 company_id_map 在這裡提供
    my_company_id_map = {
    "1101": 1,
    "1102": 2,
    "1103": 3,
    "1104": 4,
    "1108": 5,
    "1109": 6,
    "1110": 7,
    "1201": 8,
    "9949": 1902,
    "9950": 1903,
    "9951": 1904,
    "9960": 1905,
    "9962": 1906
}
    


    required_env_vars = ['PostgreSQL_DB_HOST', 'PostgreSQL_DB_NAME', 'PostgreSQL_DB_USER', 'PostgreSQL_DB_PASSWORD', 'PostgreSQL_DB_PORT', 'Financial_Report_S3_BUCKET_NAME', 'AWS_REGION']
    if not all(os.getenv(var) for var in required_env_vars):
        print("錯誤：部分必要的環境變數未設置。請確保所有變數都已在 ECS Task Definition 中設定。")
    else:
        # 使用 AWS 的憑證鏈，不需要傳入 access_key 和 secret_key
        process_s3_financial_statements(
            s3_key_prefix='raw-data/income_statement/',
            company_id_map=my_company_id_map
        )
    
    print("\n處理完成。")