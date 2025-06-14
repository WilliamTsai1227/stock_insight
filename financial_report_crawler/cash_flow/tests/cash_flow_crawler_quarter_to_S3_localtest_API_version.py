import os
import json
import time
import logging
import boto3
import requests # 新增：引入 requests 函式庫
from datetime import datetime
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

# --- 配置區塊：建議透過環境變數或專門的配置檔案管理這些值 ---
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
S3_BUCKET_NAME = os.environ.get('Financial_Report_S3_BUCKET_NAME')
S3_RAW_DATA_PREFIX = os.environ.get('Financial_Report_S3_RAW_DATA_PREFIX', 'raw-data/cash_flow/')

AWS_S3_ACCESS_KEY_ID = os.getenv('aws_s3_access_key_id')
AWS_S3_SECRET_ACCESS_KEY = os.getenv('aws_s3_secret_access_key')
# --------------------------------------------------------

class QuarterlyCashFlowAPICrawler:
    def __init__(self):
        self.api_url = "https://mops.twse.com.tw/mops/api/t164sb05"
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-TW,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Host": "mops.twse.com.tw",
            "Origin": "https://mops.twse.com.tw",
            "Pragma": "no-cache",
            "Referer": "https://mops.twse.com.tw/mops/#/web/t164sb05", # 增加 Referer
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\""
        }
        
        self.s3_client = boto3.client(
            's3',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_S3_SECRET_ACCESS_KEY
        )

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
        logger_name = f"{stock_code}_{company_name}_cash_flow_api_crawler"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(f'%(asctime)s - %(levelname)s - [{stock_code} {company_name}] - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger

    def fetch_data_from_api(self, stock_code, year_roc, quarter, logger):
        payload = {
            "companyId": stock_code,
            "dataType": "2", # 2 表示自訂報表
            "season": str(quarter),
            "year": str(year_roc),
            "subsidiaryCompanyId": ""
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=15)
            response.raise_for_status() # 對於 4xx/5xx 錯誤會拋出 HTTPError
            
            json_response = response.json()
            
            if json_response.get('code') == 200 and json_response.get('result'):
                return json_response['result']
            elif json_response.get('message') == "查詢無資料":
                logger.info(f"API 查詢 民國 {year_roc} 第 {quarter} 季：查無資料。")
                return None
            else:
                logger.warning(f"API 回應非成功狀態碼或無結果：{json_response.get('code')} - {json_response.get('message')}")
                return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"API 請求失敗，HTTP 狀態碼：{e.response.status_code} - {e.response.text}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"API 連線錯誤：{e}")
            return None
        except requests.exceptions.Timeout as e:
            logger.error(f"API 請求超時：{e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"API 回應非 JSON 格式：{e} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"API 請求發生未預期錯誤：{e}", exc_info=True)
            return None

    def crawl_cash_flow(self, stock_code, company_name, start_year_roc=105, end_year_roc=114):
        logger = self._get_logger(stock_code, company_name)

        target_end_year_roc = 114 # 截止年 (民國)
        target_end_quarter = 1   # 截止季

        for year_roc_query in range(start_year_roc, target_end_year_roc + 1):
            quarters_to_crawl = [1, 2, 3, 4]
            
            if year_roc_query == target_end_year_roc:
                quarters_to_crawl = [q for q in quarters_to_crawl if q <= target_end_quarter]
            
            if year_roc_query == target_end_year_roc and not quarters_to_crawl:
                break

            for quarter_query in quarters_to_crawl:
                logger.info(f"正在透過 API 查詢 民國 {year_roc_query} 第 {quarter_query} 季的現金流量數據...")
                
                retries = 1
                for attempt in range(retries):
                    api_result = self.fetch_data_from_api(stock_code, year_roc_query, quarter_query, logger)
                    
                    if api_result:
                        report_list = api_result.get('reportList', [])
                        titles = api_result.get('titles', [])
                        
                        data_for_current_period = {}
                        data_for_prior_period = {}

                        current_year_col_index = -1
                        prior_year_col_index = -1

                        # 根據 titles 找到對應的欄位索引
                        for i, title_info in enumerate(titles):
                            if f"{year_roc_query}年度" in title_info.get('main', '') or f"{year_roc_query}年" in title_info.get('main', ''):
                                current_year_col_index = i
                            elif f"{year_roc_query - 1}年度" in title_info.get('main', '') or f"{year_roc_query - 1}年" in title_info.get('main', ''):
                                prior_year_col_index = i

                        if current_year_col_index == -1:
                            logger.warning(f"無法在 API 回應的表頭中找到當前查詢年份 {year_roc_query} 的數據欄位。")

                        for row in report_list:
                            if len(row) > 0:
                                # 移除會計項目名稱前方的全形或半形空白字元
                                item_name = row[0].lstrip(' 　').strip()
                                if not item_name:
                                    continue

                                # 處理當期數據
                                if current_year_col_index != -1 and len(row) > current_year_col_index:
                                    value_str_current = row[current_year_col_index].strip()
                                    if value_str_current:
                                        try:
                                            # 移除數字中的逗號
                                            value = int(value_str_current.replace(',', ''))
                                            data_for_current_period[item_name] = value
                                        except ValueError:
                                            # 可能是空字串或非數字，跳過
                                            pass
                                
                                # 處理去年同期數據
                                # 這裡的 logic 是：如果 API response 的 titles 中包含 "111年度" (假設 current_year_col_index 是 112 年度)，
                                # 並且 prior_year_col_index 有效，則將其視為去年同期數據
                                if prior_year_col_index != -1 and len(row) > prior_year_col_index and year_roc_query > start_year_roc:
                                    value_str_prior = row[prior_year_col_index].strip()
                                    if value_str_prior:
                                        try:
                                            value = int(value_str_prior.replace(',', ''))
                                            data_for_prior_period[item_name] = value
                                        except ValueError:
                                            pass

                        # 將當期數據保存到 S3
                        if data_for_current_period:
                            self.save_data_to_s3(stock_code, company_name, year_roc_query, quarter_query, data_for_current_period, logger)
                            logger.info(f"成功保存當期數據至 S3：民國 {year_roc_query} 第 {quarter_query} 季。")
                        else:
                            logger.info(f"API 回應中未找到 民國 {year_roc_query} 第 {quarter_query} 季的有效數據，不保存。")

                        # 將去年同期數據保存到 S3
                        # 注意：這裡的 year_roc_query - 1 是指該數據實際所屬的年份
                        if data_for_prior_period and year_roc_query > start_year_roc:
                            self.save_data_to_s3(stock_code, company_name, year_roc_query - 1, quarter_query, data_for_prior_period, logger, is_prior_year_data=True)
                            logger.info(f"成功保存去年同期（來自 民國 {year_roc_query} 第 {quarter_query} 季報表）數據至 S3：民國 {year_roc_query - 1} 第 {quarter_query} 季。")
                        else:
                            logger.info(f"未找到或不適用去年同期數據，不保存 民國 {year_roc_query - 1} 第 {quarter_query} 季的數據。")
                        
                        time.sleep(1) # 每次成功查詢後稍作延遲，避免頻率過高
                        break # 成功獲取並處理數據，跳出重試迴圈
                    else:
                        logger.warning(f"取得 民國 {year_roc_query} 第 {quarter_query} 季數據失敗，進行第 {attempt + 1} 次重試...")
                        time.sleep(3) # 失敗後等待較長時間再重試
                else:
                    logger.error(f"**多次嘗試後仍無法取得 民國 {year_roc_query} 第 {quarter_query} 季數據，跳過此季度。**")

    def save_data_to_s3(self, stock_code, company_name, year_roc, quarter, data, logger, is_prior_year_data=False):
        # 檔案名稱和格式保持不變
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
    crawler = QuarterlyCashFlowAPICrawler()
    
    companies_list_file = 'enriched_missing_stocks_v2.json' # 本地檔案名稱

    try:
        with open(companies_list_file, 'r', encoding='utf-8') as f:
            companies = json.load(f)
        
        root_logger = logging.getLogger()
        root_logger.info(f"從本地檔案 '{companies_list_file}' 載入公司列表，共 {len(companies)} 筆。")

        for stock_code, company_name in companies.items():
            root_logger.info(f"\n--- 開始 API 爬取任務：{stock_code} {company_name} ---")
            crawler.crawl_cash_flow(stock_code, company_name, start_year_roc=105, end_year_roc=114)
            root_logger.info(f"--- 完成 API 爬取任務：{stock_code} {company_name} ---")

    except FileNotFoundError:
        logging.error(f"錯誤: 找不到公司列表檔案 '{companies_list_file}'。請確認檔案是否存在於相同目錄。")
    except json.JSONDecodeError:
        logging.error(f"錯誤: 公司列表檔案 '{companies_list_file}' 格式不正確，無法解析 JSON。", exc_info=True)
    except Exception as e:
        logging.critical(f"API 爬取時發生未預期的嚴重錯誤: {e}", exc_info=True)