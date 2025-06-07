import pandas as pd
import json

"""從多個 CSV 檔案中，彙整並提取所有不重複的「產業類別」，然後將這些獨特的產業類別儲存成一個 JSON 檔案。"""

def extract_unique_industries_from_multiple_csv(csv_filepaths, output_json_filepath):
    """
    從多個CSV檔案中提取所有不重複的「產業類別」並儲存為指定格式的JSON檔案。

    Args:
        csv_filepaths (list): 包含所有輸入CSV檔案路徑的列表。
        output_json_filepath (str): 輸出的JSON檔案路徑。
    """
    all_industries = set() # 使用 set 來自動處理重複項
    encodings_to_try = ['cp950', 'big5', 'utf-8', 'utf-8-sig'] # 優先 cp950

    for csv_filepath in csv_filepaths:
        df = None
        print(f"\n--- 處理檔案: '{csv_filepath}' ---")
        for encoding in encodings_to_try:
            try:
                print(f"嘗試以 '{encoding}' 編碼讀取檔案 '{csv_filepath}'...")
                df = pd.read_csv(csv_filepath, encoding=encoding)
                print(f"成功以 '{encoding}' 編碼讀取檔案。")
                break # 成功讀取後跳出迴圈
            except UnicodeDecodeError:
                print(f"以 '{encoding}' 編碼讀取失敗。")
                continue # 繼續嘗試下一個編碼
            except FileNotFoundError:
                print(f"錯誤：找不到檔案 '{csv_filepath}'。請檢查路徑是否正確。")
                df = None # 確保 df 保持為 None 以便後續檢查
                break # 檔案不存在，停止嘗試其他編碼
            except Exception as e:
                print(f"讀取檔案時發生非解碼錯誤：{e}")
                df = None
                break

        if df is None:
            print(f"跳過檔案 '{csv_filepath}'，因為無法成功讀取。")
            continue # 無法讀取當前檔案，跳到下一個

        # 檢查「產業類別」欄位是否存在
        if '產業類別' not in df.columns:
            print(f"錯誤：檔案 '{csv_filepath}' 中找不到 '產業類別' 欄位。")
            print(f"該檔案中的欄位有：{df.columns.tolist()}")
            continue # 跳到下一個檔案

        # 提取「產業類別」並加入到 set 中
        # 使用 .dropna() 排除 NaN 值，.astype(str) 確保都是字串類型
        industries_in_file = df['產業類別'].dropna().astype(str).tolist()
        all_industries.update(industries_in_file) # 使用 update 將列表中的元素添加到 set

    # 將 set 轉換為列表，因為 set 是無序的，可以排序以獲得一致的輸出
    unique_industries_list = sorted(list(all_industries))

    # 構建JSON資料
    json_data = {"data": unique_industries_list}

    # 將資料寫入JSON檔案
    with open(output_json_filepath, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

    print(f"\n'{output_json_filepath}' 檔案已成功建立，共提取到 {len(unique_industries_list)} 種不重複的產業類別。")

# --- 使用範例 ---
# 請將這裡替換為你的實際CSV檔案名稱和路徑
input_csv_files = [
    'Taiwan_listed_companies_20250601.csv',
    'Taiwan_OTC_companies_20250601.csv' # 假設你有另一個檔案，例如上櫃公司資料
    # 如果有更多檔案，可以在這裡繼續添加
]
output_json = 'industry_category_statistics.json'

extract_unique_industries_from_multiple_csv(input_csv_files, output_json)