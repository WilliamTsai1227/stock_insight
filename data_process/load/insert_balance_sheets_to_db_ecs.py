import json
import os
import re
import boto3
import psycopg2
import logging
from datetime import date

# --- 日誌設定  ---
logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s - %(levelname)s - %(message)s"
)


DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'port': os.getenv('POSTGRES_PORT', 5432)
}

S3_BUCKET_NAME = os.getenv('FINANCIAL_REPORT_S3_BUCKET_NAME')
S3_REGION_NAME = os.getenv('AWS_REGION', 'ap-northeast-1')  # 可根據實際情況修改

# --- 常量定義 ---
DATA_FIELD_MAPPING = {
    "現金及約當現金": ("cash_and_equivalents", "cash_and_equivalents_pct", ["現金及約當現金"]),
    "短期投資": ("short_term_investments", "short_term_investments_pct", ["透過損益按公允價值衡量之金融資產－流動", "備供出售金融資產－流動淨額"]),
    "應收帳款及票據": ("accounts_receivable_and_notes", "accounts_receivable_and_notes_pct", ["應收票據淨額", "應收帳款淨額", "應收帳款－關係人淨額"]), # 嚴格依照提供的對應，移除了"其他應收款淨額", "其他應收款－關係人淨額"
    "存貨": ("inventory", "inventory_pct", ["存貨"]),
    "其他流動資產": ("other_current_assets", "other_current_assets_pct", ["其他流動資產"]), # 嚴格依照提供的對應，移除了"預付款項"
    "流動資產合計": ("current_assets", "current_assets_pct", ["流動資產合計"]),
    "長期投資": ("total_long_term_investments", "total_long_term_investments_pct", ["備供出售金融資產－非流動淨額", "以成本衡量之金融資產－非流動淨額", "採用權益法之投資淨額"]),
    "固定資產合計": ("fixed_assets_total", "fixed_assets_total_pct", ["不動產、廠房及設備"]), # 嚴格依照提供的對應，移除了"投資性不動產淨額"
    "其他非流動資產": ("other_non_current_assets", "other_non_current_assets_pct", ["其他非流動資產"]), # 嚴格依照提供的對應，移除了"無形資產"
    "資產總計": ("total_assets", "total_assets_pct", ["負債及權益總計"]), # 更名為 total_assets
}

BASE_TEMP_DIR = "/tmp/temp_json"   # ECS 容器內可用 /tmp 暫存

# --- 輔助函數 ---
def download_json_from_s3(bucket_name, s3_key, local_path):
    """ 從 S3 下載 JSON 檔案到本地 """
    s3 = boto3.client("s3", region_name=S3_REGION_NAME)
    try:
        s3.download_file(bucket_name, s3_key, local_path)
        logging.info(f"成功下載 {s3_key} 到 {local_path}")
        return True
    except Exception as e:
        logging.error(f"下載失敗: {e}", exc_info=True)
        return False


def transform_balance_sheet_data(json_data, filename_info, company_id_map):
    """
    轉換 S3 JSON 資產負債表資料為適合資料庫的格式。
    """
    stock_code, year_roc, quarter, report_kind, data_type_from_filename = filename_info

    company_id = company_id_map.get(stock_code)

    if not company_id:
        logging.error(f"錯誤: 找不到股票代碼 {stock_code} 對應的 company_id。跳過此檔案。")
        print(f"錯誤: 找不到股票代碼 {stock_code} 對應的 company_id。跳過此檔案。")
        return None

    report_type = 'quarterly'
    year_ad = year_roc + 1911

    db_record = {
        "company_id": company_id,
        "report_type": report_type,
        "year": year_ad,
        "quarter": quarter,
        "original_currency": "TWD",
    }

    for db_field_group, (numerical_col, percentage_col, s3_keys) in DATA_FIELD_MAPPING.items():
        total_numerical_value = 0
        total_percentage_value = 0
        
        found_any_value = False

        for s3_key in s3_keys:
            if s3_key in json_data.get("data", {}):
                values = json_data["data"][s3_key]
                
                current_numerical_value = values[0]
                current_percentage_value = values[1] if len(values) > 1 else None

                if current_numerical_value is None or (isinstance(current_numerical_value, str) and current_numerical_value.lower() == 'null'):
                    current_numerical_value = None
                if current_percentage_value is None or (isinstance(current_percentage_value, str) and current_percentage_value.lower() == 'null'):
                    current_percentage_value = None

                if current_numerical_value is not None:
                    total_numerical_value += current_numerical_value
                    found_any_value = True
                
                # 百分比只在特定情況下累加，否則取總值百分比
                # 這裡仍然保留累加邏輯，但對於總計項目，會覆蓋為 JSON 原始總計百分比
                if current_percentage_value is not None:
                    total_percentage_value += current_percentage_value


        if found_any_value:
            db_record[numerical_col] = total_numerical_value
            if percentage_col is not None:
                # 針對總計項目，直接使用 JSON 中提供的百分比，因為內部細項百分比累加可能不精確
                # 這裡只針對你提供的'資產總計'進行特殊處理，其他非明確指出的總計欄位將繼續累加百分比
                if db_field_group == "資產總計":
                    if s3_keys[0] in json_data.get("data", {}) and len(json_data["data"][s3_keys[0]]) > 1:
                        db_record[percentage_col] = json_data["data"][s3_keys[0]][1]
                    else:
                        db_record[percentage_col] = None
                else:
                    db_record[percentage_col] = total_percentage_value
        else:
            db_record[numerical_col] = None
            if percentage_col is not None:
                db_record[percentage_col] = None

    return db_record

