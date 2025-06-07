import pandas as pd
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
from datetime import date 

# 載入環境變數
load_dotenv()

def get_db_connection():
    """建立資料庫連線"""
    return psycopg2.connect(
        dbname=os.getenv('PostgreSQL_DB_NAME'),
        user=os.getenv('PostgreSQL_DB_USER'),
        password=os.getenv('PostgreSQL_DB_PASSWORD'),
        host=os.getenv('PostgreSQL_DB_HOST'),
        port=os.getenv('PostgreSQL_DB_PORT')
    )

def try_read_csv(file_path):
    """自動嘗試多種編碼讀取 CSV，最後用 ignore 跑最大可讀內容"""
    encodings = ['cp950', 'utf-8', 'big5']
    for encoding in encodings:
        try:
            print(f"嘗試用 {encoding} 讀取 {file_path}")
            # 確保 '公司代號' 是字串，並在讀取時就指定為字串
            return pd.read_csv(file_path, encoding=encoding, dtype={'公司代號': str, 'stock_symbol': str}), encoding
        except UnicodeDecodeError:
            print(f"用 {encoding} 讀取失敗: UnicodeDecodeError")
        except Exception as e:
            print(f"用 {encoding} 讀取失敗: {e}")
    print(f"全部失敗，改用 cp950 + errors='ignore' 讀取 {file_path}")
    try:
        df = pd.read_csv(file_path, encoding='cp950', errors='ignore', dtype={'公司代號': str, 'stock_symbol': str})
        return df, "cp950+ignore"
    except Exception as e:
        print(f"用 cp950+ignore 仍失敗: {e}")
        raise ValueError(f"無法讀取檔案: {file_path}")

def check_csv_consistency(processed_file_path, original_file_path, column_mapping, columns_to_drop):
    """
    檢查精簡版 CSV 與原始 CSV 資料在共同欄位上是否一致。
    只檢查原始 CSV 經過映射和刪除後，與精簡版 CSV 共享的欄位。
    """
    print(f"\n--- 檢查檔案一致性: {processed_file_path} vs {original_file_path} ---")
    
    processed_df, processed_enc = try_read_csv(processed_file_path)
    original_df_raw, original_enc = try_read_csv(original_file_path) 
    print(f"精簡版檔案編碼: {processed_enc}，原始檔案編碼: {original_enc}")

    original_df_processed = original_df_raw.copy()
    
    original_df_processed = original_df_processed.drop(columns=columns_to_drop, errors='ignore')
    
    cols_to_rename = {k: v for k, v in column_mapping.items() if k in original_df_processed.columns}
    original_df_processed = original_df_processed.rename(columns=cols_to_rename)

    if 'sector_id' in original_df_processed.columns:
        original_df_processed = original_df_processed.drop(columns=['sector_id'], errors='ignore')
    if 'sector_id' in processed_df.columns:
        processed_df_for_comparison = processed_df.drop(columns=['sector_id'], errors='ignore')
    else:
        processed_df_for_comparison = processed_df.copy()

    common_columns = list(set(processed_df_for_comparison.columns) & set(original_df_processed.columns))
    # 確保 stock_symbol 在比較前是字串
    processed_df_for_comparison['stock_symbol'] = processed_df_for_comparison['stock_symbol'].astype(str).str.strip()
    original_df_processed['stock_symbol'] = original_df_processed['stock_symbol'].astype(str).str.strip()

    processed_df_for_comparison = processed_df_for_comparison.sort_values(by='stock_symbol').reset_index(drop=True)
    original_df_processed = original_df_processed.sort_values(by='stock_symbol').reset_index(drop=True)

    if len(processed_df_for_comparison) != len(original_df_processed):
        print(f"錯誤：處理後 CSV ({len(processed_df_for_comparison)} 筆) 與原始 CSV ({len(original_df_processed)} 筆) 行數不一致。")
        return False
    
    for col in common_columns:
        # 對於數字欄位，先轉換為數值型別，並處理 NaN
        if col in ['outstanding_common_shares', 'private_placement_common_shares', 'preferred_shares']:
            # 使用 pd.to_numeric 轉換，並將錯誤轉換為 NaN
            processed_df_for_comparison[col] = pd.to_numeric(processed_df_for_comparison[col], errors='coerce')
            original_df_processed[col] = pd.to_numeric(original_df_processed[col], errors='coerce')
        
        # 對於日期欄位，轉換為 date 型別
        if col in ['founding_date', 'listed_date', 'otc_listed_date']: 
            processed_df_for_comparison[col] = pd.to_datetime(processed_df_for_comparison[col], errors='coerce').dt.date
            original_df_processed[col] = pd.to_datetime(original_df_processed[col], errors='coerce').dt.date

        # 將 NaN/NaT/None 轉換為統一的空字串，方便後續比較
        # 這裡使用 .astype(str) 在 .fillna('') 之前，避免 pd.NaT 等特殊 NaN 的字串表示問題
        processed_values = processed_df_for_comparison[col].fillna('').astype(str).replace('－', '').str.strip()
        original_values = original_df_processed[col].fillna('').astype(str).replace('－', '').str.strip()
        
        for idx in range(len(processed_df_for_comparison)):
            p_val = processed_values.iloc[idx]
            o_val = original_values.iloc[idx]

            # 針對數字類型，即使是字串形式也嘗試轉成 float 再轉 int 再轉 str，確保 '123.0' 和 '123' 視為相同
            if col in ['outstanding_common_shares', 'private_placement_common_shares', 'preferred_shares']:
                try:
                    p_val = str(int(float(p_val))) if p_val else ''
                    o_val = str(int(float(o_val))) if o_val else ''
                except ValueError:
                    pass # 如果無法轉換為數字，則保持原樣字串比較

            if p_val != o_val:
                stock_symbol = processed_df_for_comparison.iloc[idx]['stock_symbol']
                print(f"錯誤：公司 {stock_symbol}，欄位 '{col}' 數據不一致。")
                print(f"  精簡版 CSV 值 (原始): '{processed_df_for_comparison.iloc[idx][col]}', 處理後: '{p_val}'")
                print(f"  原始 CSV 值 (原始):    '{original_df_processed.iloc[idx][col]}', 處理後: '{o_val}'")
                return False
    
    print(f"✓ 檔案 {processed_file_path} 與 {original_file_path} 在共同欄位上數據一致。")
    return True


