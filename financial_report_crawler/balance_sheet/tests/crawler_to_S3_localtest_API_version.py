import os
import json
import time
import logging
import boto3
import requests
from datetime import datetime
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

# --- 配置區塊：建議透過環境變數或專門的配置檔案管理這些值 ---
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
S3_BUCKET_NAME = os.environ.get('Financial_Report_S3_BUCKET_NAME')
S3_RAW_DATA_PREFIX = os.environ.get('Financial_Report_S3_BALANCE_SHEET_RAW_DATA_PREFIX', 'raw-data/balance_sheet/')

AWS_S3_ACCESS_KEY_ID = os.getenv('aws_s3_access_key_id')
AWS_S3_SECRET_ACCESS_KEY = os.getenv('aws_s3_secret_access_key')
# --------------------------------------------------------

class BalanceSheetAPICrawler:
    def __init__(self):
        self.api_url = "https://mops.twse.com.tw/mops/api/t164sb03"
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
            "Referer": "https://mops.twse.com.tw/mops/#/web/t164sb03",
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
        logger_name = f"{stock_code}_{company_name}_balance_sheet_api_crawler"
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
            "dataType": "2", 
            "season": str(quarter),
            "year": str(year_roc),
            "subsidiaryCompanyId": ""
        }
        logger.info(f"發送請求 payload: {payload}")

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=15)
            response.raise_for_status()
            
            json_response = response.json()
            
            if json_response.get('code') == 200 and json_response.get('result'):
                return json_response['result']
            elif json_response.get('message') == "查詢無資料":
                logger.info(f"API 查詢 民國 {year_roc} 第 {quarter} 季：查無資料。")
                return None
            else:
                logger.warning(f"API 回應非成功狀態碼或無結果：{json_response.get('code')} - {json_response.get('message')}，原始回應：{response.text}")
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

    def crawl_balance_sheet(self, stock_code, company_name, start_year_roc, start_quarter_roc, end_year_roc, end_quarter_for_end_year):
        logger = self._get_logger(stock_code, company_name)

        for year_to_query in range(start_year_roc, end_year_roc + 1):
            quarters_to_crawl = [1, 2, 3, 4]
            
            # 處理起始年份的季度
            if year_to_query == start_year_roc:
                quarters_to_crawl = [q for q in quarters_to_crawl if q >= start_quarter_roc]
            
            # 處理結束年份的季度
            if year_to_query == end_year_roc:
                quarters_to_crawl = [q for q in quarters_to_crawl if q <= end_quarter_for_end_year]
            
            # 如果某個年份經過篩選後沒有季度可爬，則跳過
            if not quarters_to_crawl:
                logger.info(f"民國 {year_to_query} 年沒有符合條件的季度可爬取，跳過此年份。")
                continue

            for quarter_to_query in quarters_to_crawl:
                logger.info(f"正在透過 API 查詢 民國 {year_to_query} 第 {quarter_to_query} 季的資產負債表數據...")
                
                retries = 2
                for attempt in range(retries):
                    api_result = self.fetch_data_from_api(stock_code, year_to_query, quarter_to_query, logger)
                    
                    if api_result:
                        report_list = api_result.get('reportList', [])
                        titles = api_result.get('titles', [])
                        
                        time_period_columns = []
                        
                        for i in range(1, len(titles)):
                            title_info = titles[i]
                            main_title = title_info.get('main', '')
                            sub_titles = title_info.get('sub', [])

                            try:
                                year_str = main_title.split('年')[0]
                                year_roc_from_title = int(year_str)

                                month_day_str = main_title.split('年')[1].split('日')[0]
                                month = int(month_day_str.split('月')[0])
                                quarter_from_title = (month - 1) // 3 + 1
                                
                                amount_col_offset = (i - 1) * 2 + 1
                                percent_col_offset = (i - 1) * 2 + 2
                                
                                if len(sub_titles) == 2 and sub_titles[0].get('main') == '金額' and sub_titles[1].get('main') == '%':
                                    time_period_columns.append({
                                        "year_roc": year_roc_from_title,
                                        "quarter": quarter_from_title,
                                        "amount_idx": amount_col_offset,
                                        "percent_idx": percent_col_offset
                                    })
                                else:
                                    logger.warning(f"標題 '{main_title}' 的子標題格式不符預期，跳過。")

                            except (ValueError, IndexError):
                                logger.warning(f"無法解析標題年份或月份: {main_title}，跳過此標題。")
                                continue
                        
                        if not time_period_columns:
                            logger.warning(f"無法在 API 回應的表頭中找到有效的時間週期數據欄位，可能沒有數據。")
                            break

                        for period_info in time_period_columns:
                            current_year = period_info['year_roc']
                            current_quarter = period_info['quarter']
                            amount_idx = period_info['amount_idx']
                            percent_idx = period_info['percent_idx']

                            data_for_period = {}
                            for row in report_list:
                                if len(row) > 0:
                                    item_name = row[0].lstrip(' 　').strip()
                                    if not item_name:
                                        continue

                                    if len(row) > percent_idx:
                                        value = None
                                        percent = None
                                        
                                        value_str = row[amount_idx].strip()
                                        if value_str:
                                            try:
                                                value = int(value_str.replace(',', ''))
                                            except ValueError:
                                                pass

                                        percent_str = row[percent_idx].strip()
                                        if percent_str:
                                            try:
                                                percent = float(percent_str)
                                            except ValueError:
                                                pass
                                        
                                        if value is not None or percent is not None:
                                            data_for_period[item_name] = [value, percent]
                                    else:
                                        if item_name and item_name not in data_for_period:
                                            data_for_period[item_name] = [None, None]

                            if data_for_period:
                                self.save_data_to_s3(stock_code, company_name, current_year, current_quarter, data_for_period, logger)
                                logger.info(f"成功保存 民國 {current_year} 第 {current_quarter} 季數據至 S3。")
                            else:
                                logger.info(f"API 回應中未找到 民國 {current_year} 第 {current_quarter} 季的有效數據，不保存。")
                        
                        time.sleep(1)
                        break
                    else:
                        logger.warning(f"取得 民國 {year_to_query} 第 {quarter_to_query} 季數據失敗，進行第 {attempt + 1} 次重試...")
                        time.sleep(3)
                else:
                    logger.error(f"**多次嘗試後仍無法取得 民國 {year_to_query} 第 {quarter_to_query} 季數據，跳過此季度。**")

    def save_data_to_s3(self, stock_code, company_name, year_roc, quarter, data, logger):
        s3_object_key = f"{S3_RAW_DATA_PREFIX}{stock_code}_{year_roc}Q{quarter}_balance_sheet.json"
        
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
    crawler = BalanceSheetAPICrawler()
    
    companies_list_file = 'companies_list_source_v2.json'

    # **** 在這裡設定您要爬取的年份和季度範圍 ****
    start_year = 105    # 起始民國年份
    start_quarter = 1   # 起始季度 (1, 2, 3, 4)
    end_year = 114      # 結束民國年份
    end_quarter = 1     # 結束年份要爬取的最終季度 (例如：如果 end_year=114, end_quarter=1, 則只爬 114 年第一季)
    # *************************************************

    try:
        with open(companies_list_file, 'r', encoding='utf-8') as f:
            companies = json.load(f)
        
        root_logger = logging.getLogger()
        root_logger.info(f"從本地檔案 '{companies_list_file}' 載入公司列表，共 {len(companies)} 筆。")
        root_logger.info(f"設定爬取範圍：從 民國 {start_year} 年第 {start_quarter} 季到 民國 {end_year} 年第 {end_quarter} 季。")

        for stock_code, company_name in companies.items():
            root_logger.info(f"\n--- 開始 API 爬取任務：{stock_code} {company_name} ---")
            crawler.crawl_balance_sheet(stock_code, company_name, start_year, start_quarter, end_year, end_quarter)
            root_logger.info(f"--- 完成 API 爬取任務：{stock_code} {company_name} ---")

    except FileNotFoundError:
        logging.error(f"錯誤: 找不到公司列表檔案 '{companies_list_file}'。請確認檔案是否存在於相同目錄。")
    except json.JSONDecodeError:
        logging.error(f"錯誤: 公司列表檔案 '{companies_list_file}' 格式不正確，無法解析 JSON。", exc_info=True)
    except Exception as e:
        logging.critical(f"API 爬取時發生未預期的嚴重錯誤: {e}", exc_info=True)