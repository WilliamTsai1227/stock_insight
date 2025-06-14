import requests
import json

def fetch_cash_flow_data(stock_code, year_roc, quarter):
    url = "https://mops.twse.com.tw/mops/api/t164sb05"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd", # 建議保留
        "Accept-Language": "zh-TW,zh;q=0.9",
        "Origin": "https://mops.twse.com.tw", # 建議保留
        "Referer": "https://mops.twse.com.tw/mops/web/t164sb05", # 建議保留，填寫查詢頁面
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
    }

    payload = {
        "companyId": stock_code,
        "dataType": "2", # 假設 2 是您需要的合併報表
        "season": str(quarter), # 確保是字串
        "year": str(year_roc),  # 確保是字串
        "subsidiaryCompanyId": ""
    }

    try:
        # 發送 POST 請求，json=payload 會自動設定 Content-Type: application/json
        # 並且將 payload 字典序列化為 JSON 字串
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status() # 對於 4XX/5XX 的錯誤回應，引發 HTTPError 異常

        data = response.json()

        if data.get("code") == 200 and data.get("result"):
            print(f"成功取得 {stock_code} 民國 {year_roc} 年 Q{quarter} 的數據。")
            return data["result"]
        else:
            print(f"查詢 {stock_code} 民國 {year_roc} 年 Q{quarter} 失敗: {data.get('message', '未知錯誤')}")
            return None

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP 錯誤: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"連線錯誤: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"超時錯誤: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"請求時發生錯誤: {err}")
    except json.JSONDecodeError:
        print(f"無法解析回應為 JSON: {response.text}")
    return None

# 範例使用
if __name__ == "__main__":
    stock_code = "2630"
    year = 112
    quarter = 1
    cash_flow_data = fetch_cash_flow_data(stock_code, year, quarter)

    if cash_flow_data:
        # 您可以進一步處理 cash_flow_data['reportList'] 來提取具體數值
        # 例如，印出前幾行報告數據
        print("\n部分報告數據：")
        for i, row in enumerate(cash_flow_data.get('reportList', [])[:10]):
            print(row)
        print(f"報表類型：{cash_flow_data.get('reportType')}")
        print(f"公司簡稱：{cash_flow_data.get('companyAbbreviation')}")