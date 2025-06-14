from dotenv import load_dotenv, find_dotenv # 引入 find_dotenv
import psycopg2
import json
import os

# 載入 .env 檔案中的環境變數。find_dotenv() 會自動向上尋找 .env 檔案。
load_dotenv(find_dotenv()) 

def generate_companies_list_json(output_filename='companies_list_source.json'):
    """
    從資料庫讀取股票代碼和公司名稱，並儲存為 JSON 字典格式。
    資料庫連接配置從環境變數中讀取。

    Args:
        output_filename (str): 輸出 JSON 檔案的名稱。
    """
    companies = {}
    conn = None
    try:
        # 從環境變數讀取資料庫配置
        db_config = {
            'host': os.getenv('PostgreSQL_DB_HOST'),
            'database': os.getenv('PostgreSQL_DB_NAME'),
            'user': os.getenv('PostgreSQL_DB_USER'),
            'password': os.getenv('PostgreSQL_DB_PASSWORD'), # 允許密碼為空字串
            'port': os.getenv('PostgreSQL_DB_PORT')
        }

        # --- 修正這裡的環境變數檢查邏輯 ---
        missing_vars = []
        if not db_config['host']:
            missing_vars.append('PostgreSQL_DB_HOST')
        if not db_config['database']:
            missing_vars.append('PostgreSQL_DB_NAME')
        if not db_config['user']:
            missing_vars.append('PostgreSQL_DB_USER')
        # 對於密碼，檢查 key 是否存在，因為空字串是合法的
        if 'password' not in os.environ and db_config['password'] is None:
             missing_vars.append('PostgreSQL_DB_PASSWORD')
        if not db_config['port']:
            missing_vars.append('PostgreSQL_DB_PORT')
            
        if missing_vars:
            print(f"錯誤：以下資料庫連接環境變數未設定或為空字串：{', '.join(missing_vars)}。")
            print("請確保所有必要的資料庫連接環境變數已在 .env 檔案中正確設定。")
            return
        # --- 修正檢查邏輯結束 ---

        # 連接資料庫
        print(f"正在連接資料庫 (Host: {db_config['host']}, DB: {db_config['database']}, User: {db_config['user']})...")
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()

        # 執行查詢，只選擇 stock_symbol 和 company_name
        print("正在查詢 Companies 表格以獲取股票代碼與公司名稱...")
        cur.execute("SELECT stock_symbol, company_name FROM Companies;")
        
        # 遍歷查詢結果
        for row in cur:
            stock_symbol = row[0]
            company_name = row[1]
            companies[stock_symbol] = company_name
        
        # 獲取當前腳本所在的目錄
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, output_filename)

        # 將字典寫入 JSON 檔案
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(companies, f, ensure_ascii=False, indent=4)
        
        print(f"成功生成 {output_filename}，共 {len(companies)} 筆公司資料。")

    except psycopg2.OperationalError as e:
        print(f"資料庫連接失敗，請檢查資料庫憑證、網路連接或資料庫服務狀態：{e}")
    except Exception as e:
        print(f"處理過程中發生錯誤：{e}")
    finally:
        if conn:
            cur.close()
            conn.close()
            print("資料庫連接已關閉。")

if __name__ == "__main__":
    generate_companies_list_json()