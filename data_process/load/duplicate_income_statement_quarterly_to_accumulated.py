import psycopg2
import os

# 資料庫連線配置
DB_CONFIG = {
    'host': 'localhost', # 通常本地資料庫為 localhost
    'database': os.getenv('PostgreSQL_DB_NAME'),
    'user': os.getenv('PostgreSQL_DB_USER'),
    'password': os.getenv('PostgreSQL_DB_PASSWORD'),
    'port': os.getenv('PostgreSQL_DB_PORT')
}

def duplicate_quarterly_to_accumulated():
    """
    從 Income_Statements 表中選取 report_type='quarterly' 且 quarter=1 的資料，
    複製一份並將 report_type 改為 'accumulated' 後插入回表中。
    """
    conn = None
    cur = None
    try:
        # 建立資料庫連線
        print("正在連線到資料庫...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("資料庫連線成功。")

        # 1. 選取符合條件的資料
        select_sql = """
        SELECT
            company_id, year, quarter, original_currency,
            revenue, revenue_pct, cost_of_revenue, cost_of_revenue_pct,
            gross_profit, gross_profit_pct, sales_expenses, sales_expenses_pct,
            administrative_expenses, administrative_expenses_pct,
            research_and_development_expenses, research_and_development_expenses_pct,
            operating_expenses, operating_expenses_pct, operating_income, operating_income_pct,
            pre_tax_income, pre_tax_income_pct, net_income, net_income_pct,
            net_income_attributable_to_parent, net_income_attributable_to_parent_pct,
            basic_eps, diluted_eps
        FROM
            Income_Statements
        WHERE
            report_type = 'quarterly' AND quarter = 1;
        """
        cur.execute(select_sql)
        rows = cur.fetchall()

        if not rows:
            print("沒有找到 report_type='quarterly' 且 quarter=1 的資料。")
            return

        print(f"找到 {len(rows)} 筆符合條件的資料，準備複製並插入。")

        # 2. 準備插入新的資料
        insert_sql = """
        INSERT INTO Income_Statements (
            company_id, report_type, year, quarter, original_currency,
            revenue, revenue_pct, cost_of_revenue, cost_of_revenue_pct,
            gross_profit, gross_profit_pct, sales_expenses, sales_expenses_pct,
            administrative_expenses, administrative_expenses_pct,
            research_and_development_expenses, research_and_development_expenses_pct,
            operating_expenses, operating_expenses_pct, operating_income, operating_income_pct,
            pre_tax_income, pre_tax_income_pct, net_income, net_income_pct,
            net_income_attributable_to_parent, net_income_attributable_to_parent_pct,
            basic_eps, diluted_eps
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s
        );
        """
        
        new_records = []
        for row in rows:
            # 複製現有資料，並將 report_type 改為 'accumulated'
            # income_id 是 SERIAL PRIMARY KEY，資料庫會自動處理，所以不包含在 INSERT 語句中
            new_record = (
                row[0], # company_id
                'accumulated', # report_type 更改為 'accumulated'
                row[1], # year
                row[2], # quarter (保持為 1)
                row[3], # original_currency
                row[4], row[5], row[6], row[7], # revenue, revenue_pct, cost_of_revenue, cost_of_revenue_pct
                row[8], row[9], row[10], row[11], # gross_profit, gross_profit_pct, sales_expenses, sales_expenses_pct
                row[12], row[13], # administrative_expenses, administrative_expenses_pct
                row[14], row[15], # research_and_development_expenses, research_and_development_expenses_pct
                row[16], row[17], # operating_expenses, operating_expenses_pct
                row[18], row[19], # operating_income, operating_income_pct
                row[20], row[21], # pre_tax_income, pre_tax_income_pct
                row[22], row[23], # net_income, net_income_pct
                row[24], row[25], # net_income_attributable_to_parent, net_income_attributable_to_parent_pct
                row[26], row[27]  # basic_eps, diluted_eps
            )
            new_records.append(new_record)

        # 3. 執行批量插入
        cur.executemany(insert_sql, new_records)
        conn.commit() # 提交事務

        print(f"成功插入 {len(new_records)} 筆新的 'accumulated' 損益表資料。")

    except psycopg2.Error as e:
        print(f"資料庫操作錯誤: {e}")
        if conn:
            conn.rollback() # 回滾事務以防錯誤
    except Exception as e:
        print(f"發生未知錯誤: {e}")
    finally:
        # 關閉連線
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("資料庫連線已關閉。")

if __name__ == "__main__":
    # 執行腳本
    duplicate_quarterly_to_accumulated()
