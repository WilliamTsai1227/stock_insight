import pandas as pd
import psycopg2
from psycopg2 import errors
import os

# --- 資料庫連線參數 ---
DB_PARAMS = {
    "dbname": os.getenv('PostgreSQL_DB_NAME'),
    "user": os.getenv('PostgreSQL_DB_USER'),
    "host": os.getenv('PostgreSQL_DB_HOST')
}

# --- 檔案路徑設定 ---
CSV_FILEPATH = 'Taiwan_listed_companies_20250601.csv'  # <-- 請修改為你的輸入 CSV 檔案路徑
OUTPUT_CSV_FILEPATH = 'processed_listed_companies_data.csv' # <-- 處理後輸出 CSV 檔案路徑

# --- 1. 定義欄位名稱對應關係與要刪除的欄位 ---
COLUMN_MAPPING = {
    "公司代號": "stock_symbol",
    "公司名稱": "company_name",
    "公司簡稱": "abbreviation",
    "產業類別": "sector_id",  # 這個欄位的值會被替換成 ID
    "住址": "address",
    "董事長": "chairman",
    "總經理": "general_manager", # 保留為 general_manager
    "發言人": "spokesperson",
    "發言人職稱": "spokesperson_title",
    "成立日期": "founding_date",
    "上市日期": "listed_date",
    "已發行普通股數或TDR原發行股數": "outstanding_common_shares",
    "私募普通股(股)": "private_placement_common_shares",
    "特別股(股)": "preferred_shares",
    "簽證會計師事務所": "accounting_firm",
    "簽證會計師1": "accountant_1",
    "簽證會計師2": "accountant_2",
    "公司網址": "website",
    "普通股盈餘分派或虧損撥補頻率": "common_stock_dividend_frequency",
    "普通股年度(含第4季或後半年度)現金股息及紅利決議層級": "common_stock_dividend_decision_level",
}

COLUMNS_TO_DROP = [
    "外國企業註冊地國", "營利事業統一編號", "代理發言人", "總機電話",
    "普通股每股面額", "實收資本額(元)", "編製財務報告類型",
    "股票過戶機構", "過戶電話", "過戶地址", "英文簡稱", "英文通訊地址",
    "傳真機號碼", "電子郵件信箱", "投資人關係聯絡人", "投資人關係聯絡人職稱",
    "投資人關係聯絡電話", "投資人關係聯絡電子郵件", "公司網站內利害關係人專區網址",
    "公司網站內公司治理資訊專區網址"
]

# --- 2. 獲取產業名稱到 ID 的映射 ---
def get_sector_mapping():
    """從資料庫中獲取產業名稱到 ID 的對應關係"""
    conn = None
    sector_map = {}
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SELECT sector_name, sector_id FROM Sectors;")
        for name, id_val in cur.fetchall():
            sector_map[name] = id_val
        print(f"從資料庫載入 {len(sector_map)} 個產業對應關係。")
    except psycopg2.Error as e:
        print(f"無法載入產業映射: {e}")
        raise # 載入失敗則拋出異常
    finally:
        if conn:
            cur.close()
            conn.close()
    return sector_map

# --- 3. 處理 CSV 檔案並準備資料 ---
def process_companies_csv(csv_filepath, output_filepath, sector_map):
    """
    讀取 CSV 檔案，轉換欄位名稱，刪除不需要的欄位，
    並將產業名稱轉換為 ID，最後將處理後的資料儲存為新的 CSV 檔案。
    """
    try:
        # 讀取 CSV，指定 encoding='cp950'
        # 為了避免在 df.rename 之後無法存取原始欄位名，這裡先保留一份原始產業名稱的 Series
        df_original = pd.read_csv(csv_filepath, dtype={'公司代號': str}, encoding='cp950')
        df = df_original.copy() # 操作 df 副本
        
        print(f"原始資料筆數: {len(df)}")

        # 刪除不需要的欄位
        df = df.drop(columns=COLUMNS_TO_DROP, errors='ignore')
        print(f"刪除不必要欄位後，剩餘欄位數: {len(df.columns)}")

        # 替換欄位名稱
        df = df.rename(columns=COLUMN_MAPPING)
        print("已替換欄位名稱。")

        # 轉換產業名稱為 ID
        # 這裡使用 df_original['產業類別'] 來查找原始名稱，並將其映射到 df['sector_id']
        df['sector_id'] = df_original['產業類別'].apply(lambda x: sector_map.get(x, None))
        
        # 檢查是否有未找到對應 ID 的產業名稱
        # 現在使用 df_original 的 '產業類別' 欄位來獲取原始名稱，因為它沒有被修改
        missing_sectors_in_csv = df_original[df['sector_id'].isnull()]['產業類別'].unique()
        if len(missing_sectors_in_csv) > 0:
            print(f"警告：以下產業名稱在資料庫中找不到對應 ID，這些行的 sector_id 將為 NULL: {list(missing_sectors_in_csv)}")


        # 確保所有日期欄位是日期格式
        for col in ['founding_date', 'listed_date']:
            if col in df.columns:
                # 使用 errors='coerce' 將無效日期轉換為 NaT (Not a Time)
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.date

        # 清理數字欄位，例如移除千分位逗號和多餘的空白
        numeric_cols = [
            'outstanding_common_shares', 'private_placement_common_shares',
            'preferred_shares'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '', regex=False).str.strip()
                # 將空字串轉換為 NaN，然後再轉為數值型別
                df[col] = pd.to_numeric(df[col], errors='coerce')


        # 確保 company_name, stock_symbol 都是字串且非空，並移除前後空白
        df['stock_symbol'] = df['stock_symbol'].astype(str).str.strip()
        df['company_name'] = df['company_name'].astype(str).str.strip()
        
        # 將 '－' 這類表示缺失值的字串轉換為 None (NULL for DB)
        # 注意：pandas NaN 會自動被 psycopg2 處理成 NULL
        df = df.replace({'－': None}) 

        # --- 新增：將處理後的 DataFrame 另存為新的 CSV 檔案 ---
        df.to_csv(output_filepath, index=False, encoding='utf-8-sig') # 使用 utf-8-sig 以便 Excel 正確打開
        print(f"處理後的資料已儲存到: {output_filepath}")

        return df

    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 '{csv_filepath}'。請檢查路徑。")
        return None
    except Exception as e:
        print(f"處理 CSV 時發生錯誤: {e}")
        return None

