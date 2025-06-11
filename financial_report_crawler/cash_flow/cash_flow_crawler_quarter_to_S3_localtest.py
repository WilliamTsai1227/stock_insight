import os
import json
import time
import logging
import boto3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException
from datetime import datetime
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

# --- 配置區塊：建議透過環境變數或專門的配置檔案管理這些值 ---
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2') # AWS 區域 (從 .env 或系統環境讀取)
S3_BUCKET_NAME = os.environ.get('Financial_Report_S3_BUCKET_NAME') # 從 .env 或系統環境讀取
S3_RAW_DATA_PREFIX = os.environ.get('Financial_Report_S3_RAW_DATA_PREFIX', 'raw-data/cash_flow/') # 從 .env 或系統環境讀取
SQS_QUEUE_URL = os.environ.get('SQS_CASH_FLOW_QUEUE_URL') # 從 .env 或系統環境讀取 (本地測試此值不會被用到)

# --- 新增：明確從 .env 讀取您自訂的 S3 憑證變數 ---
AWS_S3_ACCESS_KEY_ID = os.getenv('aws_s3_access_key_id')
AWS_S3_SECRET_ACCESS_KEY = os.getenv('aws_s3_secret_access_key')
# --------------------------------------------------------

class QuarterlyCashFlowCrawler:
    def __init__(self):
        self.base_url = "https://mops.twse.com.tw/mops/#/web/t164sb05"
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev_shm-usage')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # S3 客戶端：現在明確地傳遞自訂的 Access Key ID 和 Secret Access Key
        self.s3_client = boto3.client(
            's3',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_S3_SECRET_ACCESS_KEY
        )
        # SQS 客戶端：如果未來要用 SQS，也可能需要類似的憑證傳遞方式
        self.sqs_client = boto3.client('sqs', region_name=AWS_REGION) 

        self._setup_root_logger()
        
    def _setup_root_logger(self):
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        if root_logger.handlers:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
        
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    def _get_logger(self, stock_code, company_name):
        logger_name = f"{stock_code}_{company_name}_cash_flow_crawler"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(f'%(asctime)s - %(levelname)s - [{stock_code} {company_name}] - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger

    def setup_driver(self):
        try:
            return webdriver.Chrome(options=self.chrome_options)
        except WebDriverException as e:
            logging.error(f"無法啟動 ChromeDriver: {e}. 請確認 ChromeDriver 已正確安裝且版本相容。")
            raise

    def _initialize_page_elements(self, driver, stock_code, company_name, logger):
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "companyId"))
            )
            time.sleep(2)

            company_id_input = driver.find_element(By.ID, "companyId")
            company_id_input.clear()
            company_id_input.send_keys(stock_code)
            
            time.sleep(2)

            custom_radio = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//label[@for='dataType_2']"))
            )
            driver.execute_script("arguments[0].click();", custom_radio)
            logger.info("已選擇 '自訂' 報表類型。")
            time.sleep(2)
            return True
            
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

        driver = None
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
                        return
            
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
                driver.quit()

    def save_data_to_s3(self, stock_code, company_name, year_roc, quarter, data, logger, is_prior_year_data=False):
        s3_object_key = f"{S3_RAW_DATA_PREFIX}{stock_code}_{year_roc}Q{quarter}_cash_flow.json"
        
        json_data = {
            "stock_code": stock_code,
            "company_name": company_name,
            "year_roc": year_roc,
            "quarter": quarter,
            "data": data,
            "crawled_at": datetime.now().isoformat()
        }
        
        try:
            json_payload = json.dumps(json_data, ensure_ascii=False, indent=2)
            
            self.s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_object_key,
                Body=json_payload.encode('utf-8'),
                ContentType='application/json'
            )
            logger.info(f"數據成功上傳至 S3: {s3_object_key}")
        except Exception as e:
            logger.error(f"上傳數據至 S3 失敗: {s3_object_key} - {e}", exc_info=True)

# --- 主程式入口點：讀取本地檔案執行爬蟲 ---
if __name__ == "__main__":
    crawler = QuarterlyCashFlowCrawler()
    
    companies_list_file = 'companies_list_source.json' # 本地檔案名稱

    try:
        with open(companies_list_file, 'r', encoding='utf-8') as f:
            companies = json.load(f)
        
        root_logger = logging.getLogger()
        root_logger.info(f"從本地檔案 '{companies_list_file}' 載入公司列表，共 {len(companies)} 筆。")

        for stock_code, company_name in companies.items():
            root_logger.info(f"\n--- 開始本地測試爬取任務：{stock_code} {company_name} ---")
            crawler.crawl_cash_flow(stock_code, company_name, start_year_roc=105, end_year_roc=114)
            root_logger.info(f"--- 完成本地測試爬取任務：{stock_code} {company_name} ---")

    except FileNotFoundError:
        logging.error(f"錯誤: 找不到公司列表檔案 '{companies_list_file}'。請確認檔案是否存在於相同目錄。")
    except json.JSONDecodeError:
        logging.error(f"錯誤: 公司列表檔案 '{companies_list_file}' 格式不正確，無法解析 JSON。", exc_info=True)
    except Exception as e:
        logging.critical(f"本地測試時發生未預期的嚴重錯誤: {e}", exc_info=True)