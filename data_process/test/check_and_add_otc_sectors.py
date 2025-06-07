import pandas as pd
import psycopg2
from psycopg2 import errors
from datetime import datetime
import os

"""
1.遍歷 CSV 檔案中所有的「產業類別」。
2.對於每個產業類別，檢查它是否已經存在於資料庫中。
3.如果是一個新的產業類別（資料庫中不存在），則會將其插入到 Sectors 資料表中。
4.插入成功後，會更新記憶中的產業映射，並記錄哪些公司使用了這個新產業。
"""

# --- 資料庫連線參數 ---
DB_PARAMS = {
    "dbname": os.getenv('PostgreSQL_DB_NAME'),
    "user": os.getenv('PostgreSQL_DB_USER'),
    "host": os.getenv('PostgreSQL_DB_HOST')
}

# --- CSV 檔案路徑設定 ---
OTC_CSV_FILEPATH = 'Taiwan_OTC_Company_20250601.csv'  # <-- 請修改為你的櫃買中心 CSV 檔案路徑

# --- 1. 從資料庫獲取現有產業名稱到 ID 的映射 ---
def get_existing_sector_mapping(conn):
    """從資料庫中獲取現有的產業名稱到 ID 的對應關係。"""
    sector_name_to_id_map = {}
    cur = conn.cursor()
    try:
        cur.execute("SELECT sector_name, sector_id FROM Sectors;")
        for name, id_val in cur.fetchall():
            sector_name_to_id_map[name] = id_val
        print(f"從資料庫載入 {len(sector_name_to_id_map)} 個現有產業。")
    except psycopg2.Error as e:
        print(f"無法載入現有產業映射: {e}")
        raise # 載入失敗則拋出異常
    finally:
        cur.close()
    return sector_name_to_id_map

# --- 2. 檢查並新增產業到資料庫 ---
def check_and_add_sectors(csv_filepath, db_params):
    """
    讀取 CSV 檔案，檢查產業類別，並將新的產業新增到資料庫。
    """
    conn = None
    newly_added_sectors = []
    companies_with_new_sectors = []

    try:
        conn = psycopg2.connect(**db_params)
        conn.autocommit = False # 確保事務控制，可以在出現錯誤時回滾
        cur = conn.cursor()

        # 獲取現有的產業映射
        sector_name_to_id_map = get_existing_sector_mapping(conn)

        # 讀取 CSV，指定 CP950 編碼
        df_otc = pd.read_csv(csv_filepath, encoding='cp950', dtype={'公司代號': str})
        print(f"讀取 {csv_filepath}，共 {len(df_otc)} 筆公司資料。")

        # 取得 CSV 中所有不重複的產業類別名稱
        csv_sectors = df_otc['產業類別'].dropna().unique()
        print(f"CSV 中共有 {len(csv_sectors)} 個不重複的產業類別。")

        for sector_name_from_csv in csv_sectors:
            # 檢查這個產業名稱是否已存在於資料庫映射中
            if sector_name_from_csv not in sector_name_to_id_map:
                print(f"發現新的產業類別: '{sector_name_from_csv}'。將新增到資料庫。")
                
                try:
                    # 插入新的產業名稱
                    cur.execute(
                        "INSERT INTO Sectors (sector_name, last_updated) VALUES (%s, %s) ON CONFLICT (sector_name) DO NOTHING RETURNING sector_id;",
                        (sector_name_from_csv, datetime.now())
                    )
                    inserted_sector_id = cur.fetchone()
                    
                    if inserted_sector_id: # 如果成功插入 (而不是被 DO NOTHING 跳過)
                        new_id = inserted_sector_id[0]
                        sector_name_to_id_map[sector_name_from_csv] = new_id # 更新映射
                        newly_added_sectors.append({'sector_name': sector_name_from_csv, 'sector_id': new_id})
                        
                        # 找出使用這個新產業類別的公司
                        companies = df_otc[df_otc['產業類別'] == sector_name_from_csv]['公司代號'].tolist()
                        companies_with_new_sectors.append({
                            'new_sector_name': sector_name_from_csv,
                            'companies': companies
                        })
                    else:
                        # 如果是 DO NOTHING，表示在執行這段程式碼期間，有另一個進程插入了相同的 sector_name
                        # 重新查詢一次，獲取其 ID
                        cur.execute("SELECT sector_id FROM Sectors WHERE sector_name = %s;", (sector_name_from_csv,))
                        existing_id = cur.fetchone()
                        if existing_id:
                            sector_name_to_id_map[sector_name_from_csv] = existing_id[0]
                            print(f"產業 '{sector_name_from_csv}' 已存在，ID 為 {existing_id[0]}。")
                        else:
                            print(f"警告: 無法確認產業 '{sector_name_from_csv}' 的 ID。")

                    conn.commit() # 每次新增一個產業就提交一次，確保新增成功
                except psycopg2.Error as e:
                    conn.rollback() # 出錯時回滾
                    print(f"新增產業 '{sector_name_from_csv}' 失敗: {e}")
                    # 這裡可以選擇是否繼續處理其他產業
                    continue # 繼續處理下一個產業
            else:
                # 產業已存在，無需處理
                pass

        print("\n所有產業檢查和新增操作完成。")
        
        # 顯示所有發現並新增的產業
        if newly_added_sectors:
            print("\n--- 以下是從 CSV 中發現並成功新增到 Sectors 資料表的新產業 ---")
            for item in newly_added_sectors:
                print(f"  產業名稱: '{item['sector_name']}', ID: {item['sector_id']}")
            
            print("\n--- 這些產業類別對應的公司如下 (部分範例) ---")
            for item in companies_with_new_sectors:
                print(f"  新產業 '{item['new_sector_name']}' 相關公司代號: {', '.join(item['companies'][:5])}{'...' if len(item['companies']) > 5 else ''}")
        else:
            print("\nCSV 中沒有發現新的產業類別需要新增到資料庫。")

    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 '{csv_filepath}'。請檢查路徑。")
    except KeyError as e:
        print(f"錯誤: CSV 檔案中缺少必要的欄位。請檢查欄位名稱。缺少: {e}。")
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
    check_and_add_sectors(OTC_CSV_FILEPATH, DB_PARAMS)