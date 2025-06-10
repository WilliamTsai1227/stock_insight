import os
import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from datetime import datetime

class QuarterlyCashFlowCrawler:
    def __init__(self):
        self.base_url = "https://mops.twse.com.tw/mops/#/web/t164sb05"
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless') 
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev_shm-usage')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # 定義日誌儲存的子資料夾名稱
        self.log_folder = "cash_flow_quarter_logs"
        # 獲取當前程式檔案所在的目錄
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        # 組合日誌儲存資料夾的完整路徑
        self.log_dir = os.path.join(current_script_dir, self.log_folder)
        # 檢查並創建資料夾，如果它不存在的話
        os.makedirs(self.log_dir, exist_ok=True)

        # 定義數據儲存的子資料夾名稱 (已在 save_data 中定義，這裡僅供參考)
        # self.output_folder = "cash_flow_quarter"
        
    def setup_driver(self):
        return webdriver.Chrome(options=self.chrome_options)

    def _get_logger(self, stock_code, company_name):
        """為每個股票創建一個獨立的日誌記錄器"""
        logger_name = f"{stock_code}_{company_name}_cash_flow_crawler"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO) # 設定日誌級別為 INFO

        # 避免重複添加處理器
        if not logger.handlers:
            # 檔案處理器
            log_file_path = os.path.join(self.log_dir, f"{stock_code}_{company_name}_cash_flow.log")
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)

            # 控制台處理器 (印出到終端機)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(message)s')) # 終端機只印出訊息，更簡潔
            logger.addHandler(console_handler)
        
        return logger

    def _initialize_page_elements(self, driver, stock_code, company_name, logger):
        """初始化頁面元素，現在包含錯誤處理"""
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "companyId"))
            )
            time.sleep(2) # 給予頁面一些時間載入和穩定

            company_id_input = driver.find_element(By.ID, "companyId")
            company_id_input.clear()
            company_id_input.send_keys(stock_code)
            
            time.sleep(2) # 給予頁面足夠時間更新

            custom_radio = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//label[@for='dataType_2']"))
            )
            driver.execute_script("arguments[0].click();", custom_radio)
            logger.info("已選擇 '自訂' 報表類型。")
            time.sleep(2)
            return True  # 成功初始化
            
        except TimeoutException as e:
            logger.error(f"初始化頁面元素時發生 TimeoutException：{e}")
            return False
        except Exception as e:
            logger.error(f"初始化頁面元素時發生未預期錯誤：{e}")
            return False

    def crawl_cash_flow(self, stock_code, company_name, start_year_roc=105, end_year_roc=114):
        logger = self._get_logger(stock_code, company_name) # 獲取該股票的日誌記錄器

        # 將結束年份設定為 114 年，並在迴圈內部控制只到第一季
        target_end_year_roc = 114 
        target_end_quarter = 1 # 修改為只爬取到第一季

        driver = self.setup_driver()
        try:
            driver.get(self.base_url)
            
            # 嘗試初始化頁面元素，如果失敗就跳過這家公司
            max_init_retries = 2
            init_success = False
            
            for init_attempt in range(max_init_retries):
                logger.info(f"嘗試初始化頁面元素 (第 {init_attempt + 1} 次)")
                init_success = self._initialize_page_elements(driver, stock_code, company_name, logger)
                
                if init_success:
                    break
                else:
                    if init_attempt < max_init_retries - 1:
                        logger.warning(f"頁面初始化失敗，重新載入頁面後重試...")
                        driver.get(self.base_url)
                        time.sleep(3)
                    else:
                        logger.error(f"**{stock_code} {company_name} 頁面初始化多次失敗，跳過這家公司**")
                        return  # 直接返回，跳過這家公司
            
            if not init_success:
                logger.error(f"**{stock_code} {company_name} 無法初始化頁面，跳過這家公司**")
                return
            
            # 年份迴圈的範圍是從 start_year_roc 到 target_end_year_roc (包含)
            for year_roc_query in range(start_year_roc, target_end_year_roc + 1):
                quarters_to_crawl = [1, 2, 3, 4] 
                
                # 如果是目標結束年份，則只爬取到指定季度
                if year_roc_query == target_end_year_roc:
                    quarters_to_crawl = [q for q in quarters_to_crawl if q <= target_end_quarter]
                
                # 如果已經處理完目標季度，則跳出年份迴圈
                # 這可以確保 114 年第一季處理完畢後，不會再嘗試其他季度
                if year_roc_query == target_end_year_roc and not quarters_to_crawl:
                    break 

                for quarter_query in quarters_to_crawl:
                    logger.info(f"正在爬取 {stock_code} - 民國 {year_roc_query} 第 {quarter_query} 季（及頁面顯示的同期比較數據）...")
                    
                    max_retries = 1 # 初始嘗試一次，加上重試一次，總共兩次
                    quarter_success = False
                    
                    for attempt in range(max_retries + 1):
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
                            
                            # --- 修正後的邏輯：判斷是資料表格還是查無資料訊息 ---
                            table_xpath = "//div[@class='content']//table"
                            # 使用更精確的 XPath
                            no_data_xpath = "//div[@id='searchBlock']//div[contains(@class, 'SearchResults')]//div[contains(@class, 'stateError')]"

                            WebDriverWait(driver, 15).until(
                                EC.visibility_of_element_located((By.XPATH, table_xpath)) or
                                EC.presence_of_element_located((By.XPATH, no_data_xpath))
                            )

                            # 檢查是否為「查無資料」區塊
                            if driver.find_elements(By.XPATH, no_data_xpath):
                                logger.info(f"爬取 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季：**查無資料**。跳過此季度。")
                                quarter_success = True  # 設為成功，避免重試
                                break # 跳過重試，直接跳到下一個季度
                            
                            # 如果不是「查無資料」，則假定表格已出現，並等待表格內部數據
                            table_element = WebDriverWait(driver, 10).until( # 再次確認表格元素，以防萬一
                                EC.visibility_of_element_located((By.XPATH, table_xpath))
                            )
                            logger.info(f"已找到表格並可見，針對 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季。")

                            expected_data_xpath = f".//tbody//td[contains(normalize-space(), '營業活動之現金流量－間接法')]"
                            WebDriverWait(table_element, 10).until( 
                                EC.presence_of_element_located((By.XPATH, expected_data_xpath))
                            )
                            logger.info(f"已在表格中找到特定數據 '營業活動之現金流量－間接法'。")
                            
                            time.sleep(2) # 給予頁面一些緩衝時間
                            quarter_success = True
                            break # 成功獲取數據，跳出重試迴圈
                        
                        except TimeoutException:
                            if attempt < max_retries:
                                logger.warning(f"爬取 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季：等待數據表格或查無資料訊息逾時。這是第 {attempt + 1} 次嘗試。重新初始化頁面並重試。")
                                driver.get(self.base_url)
                                # 重新初始化頁面，如果失敗就跳過這個季度
                                if not self._initialize_page_elements(driver, stock_code, company_name, logger):
                                    logger.error(f"重新初始化頁面失敗，跳過 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季")
                                    break
                                time.sleep(2) # 重試前稍作等待
                            else:
                                logger.error(f"爬取 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季：**多次嘗試後仍等待數據表格或查無資料訊息逾時。跳過此季度。**")
                                break # 達到最大重試次數，跳過此季度
                        
                        except Exception as e: # 捕捉其他未預期的錯誤
                            if attempt < max_retries:
                                logger.warning(f"爬取 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季數據時發生未預期錯誤：{str(e)}。這是第 {attempt + 1} 次嘗試。重新初始化頁面並重試。")
                                driver.get(self.base_url)
                                # 重新初始化頁面，如果失敗就跳過這個季度
                                if not self._initialize_page_elements(driver, stock_code, company_name, logger):
                                    logger.error(f"重新初始化頁面失敗，跳過 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季")
                                    break
                                time.sleep(2) # 重試前稍作等待
                            else:
                                logger.error(f"爬取 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季數據時發生未預期錯誤：{str(e)}。**多次嘗試後仍失敗。跳過此季度。**", exc_info=True)
                                break # 達到最大重試次數，跳過此季度

                    # --- 數據提取邏輯：同時提取當期和去年同期數據 ---
                    # 只有當成功獲取數據後才執行此部分，否則跳過
                    if quarter_success and driver.find_elements(By.XPATH, table_xpath) and not driver.find_elements(By.XPATH, no_data_xpath):
                        try:
                            table_element = driver.find_element(By.XPATH, table_xpath) # 重新獲取表格元素確保是最新的
                            year_header_cells = table_element.find_element(By.XPATH, ".//thead/tr[1]").find_elements(By.TAG_NAME, "td")
                            
                            data_for_current_period = {} 
                            data_for_prior_period = {}   

                            current_year_col_index = -1
                            prior_year_col_index = -1

                            for i in range(1, len(year_header_cells)):
                                header_text = year_header_cells[i].text
                                if f"{year_roc_query}年" in header_text:
                                    current_year_col_index = i
                                elif f"{year_roc_query - 1}年" in header_text:
                                    prior_year_col_index = i
                            
                            if current_year_col_index == -1:
                                logger.warning(f"無法在表頭中找到當前查詢年份 {year_roc_query} ({stock_code} Q{quarter_query})。")

                            table_rows = table_element.find_elements(By.XPATH, ".//tbody/tr")
                            
                            for row in table_rows:
                                cells = row.find_elements(By.TAG_NAME, "td")
                                
                                item_name = cells[0].text.strip()
                                if not item_name: 
                                    continue 

                                if current_year_col_index != -1 and len(cells) > current_year_col_index:
                                    value_str_current = cells[current_year_col_index].text.strip()
                                    if value_str_current: 
                                        try:
                                            value = int(value_str_current.replace(',', ''))
                                            data_for_current_period[item_name] = value
                                        except ValueError:
                                            pass 

                                if prior_year_col_index != -1 and len(cells) > prior_year_col_index and year_roc_query > start_year_roc:
                                    value_str_prior = cells[prior_year_col_index].text.strip()
                                    if value_str_prior: 
                                        try:
                                            value = int(value_str_prior.replace(',', ''))
                                            data_for_prior_period[item_name] = value
                                        except ValueError:
                                            pass 

                            # 將當期數據保存
                            if data_for_current_period and any(v is not None and v != '' for v in data_for_current_period.values()):
                                self.save_data(stock_code, company_name, year_roc_query, quarter_query, data_for_current_period, logger) # 傳遞 logger
                                logger.info(f"成功保存當期數據：{stock_code} 民國 {year_roc_query} 第 {quarter_query} 季。")
                            else:
                                logger.info(f"未找到或當期數據皆為空值，不保存 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季。")

                            # 將去年同期數據保存
                            if data_for_prior_period and year_roc_query > start_year_roc and any(v is not None and v != '' for v in data_for_prior_period.values()):
                                self.save_data(stock_code, company_name, year_roc_query - 1, quarter_query, data_for_prior_period, logger) # 傳遞 logger
                                logger.info(f"成功保存去年同期（調整後）數據：{stock_code} 民國 {year_roc_query - 1} 第 {quarter_query} 季（來自 {year_roc_query} 第 {quarter_query} 季報表）。")
                            else:
                                logger.info(f"未找到、不適用或去年同期數據皆為空值，不保存 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季的去年同期數據。")
                        except Exception as e:
                            logger.error(f"處理 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季數據時發生錯誤：{e}")
                            logger.info(f"跳過 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季的數據提取與保存")
                    else:
                        logger.info(f"跳過 {stock_code} 民國 {year_roc_query} 第 {quarter_query} 季的數據提取與保存，因前述重試失敗或查無資料。")

        except Exception as e:
            logger.error(f"爬取 {stock_code} {company_name} 時發生未預期的嚴重錯誤：{e}")
            logger.info(f"跳過 {stock_code} {company_name}，繼續處理下一家公司")
        finally:
            driver.quit() # 完成所有爬取後關閉瀏覽器

    def save_data(self, stock_code, company_name, year_roc, quarter, data, logger): # 接收 logger
        # 定義儲存的子資料夾名稱
        output_folder = "cash_flow_quarter"
        
        # 獲取當前程式檔案所在的目錄
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        # 組合目標儲存資料夾的完整路徑
        save_dir = os.path.join(current_script_dir, output_folder)

        # 檢查並創建資料夾，如果它不存在的話
        os.makedirs(save_dir, exist_ok=True) 

        # 檔名使用底線分隔
        filename = f"{stock_code}_{company_name}_現金流量表.json"
        # 組合完整的檔案路徑
        full_path = os.path.join(save_dir, filename)
        
        existing_data = []
        if os.path.exists(full_path): 
            with open(full_path, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list): 
                        existing_data = []
                except json.JSONDecodeError:
                    logger.warning(f"現有檔案 {full_path} 已損壞。將從空數據開始寫入。") # 使用 logger
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
            existing_data.append(new_entry) 

        # 排序確保數據的順序一致性，方便閱讀和管理 (按年份和季度升序)
        existing_data.sort(key=lambda x: (x.get("year_roc", 0), x.get("quarter", 0)))

        with open(full_path, 'w', encoding='utf-8') as f: 
            json.dump(existing_data, f, ensure_ascii=False, indent=2) 

