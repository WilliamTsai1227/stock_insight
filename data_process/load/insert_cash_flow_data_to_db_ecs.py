import os
import json
import boto3
import psycopg2
from psycopg2 import errors
import logging

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- 環境變數設定 ---

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'port': os.getenv('POSTGRES_PORT')
}

# S3 設定 (從 ECS 任務定義中讀取)
S3_BUCKET_NAME = os.getenv('FINANCIAL_REPORT_S3_BUCKET_NAME')

# S3 物件前綴
S3_KEY_PREFIX = 'raw-data/cash_flow/'


my_company_id_map = {
    "1101": 1,
    "1102": 2,
    "9962": 1906
}

def get_db_connection():
    """
    建立並返回 PostgreSQL 資料庫連接。
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logging.info("成功連接到 PostgreSQL 資料庫。")
        return conn
    except Exception as e:
        logging.error(f"連接資料庫失敗: {e}")
        return None

def get_s3_client():
    """
    建立並返回 S3 客戶端。
    使用 ECS 的 IAM Role，不需要提供 Access Key。
    """
    try:
        # boto3 會自動使用 ECS 任務的 IAM Role 憑證
        s3_client = boto3.client('s3')
        logging.info("成功建立 S3 客戶端。")
        return s3_client
    except Exception as e:
        logging.error(f"建立 S3 客戶端失敗: {e}")
        return None

def process_s3_object(s3_client, bucket_name, key, conn, cursor):
    """
    處理單個 S3 物件，提取資料並插入資料庫。
    """
    try:
        logging.info(f"正在處理 S3 物件: {key}")
        obj = s3_client.get_object(Bucket=bucket_name, Key=key)
        json_data = json.loads(obj['Body'].read().decode('utf-8'))

        stock_code = json_data.get('stock_code')
        year_roc = json_data.get('year_roc')
        quarter = json_data.get('quarter')
        data_fields = json_data.get('data', {})

        if not all([stock_code, year_roc, quarter, data_fields]):
            logging.warning(f"S3 物件 {key} 缺少必要的欄位。跳過。")
            return

        if stock_code not in my_company_id_map:
            logging.warning(f"股票代碼 {stock_code} 不在 company_id 映射表中。跳過 {key}。")
            return

        company_id = my_company_id_map[stock_code]
        year_ad = year_roc + 1911

        depreciation = data_fields.get('折舊費用')
        amortization = data_fields.get('攤銷費用')
        operating_cash_flow = data_fields.get('營業活動之淨現金流入（流出）')
        investing_cash_flow = data_fields.get('投資活動之淨現金流入（流出）')
        capital_expenditures = data_fields.get('取得不動產、廠房及設備')
        financing_cash_flow = data_fields.get('籌資活動之淨現金流入（流出）')
        dividends_paid = data_fields.get('發放現金股利')

        free_cash_flow = None
        if operating_cash_flow is not None and capital_expenditures is not None:
            free_cash_flow = operating_cash_flow - capital_expenditures

        net_change_in_cash = None
        if operating_cash_flow is not None and investing_cash_flow is not None and financing_cash_flow is not None:
            net_change_in_cash = operating_cash_flow + investing_cash_flow + financing_cash_flow

        original_currency = 'TWD'
        report_type = 'accumulated'

        insert_sql = """
        INSERT INTO Cash_Flow_Statements (
            company_id, report_type, year, quarter, original_currency,
            depreciation, amortization, operating_cash_flow, investing_cash_flow,
            capital_expenditures, financing_cash_flow, dividends_paid,
            free_cash_flow, net_change_in_cash
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (company_id, year, quarter, report_type) DO NOTHING;
        """

        cursor.execute(insert_sql, (
            company_id, report_type, year_ad, quarter, original_currency,
            depreciation, amortization, operating_cash_flow, investing_cash_flow,
            capital_expenditures, financing_cash_flow, dividends_paid,
            free_cash_flow, net_change_in_cash
        ))
        conn.commit()
        logging.info(f"成功插入或跳過 {stock_code}_{year_roc}Q{quarter} 的現金流量資料。")

    except errors.UniqueViolation:
        conn.rollback()
        logging.info(f"資料 {key} 已存在資料庫中 (重複鍵)。跳過。")
    except json.JSONDecodeError as e:
        logging.error(f"無法解析 S3 物件 {key} 的 JSON 內容: {e}")
    except KeyError as e:
        logging.error(f"S3 物件 {key} 中缺少預期的 JSON 鍵: {e}")
    except Exception as e:
        conn.rollback()
        logging.error(f"處理 S3 物件 {key} 時發生未知錯誤: {e}")

def main():
    """
    主函數，協調 S3 資料讀取和資料庫寫入。
    """
    conn = None
    s3_client = None
    try:
        conn = get_db_connection()
        if not conn:
            return

        s3_client = get_s3_client()
        if not s3_client:
            return

        cursor = conn.cursor()

        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix=S3_KEY_PREFIX)

        found_objects = False
        for page in pages:
            if 'Contents' in page:
                found_objects = True
                for obj in page['Contents']:
                    key = obj['Key']
                    if key.endswith('.json'):
                        process_s3_object(s3_client, S3_BUCKET_NAME, key, conn, cursor)
            
        if not found_objects:
            logging.info(f"S3 桶 '{S3_BUCKET_NAME}' 中 '{S3_KEY_PREFIX}' 前綴下沒有找到物件。")

    except Exception as e:
        logging.error(f"主程式執行錯誤: {e}")
    finally:
        if conn:
            conn.close()
            logging.info("資料庫連接已關閉。")

if __name__ == "__main__":
    main()