# --- 欄位映射與刪除定義 (必須與處理腳本一致) ---
OTC_COLUMN_MAPPING = {
    "公司代號": "stock_symbol",
    "公司名稱": "company_name",
    "公司簡稱": "abbreviation",
    "產業類別": "sector_id",
    "住址": "address",
    "董事長": "chairman",
    "總經理": "general_manager",
    "發言人": "spokesperson",
    "發言人職稱": "spokesperson_title",
    "成立日期": "founding_date",
    "上櫃日期": "otc_listed_date",
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

OTC_COLUMNS_TO_DROP = [
    "外國企業註冊地國", "營利事業統一編號", "代理發言人", "總機電話",
    "普通股每股面額", "實收資本額(元)", "編製財務報告類型", 
    "股票過戶機構", "過戶電話", "過戶地址", "英文簡稱", "英文通訊地址",
    "傳真機號碼", "電子郵件信箱", "投資人關係聯絡人", "投資人關係聯絡人職稱",
    "投資人關係聯絡電話", "投資人關係聯絡電子郵件", "公司網站內利害關係人專區網址",
    "公司網站內公司治理資訊專區網址",
    "上市日期", 
]

LISTED_COLUMN_MAPPING = {
    "公司代號": "stock_symbol",
    "公司名稱": "company_name",
    "公司簡稱": "abbreviation",
    "產業類別": "sector_id",
    "住址": "address",
    "董事長": "chairman",
    "總經理": "general_manager",
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

LISTED_COLUMNS_TO_DROP = [
    "外國企業註冊地國", "營利事業統一編號", "代理發言人", "總機電話",
    "普通股每股面額", "實收資本額(元)", "編製財務報告類型",
    "股票過戶機構", "過戶電話", "過戶地址", "英文簡稱", "英文通訊地址",
    "傳真機號碼", "電子郵件信箱", "投資人關係聯絡人", "投資人關係聯絡人職稱",
    "投資人關係聯絡電話", "投資人關係聯絡電子郵件", "公司網站內利害關係人專區網址",
    "公司網站內公司治理資訊專區網址",
    "上櫃日期", 
]


def test_company_count():
    """測試上市櫃公司數量是否與資料庫一致"""
    listed_df, _ = try_read_csv('../file/Taiwan_listed_companies_data_processed.csv')
    otc_df, _ = try_read_csv('../file/Taiwan_OTC_companies_data_processed.csv')
    
    csv_total = len(listed_df) + len(otc_df)
    print(f"CSV 檔案中總公司數量: {csv_total}")
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM Companies WHERE country_id = (SELECT country_id FROM Countrys WHERE country_name = 'Taiwan')")
        db_count = cur.fetchone()[0]
        cur.close()
        print(f"資料庫中台灣公司數量: {db_count}")
        
        assert csv_total == db_count, f"公司數量不一致：CSV 總數 {csv_total}，資料庫數量 {db_count}"
    finally:
        if conn:
            conn.close()

def test_market_type():
    """測試市場類型是否正確 (TWSE 對應 listed_date, TPEx 對應 otc_listed_date)"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT stock_symbol FROM Companies
            WHERE (market != 'TWSE' OR listed_date IS NULL OR otc_listed_date IS NOT NULL)
              AND listed_date IS NOT NULL 
              AND country_id = (SELECT country_id FROM Countrys WHERE country_name = 'Taiwan');
        """)
        twse_wrong_companies = cur.fetchall()
        assert len(twse_wrong_companies) == 0, f"有 {len(twse_wrong_companies)} 筆上市公司 ({[s[0] for s in twse_wrong_companies]}) 的市場類型或日期欄位不符合 'TWSE' 規範。"

        cur.execute("""
            SELECT stock_symbol FROM Companies
            WHERE (market != 'TPEx' OR otc_listed_date IS NULL OR listed_date IS NOT NULL)
              AND otc_listed_date IS NOT NULL 
              AND country_id = (SELECT country_id FROM Countrys WHERE country_name = 'Taiwan');
        """)
        tpex_wrong_companies = cur.fetchall()
        assert len(tpex_wrong_companies) == 0, f"有 {len(tpex_wrong_companies)} 筆上櫃公司 ({[s[0] for s in tpex_wrong_companies]}) 的市場類型或日期欄位不符合 'TPEx' 規範。"

        cur.execute("""
            SELECT stock_symbol FROM Companies
            WHERE listed_date IS NOT NULL AND otc_listed_date IS NOT NULL
              AND country_id = (SELECT country_id FROM Countrys WHERE country_name = 'Taiwan');
        """)
        both_dates_companies = cur.fetchall()
        assert len(both_dates_companies) == 0, f"有 {len(both_dates_companies)} 筆公司 ({[s[0] for s in both_dates_companies]}) 同時有上市和上櫃日期。"

        cur.close()
    finally:
        if conn:
            conn.close()
    print("✓ 市場類型測試通過")

def test_null_values():
    """測試是否有不應該為空的欄位為空"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        required_fields = [
            'stock_symbol', 'company_name', 'market', 
            'country_id', 'sector_id'
        ]
        for field in required_fields:
            cur.execute(sql.SQL("""
                SELECT COUNT(*) FROM Companies
                WHERE {} IS NULL
                  AND country_id = (SELECT country_id FROM Countrys WHERE country_name = 'Taiwan');
            """).format(sql.Identifier(field)))
            null_count = cur.fetchone()[0]
            assert null_count == 0, f"欄位 '{field}' 有 {null_count} 筆空值，這是不允許的。"
        cur.close()
    finally:
        if conn:
            conn.close()
    print("✓ 空值檢查測試通過")

def test_data_consistency():
    """測試所有欄位的資料一致性 (CSV 轉換後與資料庫)"""
    print("\n--- 開始資料庫與處理後 CSV 的數據一致性檢查 ---")
    listed_df, _ = try_read_csv('../file/Taiwan_listed_companies_data_processed.csv')
    otc_df, _ = try_read_csv('../file/Taiwan_OTC_companies_data_processed.csv')
    all_companies_df = pd.concat([listed_df, otc_df])
    
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        sector_id_to_name_map = {}
        sector_name_to_id_map = {}
        cur.execute("SELECT sector_id, sector_name FROM Sectors;")
        for id_val, name in cur.fetchall():
            sector_id_to_name_map[id_val] = name
            sector_name_to_id_map[name] = id_val
        
        if '金融保險業' in sector_name_to_id_map:
            sector_name_to_id_map['金融業'] = sector_name_to_id_map['金融保險業']

        fields_to_check = [
            'stock_symbol', 'company_name', 'abbreviation', 'founding_date',
            'listed_date', 'otc_listed_date', 'market', 'address',
            'chairman', 'general_manager', 'spokesperson', 'spokesperson_title',
            'outstanding_common_shares', 'private_placement_common_shares',
            'preferred_shares', 'accounting_firm', 'accountant_1', 'accountant_2',
            'website', 'common_stock_dividend_frequency',
            'common_stock_dividend_decision_level', 'description', 'is_verified', 'sector_id'
        ]

        for idx, company_row in all_companies_df.iterrows():
            # 確保 stock_symbol 始終是字串，並去除空白
            stock_symbol = str(company_row['stock_symbol']).strip() 
            
            try:
                if conn and not conn.autocommit: # 如果不是自動提交，且事務可能中止
                    conn.rollback() # 回滾上一個可能中止的事務，確保當前查詢能執行
                
                cur.execute(f"""
                    SELECT {', '.join(fields_to_check)}
                    FROM Companies
                    WHERE stock_symbol = %s AND country_id = (SELECT country_id FROM Countrys WHERE country_name = 'Taiwan');
                """, (stock_symbol,))
                db_company = cur.fetchone()

                if db_company is None:
                    print(f"錯誤：資料庫中找不到公司 {stock_symbol} 的資料。")
                    return False

                db_data = dict(zip(fields_to_check, db_company))

                for field in fields_to_check:
                    csv_value = company_row.get(field)
                    db_value = db_data.get(field)

                    csv_is_null = pd.isna(csv_value)
                    db_is_null = db_value is None

                    if csv_is_null and db_is_null:
                        continue
                    
                    # 特殊處理 stock_symbol 的類型轉換
                    if field == 'stock_symbol':
                        # 確保兩邊都是字串，並去除空白，再進行比較
                        csv_value = str(csv_value).strip()
                        db_value = str(db_value).strip()


                    if field in ['founding_date', 'listed_date', 'otc_listed_date']:
                        if pd.notna(csv_value):
                            csv_value = pd.to_datetime(csv_value).date()
                    
                    if field in ['outstanding_common_shares', 'private_placement_common_shares', 'preferred_shares']:
                        if pd.notna(csv_value):
                            csv_value = int(csv_value)
                        if db_value is not None:
                            db_value = int(db_value)

                    if field == 'sector_id':
                        if csv_value != db_value:
                            csv_sector_name = sector_id_to_name_map.get(csv_value, f"未知ID({csv_value})")
                            db_sector_name = sector_id_to_name_map.get(db_value, f"未知ID({db_value})")
                            print(f"錯誤：公司 {stock_symbol} 的 {field} (產業) 欄位不一致。")
                            print(f"  精簡版 CSV ID: {csv_value} (名稱: {csv_sector_name})")
                            print(f"  資料庫 ID:    {db_value} (名稱: {db_sector_name})")
                            return False
                        continue 
                    
                    if field == 'market':
                        continue 
                    
                    if field == 'description' and db_is_null and csv_is_null:
                        continue
                    if field == 'is_verified' and db_value is False and (csv_is_null or csv_value is False):
                        continue
                    
                    if isinstance(csv_value, float) and csv_value.is_integer():
                        csv_value = int(csv_value)
                    if isinstance(db_value, float) and db_value.is_integer():
                        db_value = int(db_value)

                    if csv_value != db_value:
                        print(f"\n錯誤：公司 {stock_symbol} 的 '{field}' 欄位不一致。")
                        print(f"  精簡版 CSV 值: {csv_value} (類型: {type(csv_value)})")
                        print(f"  資料庫值:    {db_value} (類型: {type(db_value)})")
                        return False

            except psycopg2.Error as db_err:
                print(f"\n資料庫查詢公司 {stock_symbol} 時發生資料庫錯誤: {db_err}")
                if conn and not conn.autocommit:
                    conn.rollback()
                return False
            except Exception as e:
                print(f"\n處理公司 {stock_symbol} 時發生內部錯誤：{e}")
                return False

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    print("✓ 資料庫與處理後 CSV 的數據一致性檢查完成。")
    return True

if __name__ == "__main__":
    print("開始執行資料一致性測試...")
    try:
        # 檢查精簡版 CSV 與原始 CSV 資料是否一致
        if not check_csv_consistency(
            '../file/Taiwan_listed_companies_data_processed.csv',
            '../file/Taiwan_listed_companies_20250601.csv',
            LISTED_COLUMN_MAPPING,
            LISTED_COLUMNS_TO_DROP
        ):
            print("\n上市公司精簡版與原始 CSV 資料不一致，測試結束。")
            exit(1)
            
        if not check_csv_consistency(
            '../file/Taiwan_OTC_companies_data_processed.csv',
            '../file/Taiwan_OTC_Company_20250601.csv',
            OTC_COLUMN_MAPPING,
            OTC_COLUMNS_TO_DROP
        ):
            print("\n上櫃公司精簡版與原始 CSV 資料不一致，測試結束。")
            exit(1)
        
        print("\n--- 所有 CSV 檔案間的一致性檢查已通過。開始資料庫一致性檢查 ---")

        # 檢查精簡版 CSV 與資料庫資料是否一致
        test_company_count()
        test_market_type()
        test_null_values()
        
        if not test_data_consistency():
            print("\n資料庫與處理後 CSV 的數據一致性測試失敗，請檢查上述錯誤。")
            exit(1)

        print("\n所有測試都通過了！")

    except AssertionError as e:
        print(f"\n測試失敗：{str(e)}")
    except Exception as e:
        print(f"\n執行測試時發生錯誤：{str(e)}")