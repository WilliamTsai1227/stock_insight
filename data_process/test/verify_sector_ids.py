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
ORIGINAL_CSV_FILEPATH = 'Taiwan_OTC_Company_20250601.csv'  # <-- 請修改為你的原始 CSV 檔案路徑
PROCESSED_CSV_FILEPATH = 'processed_OTC_companies_data.csv'       # <-- 請修改為你處理後 CSV 檔案路徑

# --- 1. 從資料庫獲取產業映射並格式化為 list of dictionary ---
def get_sector_mapping_list_of_dict():
    """從資料庫中獲取產業名稱到 ID 的對應關係，並返回 list of dictionary。"""
    conn = None
    sector_list = []
    sector_name_to_id_map = {} # 也建立一個 name -> id 的映射供快速查找
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SELECT sector_id, sector_name, last_updated FROM Sectors ORDER BY sector_id;")
        for sector_id, sector_name, last_updated in cur.fetchall():
            sector_dict = {
                'sector_id': sector_id,
                'sector_name': sector_name,
                'last_updated': last_updated
            }
            sector_list.append(sector_dict)
            sector_name_to_id_map[sector_name] = sector_id
        
        print(f"從資料庫載入 {len(sector_list)} 個產業對應關係。")
        print("以下是部分產業對應列表範例：")
        for i in range(min(5, len(sector_list))): # 打印前5個作為範例
            print(sector_list[i])

    except psycopg2.Error as e:
        print(f"無法載入產業映射: {e}")
        raise # 載入失敗則拋出異常
    finally:
        if conn:
            cur.close()
            conn.close()
    return sector_list, sector_name_to_id_map

# --- 2. 驗證產業 ID 轉換 ---
def verify_sector_id_conversion(original_csv_path, processed_csv_path, sector_name_to_id_map):
    """
    讀取原始和處理後的 CSV，並驗證產業 ID 轉換是否正確。
    """
    print(f"\n開始驗證產業 ID 轉換...")
    try:
        # 讀取原始 CSV，指定 CP950 編碼，並確保 '公司代號' 是字串
        df_original = pd.read_csv(original_csv_path, encoding='cp950', dtype={'公司代號': str})
        
        # 讀取處理後的 CSV，假設是 UTF-8 編碼，並確保 'stock_symbol' 是字串
        df_processed = pd.read_csv(processed_csv_path, encoding='utf-8', dtype={'stock_symbol': str})

        # 只選取需要的欄位進行合併
        df_original_subset = df_original[['公司代號', '產業類別']].copy()
        df_processed_subset = df_processed[['stock_symbol', 'sector_id']].copy()

        # 將兩個 DataFrame 根據唯一的識別碼 (公司代號 / stock_symbol) 進行合併
        # 使用 'inner' 連結，只保留兩個檔案中都有的公司代號
        df_merged = pd.merge(
            df_original_subset,
            df_processed_subset,
            left_on='公司代號',
            right_on='stock_symbol',
            how='inner'
        )

        if df_merged.empty:
            print("警告: 合併後的資料為空，可能沒有共同的公司代號可供比較。")
            print("請檢查原始 CSV 和處理後 CSV 中的 '公司代號'/'stock_symbol' 欄位。")
            return

        mismatches_found = 0
        
        # 迭代合併後的 DataFrame 進行比較
        for index, row in df_merged.iterrows():
            original_sector_name = row['產業類別']
            processed_sector_id = row['sector_id']
            stock_symbol = row['公司代號'] # 用於識別

            # 根據資料庫映射查找預期的 ID
            expected_sector_id = sector_name_to_id_map.get(original_sector_name, None)

            # 進行比較
            # 處理原始產業名稱在資料庫中找不到的情況
            if expected_sector_id is None and pd.notna(original_sector_name):
                # 如果資料庫中沒有對應，但處理後的 CSV 卻有 ID，則為不一致
                if pd.notna(processed_sector_id):
                    print(f"不一致 - 公司代號: {stock_symbol}")
                    print(f"  原始產業名稱 '{original_sector_name}' 在資料庫中無對應 ID。")
                    print(f"  但處理後 'sector_id' 卻是: {processed_sector_id}")
                    mismatches_found += 1
                # 如果 expected_sector_id 是 None 且 processed_sector_id 也是 None/NaN，則符合預期
            elif expected_sector_id is not None and processed_sector_id != expected_sector_id:
                # 只有當預期 ID 存在且不匹配處理後的 ID 時，才標記為不一致
                print(f"不一致 - 公司代號: {stock_symbol}")
                print(f"  原始產業名稱: '{original_sector_name}'")
                print(f"  預期 sector_id (根據資料庫): {expected_sector_id}")
                print(f"  處理後 CSV 的 sector_id: {processed_sector_id}")
                mismatches_found += 1
        
        if mismatches_found == 0:
            print("\n恭喜！所有公司資料的產業 ID 轉換都正確且與資料庫映射一致。")
        else:
            print(f"\n驗證完成。發現 {mismatches_found} 處產業 ID 轉換不一致。")

    except FileNotFoundError as e:
        print(f"錯誤: 找不到檔案。請檢查檔案路徑: {e}")
    except KeyError as e:
        print(f"錯誤: CSV 檔案中缺少必要的欄位。請檢查欄位名稱。缺少: {e}")
    except Exception as e:
        print(f"驗證過程中發生未知錯誤: {e}")

# --- 主執行區塊 ---
if __name__ == "__main__":
    # 1. 從資料庫獲取產業映射列表和字典
    try:
        sector_list_of_dict, sector_name_to_id_map = get_sector_mapping_list_of_dict()
    except Exception:
        print("無法取得產業映射，程式終止。")
        exit()

    # 2. 驗證產業 ID 轉換
    verify_sector_id_conversion(ORIGINAL_CSV_FILEPATH, PROCESSED_CSV_FILEPATH, sector_name_to_id_map)