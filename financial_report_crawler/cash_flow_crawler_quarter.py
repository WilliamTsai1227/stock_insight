import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from datetime import datetime

class QuarterlyCashFlowCrawler:
    def __init__(self):
        self.base_url = "https://mops.twse.com.tw/mops/#/web/t164sb05"
        self.chrome_options = Options()
        # 建議在開發階段先關閉 headless 模式，方便觀察問題
        # 部署時再開啟
        self.chrome_options.add_argument('--headless') 
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
    def setup_driver(self):
        return webdriver.Chrome(options=self.chrome_options)

    def _initialize_page_elements(self, driver, stock_code, company_name):
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "companyId"))
        )
        time.sleep(2) # 給予頁面一些時間載入和穩定

        company_id_input = driver.find_element(By.ID, "companyId")
        company_id_input.clear()
        company_id_input.send_keys(stock_code)
        
        try:
            # 等待下拉選單的提示文字出現，確保選單已載入
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//div[contains(@class, 'v-list-item')]//div[contains(text(), '{company_name}')]"))
            )
            print(f"下拉選單項目 '{company_name}' 已出現。")
            company_id_input.send_keys(Keys.ENTER)
            print(f"已透過 ENTER 鍵選擇公司 '{company_name}'。")
        except Exception as e:
            print(f"無法找到特定的下拉選單項目 '{company_name}'：{e}。嘗試直接按 ENTER。")
            company_id_input.send_keys(Keys.ENTER)
        
        time.sleep(3) # 給予頁面足夠時間更新

        try:
            custom_radio = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//label[@for='dataType_2']"))
            )
            driver.execute_script("arguments[0].click();", custom_radio)
            print("已選擇 '自訂' 報表類型。")
            time.sleep(2)
        except Exception as e:
            print(f"無法點擊 '自訂' 選項按鈕：{e}")
            raise # 如果這裡失敗，通常代表頁面載入異常，應該停止

    def crawl_cash_flow(self, stock_code, company_name, start_year_roc=109, end_year_roc=114):
        driver = self.setup_driver()
        try:
            driver.get(self.base_url)
            self._initialize_page_elements(driver, stock_code, company_name)
            
            for year_roc_query in range(start_year_roc, end_year_roc + 1): # 這是我們實際在查詢頁面輸入的年份
                # 只有最新一年會爬取到當前進度，之前的年份通常四季都已揭露
                quarters_to_crawl = [1] if year_roc_query == end_year_roc else [1, 2, 3, 4] 

                for quarter_query in quarters_to_crawl: # 這是我們實際在查詢頁面輸入的季度
                    print(f"正在爬取 {stock_code} - 民國 {year_roc_query} 第 {quarter_query} 季（及頁面顯示的同期比較數據）...")
                    try:
                        year_input = WebDriverWait(driver, 10).until( 
                            EC.presence_of_element_located((By.ID, "year"))
                        )
                        year_input.clear()
                        year_input.send_keys(str(year_roc_query))
                        time.sleep(0.5)

                        quarter_select = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, "season"))
                        )
                        quarter_select.click()
                        time.sleep(0.5)

                        quarter_option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, f"//select[@id='season']/option[@value='{quarter_query}']"))
                        )
                        quarter_option.click()
                        time.sleep(1)

                        search_btn = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, "searchBtn"))
                        )
                        driver.execute_script("arguments[0].click();", search_btn)
                        
                        # 定位表格的 XPath，根據您提供的 HTML 片段
                        table_xpath = "//div[@class='content']//table"
                        
                        # 第一步：等待表格本身可見 (visibility_of_element_located)
                        table_element = WebDriverWait(driver, 40).until( # 增加等待時間到40秒，因資料量大可能載入較久
                            EC.visibility_of_element_located((By.XPATH, table_xpath))
                        )
                        print(f"已找到表格並可見，針對 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季。")

                        # 第二步：在表格可見後，等待表格內部特定內容出現 (presence_of_element_located)
                        # 確保關鍵數據行已載入，使用 normalize-space() 更容忍文本中的空白字元
                        expected_data_xpath = f".//tbody//td[contains(normalize-space(), '營業活動之現金流量－間接法')]"
                        WebDriverWait(table_element, 10).until( # 這個等待時間可以短一些，因為表格本身已可見
                            EC.presence_of_element_located((By.XPATH, expected_data_xpath))
                        )
                        print(f"已在表格中找到特定數據 '營業活動之現金流量－間接法'。")
                        
                        time.sleep(2) # 額外等待一下，確保整個表格結構完整載入

                        # --- 數據提取邏輯：同時提取當期和去年同期數據 ---
                        year_header_cells = table_element.find_element(By.XPATH, ".//thead/tr[1]").find_elements(By.TAG_NAME, "td")
                        
                        # 儲存兩個年份的數據字典
                        data_for_current_period = {} # 儲存查詢年 (例如 110Q1) 的數據
                        data_for_prior_period = {}   # 儲存去年同期 (例如 109Q1) 的數據

                        # 找到當期年份和去年同期的欄位索引
                        current_year_col_index = -1
                        prior_year_col_index = -1

                        # 從第二個 td 開始迭代表頭單元格，因為第一個是「會計項目」
                        for i in range(1, len(year_header_cells)):
                            header_text = year_header_cells[i].text
                            if f"{year_roc_query}年" in header_text:
                                current_year_col_index = i
                            elif f"{year_roc_query - 1}年" in header_text:
                                prior_year_col_index = i
                        
                        if current_year_col_index == -1:
                            print(f"警告: 無法在表頭中找到當前查詢年份 {year_roc_query} ({stock_code} Q{quarter_query})。")
                            # 即使當期年份沒找到，如果能找到去年同期，還是可以處理，但建議檢查原因

                        # 獲取 tbody 內的所有數據行
                        table_rows = table_element.find_elements(By.XPATH, ".//tbody/tr")
                        
                        for row in table_rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            
                            item_name = cells[0].text.strip()
                            if not item_name: # 如果項目名稱為空，通常是小計或空白行，跳過
                                continue 

                            # 提取當期數據
                            if current_year_col_index != -1 and len(cells) > current_year_col_index:
                                value_str_current = cells[current_year_col_index].text.strip()
                                if value_str_current: # 確保值不為空
                                    try:
                                        value = int(value_str_current.replace(',', ''))
                                        data_for_current_period[item_name] = value
                                    except ValueError:
                                        pass # 值無法轉換為數字，跳過該項

                            # 提取去年同期數據
                            # 只有當存在去年同期欄位且不是起始年份時才嘗試提取 (起始年份沒有去年同期)
                            if prior_year_col_index != -1 and len(cells) > prior_year_col_index and year_roc_query > start_year_roc:
                                value_str_prior = cells[prior_year_col_index].text.strip()
                                if value_str_prior: # 確保值不為空
                                    try:
                                        value = int(value_str_prior.replace(',', ''))
                                        data_for_prior_period[item_name] = value
                                    except ValueError:
                                        pass # 值無法轉換為數字，跳過該項

                        # 將當期數據保存
                        if data_for_current_period:
                            self.save_data(stock_code, company_name, year_roc_query, quarter_query, data_for_current_period)
                            print(f"成功保存當期數據：{stock_code} 民國 {year_roc_query} 第 {quarter_query} 季。")
                        else:
                            print(f"未找到 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季的當期數據可供儲存。")

                        # 將去年同期數據保存（這將會覆蓋較舊的數據，確保數據來自最新報表的追溯調整）
                        if data_for_prior_period and year_roc_query > start_year_roc:
                            self.save_data(stock_code, company_name, year_roc_query - 1, quarter_query, data_for_prior_period)
                            print(f"成功保存去年同期（調整後）數據：{stock_code} 民國 {year_roc_query - 1} 第 {quarter_query} 季（來自 {year_roc_query} 第 {quarter_query} 季報表）。")
                        else:
                            # 針對起始年份，通常沒有去年的數據，因此這條訊息是正常的
                            print(f"未找到或不適用 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季的去年同期數據可供儲存。")
                        
                    except Exception as e:
                        print(f"爬取 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季數據時發生錯誤：{str(e)}")
                        # 發生錯誤時，重新載入頁面並重新執行初始化步驟，以嘗試恢復
                        driver.get(self.base_url)
                        self._initialize_page_elements(driver, stock_code, company_name)
                        continue # 繼續下一個季度的爬取
                    
        finally:
            driver.quit() # 完成所有爬取後關閉瀏覽器

    def save_data(self, stock_code, company_name, year_roc, quarter, data):
        # 定義儲存的子資料夾名稱
        output_folder = "cash_flow_quarter"
        
        # 獲取當前程式檔案所在的目錄
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        # 組合目標儲存資料夾的完整路徑
        save_dir = os.path.join(current_script_dir, output_folder)

        # 檢查並創建資料夾，如果它不存在的話
        os.makedirs(save_dir, exist_ok=True) # exist_ok=True 避免資料夾已存在時報錯

        # 檔名使用底線分隔
        filename = f"{stock_code}_{company_name}_現金流量表.json"
        # 組合完整的檔案路徑
        full_path = os.path.join(save_dir, filename)
        
        existing_data = []
        if os.path.exists(full_path): # 判斷檔案是否存在時也要使用完整路徑
            with open(full_path, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list): # 確保讀取的是列表，避免格式錯誤
                        existing_data = []
                except json.JSONDecodeError:
                    print(f"警告: 現有檔案 {full_path} 已損壞。將從空數據開始寫入。")
                    existing_data = []
        
        new_entry = {
            "year_roc": year_roc, 
            "quarter": quarter,
            "data": data
        }
        
        found = False
        for i, entry in enumerate(existing_data):
            # 找到相同的年份和季度，就覆蓋
            if entry.get("year_roc") == year_roc and entry.get("quarter") == quarter:
                existing_data[i] = new_entry
                found = True
                break
        
        if not found:
            existing_data.append(new_entry) # 如果沒有找到，就新增

        # 排序確保數據的順序一致性，方便閱讀和管理 (按年份和季度升序)
        existing_data.sort(key=lambda x: (x.get("year_roc", 0), x.get("quarter", 0)))

        with open(full_path, 'w', encoding='utf-8') as f: # 開啟檔案時也要使用完整路徑
            json.dump(existing_data, f, ensure_ascii=False, indent=2) # 以美觀的格式儲存 JSON

