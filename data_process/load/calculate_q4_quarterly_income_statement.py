
import json
import os
import re
import boto3
import psycopg2
import logging
from datetime import date
from decimal import Decimal, ROUND_HALF_UP # 導入 Decimal 進行精確計算和四捨五入
from dotenv import load_dotenv

# 在最開頭載入 .env 檔案
load_dotenv()

# --- 日誌設定 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(current_dir, 'calculate_q4_quarterly_income.log')

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=log_file_path,
    filemode='a'
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

# --- 資料庫連線配置 ---
DB_CONFIG = {
    'host': 'localhost', # 通常本地資料庫為 localhost
    'database': os.getenv('PostgreSQL_DB_NAME'),
    'user': os.getenv('PostgreSQL_DB_USER'),
    'password': os.getenv('PostgreSQL_DB_PASSWORD'),
    'port': os.getenv('PostgreSQL_DB_PORT')
}

# --- 需要計算的損益表欄位列表 ---
# 這些欄位需要進行 Q4 - Q3 的計算
FINANCIAL_FIELDS = [
    "revenue",
    "cost_of_revenue",
    "gross_profit",
    "sales_expenses",
    "administrative_expenses",
    "research_and_development_expenses",
    "operating_expenses",
    "operating_income",
    "pre_tax_income",
    "net_income",
    "net_income_attributable_to_parent",
    "basic_eps",
    "diluted_eps"
]

def get_db_connection():
    """建立並返回資料庫連接."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        logging.critical(f"無法連接到資料庫: {e}", exc_info=True)
        print("無法連接到資料庫，詳情請參考日誌。")
        return None

def calculate_q4_quarterly_income():
    """
    計算每家公司損益表第四季的單季數值，並將結果存回資料庫。
    """
    conn = get_db_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()

        # 1. 查詢所有 company_id 和 year 的 Q4 和 Q3 累積數據
        # 移除 WHERE 條件，讓 SQL 的 NULL 算術自動處理
        query = f"""
        WITH Q4_Accumulated AS (
            SELECT
                company_id,
                year,
                original_currency,
                {', '.join(FINANCIAL_FIELDS)}
            FROM
                Income_Statements
            WHERE
                report_type = 'accumulated' AND quarter = 4
        ),
        Q3_Accumulated AS (
            SELECT
                company_id,
                year,
                {', '.join(FINANCIAL_FIELDS)}
            FROM
                Income_Statements
            WHERE
                report_type = 'accumulated' AND quarter = 3
        )
        SELECT
            q4.company_id,
            q4.year,
            q4.original_currency,
            {', '.join([f'q4.{field} - q3.{field} AS {field}' for field in FINANCIAL_FIELDS])}
        FROM
            Q4_Accumulated q4
        JOIN
            Q3_Accumulated q3 ON q4.company_id = q3.company_id AND q4.year = q3.year
        ;
        """
        
        cur.execute(query)
        q4_quarterly_records = cur.fetchall()

        if not q4_quarterly_records:
            print("沒有找到足夠的第四季和第三季累積數據來計算單季損益表。")
            return

        # 準備插入的數據
        insert_records = []
        for record in q4_quarterly_records:
            company_id, year, original_currency = record[0], record[1], record[2]
            
            # 將查詢結果映射到字典，方便操作
            q4_data = {
                "company_id": company_id,
                "report_type": "quarterly",
                "year": year,
                "quarter": 4,
                "original_currency": original_currency
            }

            # 填充計算後的單季數據
            # 由於 SQL 已經處理了 NULL 算術，這裡直接取值即可
            for i, field in enumerate(FINANCIAL_FIELDS):
                q4_data[field] = record[i+3] # 從索引 3 開始是減法後的數據

            # 計算佔營收百分比
            # 注意: 這裡需要確保 q4_data["revenue"] 有值且不為 0 才能進行百分比計算
            q4_revenue = q4_data.get("revenue")
            if q4_revenue is not None and q4_revenue != 0:
                for field in FINANCIAL_FIELDS:
                    if field not in ["revenue", "basic_eps", "diluted_eps"]: # revenue 的百分比就是100%，EPS無百分比
                        value = q4_data.get(field)
                        if value is not None:
                            # 執行除法並四捨五入到小數點後第四位
                            percentage = (Decimal(str(value)) / Decimal(str(q4_revenue)) * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                            q4_data[f"{field}_pct"] = percentage
                            
                        else:
                            q4_data[f"{field}_pct"] = None # 如果數值為 None，百分比也為 None
                    elif field == "revenue": # 營業收入佔營收百分比為 100.00
                         q4_data["revenue_pct"] = Decimal('100.00')
            else:
                # 如果 revenue 為 None 或 0，所有百分比都設為 None
                for field in FINANCIAL_FIELDS:
                    if field not in ["basic_eps", "diluted_eps"]:
                        q4_data[f"{field}_pct"] = None
                q4_data["revenue_pct"] = None # 營收百分比也設為 None

            insert_records.append(q4_data)

        # 2. 將計算結果批量插入資料庫
        if insert_records:
            # 獲取所有欄位名稱 (從第一個 record 中提取)
            # 確保欄位順序正確
            all_columns = [
                "company_id", "report_type", "year", "quarter", "original_currency"
            ]
            # 依序添加 FINANCIAL_FIELDS 及對應的 _pct 欄位
            for field in FINANCIAL_FIELDS:
                all_columns.append(field)
                if field not in ["basic_eps", "diluted_eps"]:
                    all_columns.append(f"{field}_pct")
                
            # 構建 INSERT 語句
            columns_str = ", ".join(all_columns)
            placeholders = ", ".join(["%s"] * len(all_columns))
            insert_sql = f"INSERT INTO Income_Statements ({columns_str}) VALUES ({placeholders}) ON CONFLICT (company_id, year, quarter, report_type) DO UPDATE SET {', '.join([f'{col} = EXCLUDED.{col}' for col in all_columns if col not in ['company_id', 'year', 'quarter', 'report_type']])};"

            data_to_insert = []
            for record in insert_records:
                row_data = []
                for col in all_columns:
                    # 處理 Decimal 類型轉換為 float 以避免 psycopg2 警告
                    val = record.get(col)
                    if isinstance(val, Decimal):
                        row_data.append(float(val))
                    else:
                        row_data.append(val)
                data_to_insert.append(row_data)

            cur.executemany(insert_sql, data_to_insert)
            conn.commit()
            print(f"成功插入或更新 {len(insert_records)} 筆第四季單季損益表數據。")

    except psycopg2.Error as e:
        logging.error(f"執行資料庫操作時發生錯誤: {e}", exc_info=True)
        print(f"執行資料庫操作時發生錯誤，詳情請參考日誌。")
        if conn:
            conn.rollback()
    except Exception as e:
        logging.error(f"計算或處理數據時發生未預期錯誤: {e}", exc_info=True)
        print(f"計算或處理數據時發生未預期錯誤，詳情請參考日誌。")
    finally:
        if conn:
            cur.close()
            conn.close()

# --- 執行範例 ---
if __name__ == "__main__":
    print("開始計算並儲存第四季單季損益表數據...")
    calculate_q4_quarterly_income()
    print("\n計算與儲存完成。")