def insert_balance_sheet_to_db(db_config, record):
    """
    將單筆資產負債表記錄插入到 Balance_Sheets 表中。
    """
    conn = None
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()

        columns = ', '.join(record.keys())
        placeholders = ', '.join(['%s'] * len(record))
        insert_sql = f"INSERT INTO Balance_Sheets ({columns}) VALUES ({placeholders});"

        cur.execute(insert_sql, list(record.values()))
        conn.commit()
        print(f"成功插入 {record.get('company_id')} {record.get('year')}Q{record.get('quarter')} 資產負債表資料。")
        return True
    except (Exception, psycopg2.Error) as error:
        logging.error(f"插入資料庫時發生錯誤: {error}. 記錄: {record}", exc_info=True)
        print(f"插入資料庫時發生錯誤，詳情請參考日誌。")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            cur.close()
            conn.close()


# --- 主流程 ---
def process_s3_financial_statements(s3_key_prefix, company_id_map):
    if not company_id_map:
        logging.error("公司ID映射為空，無法處理財報資料。")
        return

    os.makedirs(BASE_TEMP_DIR, exist_ok=True)
    logging.info(f"暫存目錄: {BASE_TEMP_DIR}")

    try:
        s3_resource = boto3.resource("s3", region_name=S3_REGION_NAME)
        bucket = s3_resource.Bucket(S3_BUCKET_NAME)

        for obj in bucket.objects.filter(Prefix=s3_key_prefix):
            s3_key = obj.key
            if not s3_key.endswith(".json"):
                continue

            filename = os.path.basename(s3_key)
            stock_code, year_roc, quarter, report_kind, data_type = parse_filename(filename)

            if not all([stock_code, year_roc, quarter, report_kind, data_type]):
                logging.warning(f"無法解析檔案名稱 {filename}，跳過。")
                continue

            local_json_path = os.path.join(BASE_TEMP_DIR, filename)
            if download_json_from_s3(S3_BUCKET_NAME, s3_key, local_json_path):
                try:
                    with open(local_json_path, "r", encoding="utf-8") as f:
                        json_data = json.load(f)

                    transformed = transform_balance_sheet_data(
                        json_data, (stock_code, year_roc, quarter, report_kind, data_type), company_id_map
                    )

                    if transformed:
                        insert_balance_sheet_to_db(DB_CONFIG, transformed)
                except Exception as e:
                    logging.error(f"處理檔案 {filename} 出錯: {e}", exc_info=True)
                finally:
                    if os.path.exists(local_json_path):
                        os.remove(local_json_path)

    except Exception as e:
        logging.error(f"S3 處理錯誤: {e}", exc_info=True)

# --- 執行 ---
if __name__ == "__main__":
    logging.info("開始處理 S3 財報資料...")

    my_company_id_map = {
        "1101": 1, "1102": 2, "1103": 3
    }

    process_s3_financial_statements("raw-data/balance-sheet/", my_company_id_map)

    logging.info("處理完成。")