# --- 4. 將處理後的資料插入 Companies 資料表 ---
def insert_companies_to_db(df):
    """
    將處理後的 DataFrame 資料插入 Companies 資料表。
    使用 ON CONFLICT DO NOTHING 處理重複資料。
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # Companies 表的欄位列表 (按你 CREATE TABLE 定義的順序)
        target_columns = [
            "stock_symbol", "company_name", "abbreviation", "founding_date",
            "listed_date", "market", "country_id", "address", "chairman",
            "general_manager", "spokesperson", "spokesperson_title",
            "outstanding_common_shares", "private_placement_common_shares",
            "preferred_shares", "accounting_firm", "accountant_1", "accountant_2",
            "website", "common_stock_dividend_frequency", "common_stock_dividend_decision_level",
            "description", "is_verified", "sector_id"
        ]

        # 查詢 'Taiwan' 的 country_id
        taiwan_country_id = None
        try:
            cur.execute("SELECT country_id FROM Countrys WHERE country_name = 'Taiwan';")
            result = cur.fetchone()
            if result:
                taiwan_country_id = result[0]
                print(f"已取得 'Taiwan' 的 country_id: {taiwan_country_id}")
            else:
                print("錯誤: 'Taiwan' 的 country_id 在資料庫中找不到。請確認 Countrys 表中已插入 'Taiwan'。")
                return # 無法繼續，直接返回
        except Exception as e:
            print(f"查詢 'Taiwan' 的 country_id 失敗: {e}")
            return # 無法繼續，直接返回

        if taiwan_country_id is None:
            print("無法獲取 'Taiwan' 的 country_id，中止插入。")
            return

        inserted_count = 0
        skipped_count = 0
        error_count = 0

        print("\n開始插入公司資料到 Companies 資料表...")
        for index, row in df.iterrows():
            # 建立一個字典，只包含要插入的欄位
            data_to_insert = {}
            for col in target_columns:
                if col in row and pd.notna(row[col]): # 檢查欄位是否存在且不是 NaN
                    data_to_insert[col] = row[col]
                else:
                    data_to_insert[col] = None # 設定為 None 以便 psycopg2 處理為 NULL

            # 設定 country_id 為 Taiwan 的 ID
            data_to_insert['country_id'] = taiwan_country_id
            
            # 處理 Companies 表中可能沒有的欄位，給予預設值或 None
            if 'market' not in data_to_insert or data_to_insert['market'] is None:
                data_to_insert['market'] = 'TWSE' # 假設預設為 TWSE
            if 'description' not in data_to_insert:
                data_to_insert['description'] = None
            if 'is_verified' not in data_to_insert:
                data_to_insert['is_verified'] = False # Companies 表預設為 False

            # 構建 SQL 語句
            columns_in_insert = list(data_to_insert.keys())
            placeholders = ', '.join(['%s'] * len(columns_in_insert))
            column_names = ', '.join(columns_in_insert)

            sql = f"""
            INSERT INTO Companies ({column_names}) 
            VALUES ({placeholders})
            ON CONFLICT (stock_symbol, country_id) DO NOTHING;
            """
            
            values = tuple(data_to_insert[col] for col in columns_in_insert)

            try:
                cur.execute(sql, values)
                if cur.rowcount > 0:
                    inserted_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                conn.rollback() # 回滾當前事務
                print(f"插入 '{row.get('stock_symbol', '未知股票')}' 時發生錯誤: {e}")
                error_count += 1
                # 重新開始一個新的事務 (對於單個錯誤而言，回滾後繼續)
                conn.commit() # 提交前面的成功操作，開始新的事務
                conn.autocommit = False # 確保不是自動提交

        conn.commit() # 提交所有成功的操作
        print("\n所有公司資料處理完畢。")
        print(f"成功插入筆數: {inserted_count}")
        print(f"跳過筆數 (已存在或衝突): {skipped_count}")
        print(f"錯誤筆數: {error_count}")

    except psycopg2.Error as e:
        print(f"資料庫連線或操作失敗: {e}")
    except Exception as e:
        print(f"發生未知錯誤: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()
            print("資料庫連線已關閉。")

# --- 主執行區塊 ---
if __name__ == "__main__":
    # 1. 獲取產業映射
    try:
        sector_id_map = get_sector_mapping()
    except Exception:
        print("無法取得產業映射，程式終止。")
        exit()

    # 2. 處理 CSV 資料 (會自動另存一份處理後的 CSV)
    processed_df = process_companies_csv(CSV_FILEPATH, OUTPUT_CSV_FILEPATH, sector_id_map)

    if processed_df is not None and not processed_df.empty:
        # 3. 將處理後的資料插入資料庫
        insert_companies_to_db(processed_df)
    else:
        print("沒有有效資料可供插入。")