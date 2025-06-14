import os
import json
import time
import logging
import boto3 # <-- 新增：導入 boto3 函式庫
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException # 新增 WebDriverException
from datetime import datetime

# --- 配置區塊：建議透過環境變數或專門的配置檔案管理這些值 ---
# 您應將這些值設定為環境變數，以在 Docker/ECS 中動態注入
# 例如在 Dockerfile 或 ECS Task Definition 中設定
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2') # AWS 區域
S3_BUCKET_NAME = os.environ.get('Financial_Report_S3_BUCKET_NAME') #  S3 儲存桶名稱
S3_RAW_DATA_PREFIX = os.environ.get('Financial_Report_S3_RAW_DATA_PREFIX') # S3 資料夾路徑
SQS_QUEUE_URL = os.environ.get('SQS_CASH_FLOW_QUEUE_URL') #  SQS 佇列 URL

# --- 移除本地日誌資料夾的定義，改為輸出到標準輸出/CloudWatch ---
# self.log_folder 和 self.log_dir 已經被移除

class QuarterlyCashFlowCrawler:
    def __init__(self):
        self.base_url = "https://mops.twse.com.tw/mops/#/web/t164sb05"
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless') 
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev_shm-usage')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # S3 客戶端
        self.s3_client = boto3.client('s3', region_name=AWS_REGION)
        # SQS 客戶端
        self.sqs_client = boto3.client('sqs', region_name=AWS_REGION)

        # 主要日誌處理器：直接輸出到控制台 (stdout)，以便 CloudWatch Logs 收集
        self._setup_root_logger()
        # 爬蟲執行時，每個公司仍然會使用一個獨立的 logger 實例，方便追蹤
        
    def _setup_root_logger(self):
        """設定根日誌記錄器，輸出到標準輸出"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        # 清除所有現有的 handlers，確保只使用 StreamHandler
        if root_logger.handlers:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
        
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    def _get_logger(self, stock_code, company_name):
        """為每個股票創建一個獨立的日誌記錄器，但仍輸出到標準輸出"""
        logger_name = f"{stock_code}_{company_name}_cash_flow_crawler"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        # 確保不會為每個股票重複添加 StreamHandler
        if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
            console_handler = logging.StreamHandler()
            # 這裡的格式可以更詳細，包含股票代碼，方便在 CloudWatch 中篩選
            console_formatter = logging.Formatter(f'%(asctime)s - %(levelname)s - [{stock_code} {company_name}] - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger

    def setup_driver(self):
        # 這裡可以加入一些錯誤處理，例如 ChromeDriver 不存在
        try:
            return webdriver.Chrome(options=self.chrome_options)
        except WebDriverException as e:
            logging.error(f"無法啟動 ChromeDriver: {e}. 請確認 ChromeDriver 已正確安裝且版本相容。")
            raise

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
            logger.error(f"初始化頁面元素時發生未預期錯誤：{e}", exc_info=True)
            return False

    def crawl_cash_flow(self, stock_code, company_name, start_year_roc=105, end_year_roc=114):
        logger = self._get_logger(stock_code, company_name)

        target_end_year_roc = 114 
        target_end_quarter = 1 

        driver = None # 初始化為 None
        try:
            driver = self.setup_driver()
            driver.get(self.base_url)
            
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
                        logger.error(f"**頁面初始化多次失敗，跳過此公司**")
                        return  # 直接返回，跳過這家公司
            
            if not init_success:
                logger.error(f"**無法初始化頁面，跳過此公司**")
                return
            
            for year_roc_query in range(start_year_roc, target_end_year_roc + 1):
                quarters_to_crawl = [1, 2, 3, 4] 
                
                if year_roc_query == target_end_year_roc:
                    quarters_to_crawl = [q for q in quarters_to_crawl if q <= target_end_quarter]
                
                if year_roc_query == target_end_year_roc and not quarters_to_crawl:
                    break 

                for quarter_query in quarters_to_crawl:
                    logger.info(f"正在爬取 民國 {year_roc_query} 第 {quarter_query} 季...")
                    
                    max_retries = 1
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
                            
                            table_xpath = "//div[@class='content']//table"
                            no_data_xpath = "//div[@id='searchBlock']//div[contains(@class, 'SearchResults')]//div[contains(@class, 'stateError')]"

                            WebDriverWait(driver, 15).until(
                                EC.visibility_of_element_located((By.XPATH, table_xpath)) or
                                EC.presence_of_element_located((By.XPATH, no_data_xpath))
                            )

                            if driver.find_elements(By.XPATH, no_data_xpath):
                                logger.info(f"爬取 民國 {year_roc_query} 第 {quarter_query} 季：**查無資料**。跳過此季度。")
                                quarter_success = True
                                break 
                            
                            table_element = WebDriverWait(driver, 10).until( 
                                EC.visibility_of_element_located((By.XPATH, table_xpath))
                            )
                            logger.info(f"已找到表格並可見，針對 民國 {year_roc_query} 第 {quarter_query} 季。")

                            expected_data_xpath = f".//tbody//td[contains(normalize-space(), '營業活動之現金流量－間接法')]"
                            WebDriverWait(table_element, 10).until( 
                                EC.presence_of_element_located((By.XPATH, expected_data_xpath))
                            )
                            logger.info(f"已在表格中找到特定數據 '營業活動之現金流量－間接法'。")
                            
                            time.sleep(2)
                            quarter_success = True
                            break 
                        
                        except TimeoutException:
                            if attempt < max_retries:
                                logger.warning(f"爬取 民國 {year_roc_query} 第 {quarter_query} 季：等待數據表格或查無資料訊息逾時。這是第 {attempt + 1} 次嘗試。重新載入頁面並重試。")
                                driver.get(self.base_url)
                                if not self._initialize_page_elements(driver, stock_code, company_name, logger):
                                    logger.error(f"重新初始化頁面失敗，跳過 民國 {year_roc_query} 第 {quarter_query} 季")
                                    break
                                time.sleep(2)
                            else:
                                logger.error(f"爬取 民國 {year_roc_query} 第 {quarter_query} 季：**多次嘗試後仍等待數據表格或查無資料訊息逾時。跳過此季度。**")
                                break
                        
                        except Exception as e:
                            if attempt < max_retries:
                                logger.warning(f"爬取 民國 {year_roc_query} 第 {quarter_query} 季數據時發生未預期錯誤：{str(e)}。這是第 {attempt + 1} 次嘗試。重新載入頁面並重試。")
                                driver.get(self.base_url)
                                if not self._initialize_page_elements(driver, stock_code, company_name, logger):
                                    logger.error(f"重新初始化頁面失敗，跳過 民國 {year_roc_query} 第 {quarter_query} 季")
                                    break
                                time.sleep(2)
                            else:
                                logger.error(f"爬取 民國 {year_roc_query} 第 {quarter_query} 季數據時發生未預期錯誤：{str(e)}。**多次嘗試後仍失敗。跳過此季度。**", exc_info=True)
                                break

                    if quarter_success and driver.find_elements(By.XPATH, table_xpath) and not driver.find_elements(By.XPATH, no_data_xpath):
                        try:
                            table_element = driver.find_element(By.XPATH, table_xpath)
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
                                logger.warning(f"無法在表頭中找到當前查詢年份 {year_roc_query}。")

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

                            # 將當期數據保存到 S3
                            if data_for_current_period and any(v is not None and v != '' for v in data_for_current_period.values()):
                                self.save_data_to_s3(stock_code, company_name, year_roc_query, quarter_query, data_for_current_period, logger)
                                logger.info(f"成功保存當期數據至 S3：民國 {year_roc_query} 第 {quarter_query} 季。")
                            else:
                                logger.info(f"未找到或當期數據皆為空值，不保存 民國 {year_roc_query} 第 {quarter_query} 季。")

                            # 將去年同期數據保存到 S3
                            if data_for_prior_period and year_roc_query > start_year_roc and any(v is not None and v != '' for v in data_for_prior_period.values()):
                                # 注意：此處保存的是前一年度的數據，S3 Key 也應反映前一年度
                                self.save_data_to_s3(stock_code, company_name, year_roc_query - 1, quarter_query, data_for_prior_period, logger, is_prior_year_data=True)
                                logger.info(f"成功保存去年同期（調整後）數據至 S3：民國 {year_roc_query - 1} 第 {quarter_query} 季（來自 {year_roc_query} 第 {quarter_query} 季報表）。")
                            else:
                                logger.info(f"未找到、不適用或去年同期數據皆為空值，不保存 民國 {year_roc_query} 第 {quarter_query} 季的去年同期數據。")
                        except Exception as e:
                            logger.error(f"處理 民國 {year_roc_query} 第 {quarter_query} 季數據時發生錯誤：{e}", exc_info=True)
                            logger.info(f"跳過 民國 {year_roc_query} 第 {quarter_query} 季的數據提取與保存")
                    else:
                        logger.info(f"跳過 民國 {year_roc_query} 第 {quarter_query} 季的數據提取與保存，因前述重試失敗或查無資料。")

        except WebDriverException as e:
            logger.error(f"WebDriver 發生嚴重錯誤（可能瀏覽器崩潰或無法啟動）：{e}", exc_info=True)
        except Exception as e:
            logger.error(f"爬取時發生未預期的嚴重錯誤：{e}", exc_info=True)
        finally:
            if driver:
                driver.quit() # 完成所有爬取後關閉瀏覽器

    # --- 修改 save_data 方法為 save_data_to_s3 ---
    def save_data_to_s3(self, stock_code, company_name, year_roc, quarter, data, logger, is_prior_year_data=False):
        # 檔名使用底線分隔
        # 這裡的 filename 應為 S3 的物件 Key 的一部分
        # S3 Key 格式：financial-report/raw-data/cash_flow/2330_2024Q1_cash_flow.json
        s3_object_key = f"{S3_RAW_DATA_PREFIX}{stock_code}_{year_roc}Q{quarter}_cash_flow.json"
        
        # 構建要保存的數據結構
        # 建議直接保存包含元數據的單一 JSON 物件，而不是僅數據本身
        # 這樣每個 S3 物件就是一個完整的數據單元
        json_data = {
            "stock_code": stock_code,
            "company_name": company_name,
            "year_roc": year_roc,
            "quarter": quarter,
            "data": data,
            "crawled_at": datetime.now().isoformat() # 記錄爬取時間
        }
        
        try:
            # 將 JSON 數據轉換為字串
            json_payload = json.dumps(json_data, ensure_ascii=False, indent=2)
            
            # 上傳到 S3。如果 Key 相同，S3 會直接覆蓋，實現冪等性
            self.s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_object_key,
                Body=json_payload.encode('utf-8'), # S3 put_object 需要 bytes
                ContentType='application/json'
            )
            logger.info(f"數據成功上傳至 S3: {s3_object_key}")
        except Exception as e:
            logger.error(f"上傳數據至 S3 失敗: {s3_object_key} - {e}", exc_info=True)
            # 在實際生產環境中，這裡可能需要將失敗的任務重新放回 SQS 或記錄到死信佇列 (DLQ)

# --- 主程式入口點：修改為從 SQS 接收訊息 ---
if __name__ == "__main__":
    crawler = QuarterlyCashFlowCrawler()
    
    # 設置 SQS 接收訊息的參數
    # MaxNumberOfMessages: 每次拉取多少條訊息 (最多10條)
    # VisibilityTimeout: 訊息在佇列中對其他消費者不可見的時間 (秒)。這需要根據您的爬蟲處理一條訊息的時間來設定
    # WaitTimeSeconds: 長輪詢 (long polling) 時間 (最多20秒)，避免短輪詢的額外費用和請求
    max_messages = 1
    visibility_timeout_seconds = 900 # 假設爬取一家公司最多15分鐘 (900秒)
    wait_time_seconds = 20 # 長輪詢，減少空請求

    no_message_count = 0
    max_no_message_attempts = 3 # 設定連續沒有訊息的次數上限

    root_logger = logging.getLogger() # 使用根日誌記錄器來記錄 SQS 相關訊息

    while True:
        try:
            # 從 SQS 佇列拉取訊息
            root_logger.info(f"正在從 SQS 佇列 {SQS_QUEUE_URL} 接收訊息...")
            response = crawler.sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=max_messages,
                VisibilityTimeout=visibility_timeout_seconds,
                WaitTimeSeconds=wait_time_seconds
            )
            
            messages = response.get('Messages', [])
            
            if not messages:
                no_message_count += 1
                root_logger.info("沒有可用的 SQS 訊息，等待...")
                if no_message_count >= max_no_message_attempts:
                    root_logger.info(f"連續 {max_no_message_attempts} 次沒有收到 SQS 訊息，停止任務以節省成本。") # 加入退出機制，連續 N 次沒有訊息就退出，或等待特定時間後退出節省成本
                    break # 跳出 while True 迴圈，程式結束                  
                time.sleep(wait_time_seconds) # 沒有訊息時稍作等待
                continue
                
            no_message_count = 0 #重置計數器

            for message in messages:
                receipt_handle = message['ReceiptHandle'] # 訊息的唯一識別符，用於刪除訊息
                
                try:
                    # 解析訊息內容，預期是 JSON 格式
                    message_body = json.loads(message['Body'])
                    stock_code = message_body.get('stock_code')
                    company_name = message_body.get('company_name')

                    if stock_code and company_name:
                        root_logger.info(f"\n--- 從 SQS 接收任務：開始爬取 {stock_code} {company_name} ---")
                        # 執行爬蟲邏輯
                        crawler.crawl_cash_flow(stock_code, company_name, start_year_roc=105, end_year_roc=114) 
                        
                        # 爬蟲成功完成後，刪除 SQS 訊息
                        crawler.sqs_client.delete_message(
                            QueueUrl=SQS_QUEUE_URL,
                            ReceiptHandle=receipt_handle
                        )
                        root_logger.info(f"--- 完成 {stock_code} {company_name} 爬取，並已從 SQS 佇列中刪除訊息 ---")
                    else:
                        root_logger.warning(f"SQS 訊息格式不正確，缺少 stock_code 或 company_name: {message['Body']}")
                        # 對於格式不正確的訊息，也可以選擇移至死信佇列
                        crawler.sqs_client.delete_message(
                            QueueUrl=SQS_QUEUE_URL,
                            ReceiptHandle=receipt_handle
                        )

                except json.JSONDecodeError:
                    root_logger.error(f"SQS 訊息體不是有效的 JSON 格式: {message['Body']}. 將刪除此訊息以避免重複錯誤。", exc_info=True)
                    # 刪除無法解析的訊息，避免重複錯誤
                    crawler.sqs_client.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=receipt_handle
                    )
                except Exception as e:
                    root_logger.error(f"處理 SQS 訊息或執行爬蟲時發生錯誤: {e}", exc_info=True)
                    # 如果這裡發生錯誤，訊息將在 VisibilityTimeout 後重新可見，並被重新處理
                    # 如果是持續性錯誤，訊息將會進入死信佇列 (可再配置)
                    root_logger.info(f"任務處理失敗，訊息將在 {visibility_timeout_seconds} 秒後重新可見。")
        
        except Exception as e:
            root_logger.critical(f"與 SQS 服務互動時發生嚴重錯誤: {e}", exc_info=True)
            root_logger.info("程式將在短暫等待後重試 SQS 連接...")
            time.sleep(5) # 發生 SQS 相關錯誤時等待一下再重試