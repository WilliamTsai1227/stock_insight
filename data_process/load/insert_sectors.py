import psycopg2
from psycopg2 import errors
import os

"""
將預定義的產業類別列表，插入到 PostgreSQL 資料庫的 Sectors 資料表中。
"""

# 你要插入的產業資料
sector_data = {
    "data": [
        "半導體業", "光電業", "化學工業", "塑膠工業","鋼鐵工業","水泥工業","橡膠工業","食品工業",
        "造紙工業", "汽車工業", "電機機械", "電腦及週邊設備業", "電子零組件業","其他電子業",
        "通信網路業", "電子通路業", "數位雲端", "資訊服務業", "生技醫療業", "電器電纜", 
        "金融保險業", "建材營造", "油電燃氣業","存託憑證", "居家生活","玻璃陶瓷", "紡織纖維", "綠能環保",
        "航運業", "觀光餐旅", "貿易百貨", 
        "運動休閒", "其他"
    ]
}

# 資料庫連線參數
DB_PARAMS = {
    "dbname": os.getenv('PostgreSQL_DB_NAME'),
    "user": os.getenv('PostgreSQL_DB_USER'),
    "host": os.getenv('PostgreSQL_DB_HOST')
}

def insert_sectors(sectors):
    """將產業名稱插入 Sectors 資料表"""
    conn = None
    try:
        # 建立資料庫連線
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        print("開始插入產業資料...")
        inserted_count = 0
        skipped_count = 0

        for sector_name in sectors:
            try:
                # 準備 SQL 插入語句
                # 使用 ON CONFLICT (sector_name) DO NOTHING 來處理重複的產業名稱
                # 如果 sector_name 已經存在，就跳過插入，避免報錯
                sql = """
                INSERT INTO Sectors (sector_name) 
                VALUES (%s)
                ON CONFLICT (sector_name) DO NOTHING;
                """
                cur.execute(sql, (sector_name,))
                
                # 檢查是否有實際插入（因為 ON CONFLICT DO NOTHING 不會導致錯誤，但也不會影響 rowcount）
                # 更好的方式是嘗試 SELECT 後再 INSERT 或依靠 ON CONFLICT
                # 對於 ON CONFLICT DO NOTHING，如果 rowcount 是 0，表示沒有插入（可能是因為重複）
                if cur.rowcount > 0:
                    inserted_count += 1
                    print(f"成功插入: {sector_name}")
                else:
                    skipped_count += 1
                    print(f"跳過 (已存在): {sector_name}")

            except errors.UniqueViolation:
                # 雖然我們用了 ON CONFLICT DO NOTHING，但為了示範，保留這個捕獲
                # 在實際運行中，ON CONFLICT DO NOTHING 會防止這個錯誤發生
                conn.rollback() # 回滾當前事務，因為有錯誤發生
                print(f"錯誤: 產業名稱 '{sector_name}' 已存在，跳過。")
                skipped_count += 1
            except Exception as e:
                conn.rollback() # 發生其他錯誤時回滾
                print(f"插入 '{sector_name}' 時發生錯誤: {e}")
                
        # 提交事務
        conn.commit()
        print("\n所有產業資料處理完畢。")
        print(f"成功插入筆數: {inserted_count}")
        print(f"跳過筆數 (已存在): {skipped_count}")

    except psycopg2.Error as e:
        print(f"資料庫連線或操作失敗: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()
            print("資料庫連線已關閉。")

if __name__ == "__main__":
    insert_sectors(sector_data["data"])