import os
import json
import time
import logging
import boto3
import requests
from datetime import datetime

# --- 配置區塊：透過環境變數從 ECS 任務定義中注入 ---
# 不再從 .env 檔案載入，這些變數將由 ECS 環境提供
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
S3_BUCKET_NAME = os.environ.get('Financial_Report_S3_BUCKET_NAME')
S3_RAW_DATA_PREFIX = os.environ.get('Financial_Report_S3_RAW_DATA_PREFIX', 'raw-data/cash_flow/')
SQS_QUEUE_URL = os.environ.get('SQS_CASH_FLOW_QUEUE_URL') # SQS 佇列 URL

# AWS S3 ACCESS KEY ID 和 SECRET ACCESS KEY 不應直接在程式碼中硬編碼或從環境變數讀取
# 而是應該使用 IAM Role for Tasks 來授予 ECS Task S3 的存取權限
# 因此這些變數將被移除，並依賴 boto3 的預設憑證鏈。

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
            "Referer": "https://mops.twse.com.tw/mops/#/web/t164sb05",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\""
        }
        
        # S3 客戶端：依賴 ECS Task Role 提供的憑證
        self.s3_client = boto3.client('s3', region_name=AWS_REGION)
        # SQS 客戶端：依賴 ECS Task Role 提供的憑證
        self.sqs_client = boto3.client('sqs', region_name=AWS_REGION)

        self._setup_root_logger()
        
    def _setup_root_logger(self):
        """設定根日誌記錄器，輸出到標準輸出/CloudWatch"""
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
        logger_name = f"{stock_code}_{company_name}_cash_flow_api_crawler"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        # 確保不會為每個股票重複添加 StreamHandler
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
                logger.warning(f"API 回應非成功狀態碼或無結果：{json_response.get('code')} - {json_response.get('message')}. Full response: {json_response}")
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
                
                retries = 2
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
                            main_title = title_info.get('main', '')
                            # 判斷當前年度
                            if f"{year_roc_query}年度" in main_title or f"{year_roc_query}年" in main_title:
                                current_year_col_index = i
                            # 判斷去年同期
                            elif f"{year_roc_query - 1}年度" in main_title or f"{year_roc_query - 1}年" in main_title:
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
        # S3 Key 格式：financial-report/raw-data/cash_flow/股票代碼_年份Q季度_cash_flow.json
        s3_object_key = f"{S3_RAW_DATA_PREFIX}{stock_code}_{year_roc}Q{quarter}_cash_flow.json"
        
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
    crawler = QuarterlyCashFlowAPICrawler()
    
    # 設置 SQS 接收訊息的參數
    max_messages = 1
    # VisibilityTimeout 應根據實際任務處理時間設定，確保在處理期間訊息不會被其他消費者看到
    # 如果任務處理時間可能超過 5 分鐘，請將此值設高
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
                time.sleep(wait_time_seconds)
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
                        root_logger.warning(f"SQS 訊息格式不正確，缺少 stock_code 或 company_name: {message['Body']}. 將刪除此訊息以避免重複處理。")
                        # 對於格式不正確的訊息，直接刪除，避免無限循環
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
                    root_logger.error(f"處理 SQS 訊息或執行爬蟲時發生錯誤: {e}. 訊息將在 VisibilityTimeout 後重新可見。", exc_info=True)
                    # 如果這裡發生錯誤，訊息將在 VisibilityTimeout 後重新可見，並被重新處理
                    # 如果是持續性錯誤，訊息將會進入死信佇列 (可再配置)
                    # 不在此處刪除訊息，讓 SQS 處理重試邏輯
        
        except Exception as e:
            root_logger.critical(f"與 SQS 服務互動時發生嚴重錯誤: {e}", exc_info=True)
            root_logger.info("程式將在短暫等待後重試 SQS 連接...")
            time.sleep(10) # 發生 SQS 相關錯誤時等待較長時間再重試