if __name__ == "__main__":
    crawler = QuarterlyCashFlowCrawler()
    
    # --- 修正後的程式碼：讀取 companies_list.json ---
    companies_list_file = 'companies_list.json'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    companies_list_path = os.path.join(script_dir, companies_list_file)

    companies = {}
    if os.path.exists(companies_list_path):
        try:
            with open(companies_list_path, 'r', encoding='utf-8') as f:
                companies = json.load(f)
            print(f"成功從 {companies_list_path} 載入公司列表。")
        except json.JSONDecodeError:
            print(f"錯誤: {companies_list_path} 檔案格式不正確，請檢查。程式將結束。")
            exit(1) # 直接退出程式，不使用備用值
        except Exception as e:
            print(f"載入公司列表時發生未知錯誤：{e}。程式將結束。")
            exit(1) # 直接退出程式，不使用備用值
    else:
        print(f"警告: 找不到 {companies_list_path} 檔案。請先執行 companiesList_extract_from_db.py 建立檔案。程式將結束。")
        exit(1) # 直接退出程式，不使用備用值
    # --- 結束修正程式碼 ---

    for stock_code, company_name in companies.items():
        print(f"\n--- 開始爬取 {stock_code} {company_name} 的季度現金流量表 ---")
        crawler.crawl_cash_flow(stock_code, company_name, start_year_roc=109, end_year_roc=114)
        print(f"--- 完成 {stock_code} {company_name} 的季度現金流量表爬取 ---")