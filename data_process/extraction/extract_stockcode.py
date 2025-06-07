import pandas as pd
import json

def extract_company_codes_to_json(csv_filepath, output_json_filepath):
    """
    從CSV檔案中提取「公司代號」並儲存為指定格式的JSON檔案。
    會嘗試多種繁體中文和常見的編碼來讀取CSV檔案。

    Args:
        csv_filepath (str): 輸入的CSV檔案路徑。
        output_json_filepath (str): 輸出的JSON檔案路徑。
    """
    # 嘗試的編碼列表，優先嘗試您提到的 big5，然後是 cp950，最後是 utf-8 和 utf-8-sig
    encodings_to_try = ['big5', 'cp950', 'utf-8', 'utf-8-sig']
    df = None

    for encoding in encodings_to_try:
        try:
            print(f"嘗試以 '{encoding}' 編碼讀取檔案 '{csv_filepath}'...")
            df = pd.read_csv(csv_filepath, encoding=encoding)
            print(f"成功以 '{encoding}' 編碼讀取檔案。")
            break # 成功讀取後跳出迴圈
        except UnicodeDecodeError:
            print(f"以 '{encoding}' 編碼讀取失敗。")
            continue # 繼續嘗試下一個編碼
        except Exception as e:
            print(f"讀取檔案時發生非解碼錯誤：{e}")
            return # 遇到其他錯誤直接返回

    if df is None:
        print(f"錯誤：無法使用以下任何編碼讀取檔案 '{csv_filepath}'：{encodings_to_try}")
        return

    # 後續處理與之前相同
    try:
        # 檢查「公司代號」欄位是否存在
        if '公司代號' not in df.columns:
            print("錯誤：CSV檔案中找不到 '公司代號' 欄位。")
            print(f"檔案中的欄位有：{df.columns.tolist()}") # 顯示現有欄位供參考
            return

        # 提取「公司代號」欄位的值並轉換為列表
        company_codes = df['公司代號'].tolist()

        # 確保公司代號是整數 (如果CSV中是數字)
        # 排除任何可能因NaN或其他非數字導致的錯誤
        company_codes = [code for code in company_codes if pd.notna(code)]
        try:
            # 嘗試轉換為 int，如果遇到非數字，則可能需要更精確的處理
            company_codes = [int(code) for code in company_codes]
        except ValueError:
            print("警告：部分 '公司代號' 無法轉換為整數，將保留其原始類型。")
            # 如果無法全部轉為 int，就讓它保持原樣，或者你可以決定如何處理非數字代號

        # 構建JSON資料
        json_data = {"data": company_codes}

        # 將資料寫入JSON檔案
        # 輸出JSON時，由於內容可能包含中文，建議使用 'utf-8' 編碼，並設置 ensure_ascii=False
        with open(output_json_filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        print(f"'{output_json_filepath}' 檔案已成功建立。")

    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{csv_filepath}'。請檢查路徑是否正確。")
    except Exception as e:
        print(f"處理資料或寫入JSON時發生錯誤：{e}")

# --- 使用範例 ---
input_csv = 'Taiwan_OTC_Company_20250601.csv'
output_json = 'OTC_company_codes.json'

extract_company_codes_to_json(input_csv, output_json)