if __name__ == "__main__":
    crawler = QuarterlyCashFlowCrawler()
    
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
            exit(1)
        except Exception as e:
            print(f"載入公司列表時發生未知錯誤：{e}。程式將結束。")
            exit(1)
    else:
        print(f"警告: 找不到 {companies_list_path} 檔案。請先執行 companiesList_extract_from_db.py 建立檔案。程式將結束。")
        exit(1)

    # 這裡使用一個通用的 root logger 來印出進度，每個股票內部則使用各自的 logger
    # 設置 root logger，只印出到終端機
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if not root_logger.handlers: # 避免重複添加
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        root_logger.addHandler(console_handler)

    total_companies = len(companies)
    processed_companies = 0

    for stock_code, company_name in companies.items():
        processed_companies += 1
        root_logger.info(f"\n--- 開始爬取 {stock_code} {company_name} 的季度現金流量表 ({processed_companies}/{total_companies}) ---")
        
        try:
            # 將 end_year_roc 設置為 114，季度判斷邏輯已移至 crawl_cash_flow 內部
            crawler.crawl_cash_flow(stock_code, company_name, start_year_roc=105, end_year_roc=114) 
            root_logger.info(f"--- 完成 {stock_code} {company_name} 的季度現金流量表爬取 ---")
        except Exception as e:
            root_logger.error(f"--- 處理 {stock_code} {company_name} 時發生嚴重錯誤：{e} ---")
            root_logger.info(f"--- 跳過 {stock_code} {company_name}，繼續處理下一家公司 ---")
            continue

    root_logger.info(f"\n=== 所有公司處理完畢 ({processed_companies}/{total_companies}) ===")