import json
import os

def check_json_diff(file_path_v1, file_path_v2):
    """
    檢查兩個 JSON 檔案（字典格式）之間的差異。
    特別指出 v2 比 v1 少了哪些項目，以及 v2 比 v1 多了哪些項目。

    Args:
        file_path_v1 (str): 第一個 JSON 檔案的路徑 (基準檔案)。
        file_path_v2 (str): 第二個 JSON 檔案的路徑 (要比較檢查的檔案)。
    """
    print(f"嘗試讀取檔案：'{file_path_v1}' 和 '{file_path_v2}'")
    try:
        with open(file_path_v1, 'r', encoding='utf-8') as f1:
            data_v1 = json.load(f1)
        with open(file_path_v2, 'r', encoding='utf-8') as f2:
            data_v2 = json.load(f2)
    except FileNotFoundError:
        print("錯誤：找不到指定的 JSON 檔案，請檢查路徑是否正確。")
        print(f"請確保檔案存在於：\n- {os.path.abspath(file_path_v1)}\n- {os.path.abspath(file_path_v2)}")
        return
    except json.JSONDecodeError:
        print("錯誤：JSON 檔案格式不正確，無法解析。")
        print(f"請檢查檔案內容：'{file_path_v1}' 和 '{file_path_v2}'。")
        return

    # 確保資料是字典類型
    if not isinstance(data_v1, dict) or not isinstance(data_v2, dict):
        print("錯誤：JSON 檔案的根元素不是字典格式。")
        print("請確保 JSON 內容以 `{` 開頭和以 `}` 結尾。")
        return

    # 將字典的鍵轉換為集合 (Set)，方便進行集合運算
    keys_v1 = set(data_v1.keys())
    keys_v2 = set(data_v2.keys())

    # 檢查 v2 比 v1 少了哪些項目 (即存在於 v1 但不存在於 v2 的鍵)
    missing_in_v2 = keys_v1 - keys_v2

    # 檢查 v2 比 v1 多了哪些項目 (即存在於 v2 但不存在於 v1 的鍵)
    added_in_v2 = keys_v2 - keys_v1

    print(f"\n--- 比較 '{os.path.basename(file_path_v1)}' 與 '{os.path.basename(file_path_v2)}' 的差異 ---")

    if missing_in_v2:
        print(f"\n'{os.path.basename(file_path_v2)}' 比 '{os.path.basename(file_path_v1)}' 少了以下項目：")
        for key in sorted(list(missing_in_v2)): # 排序輸出，方便查看
            print(f"  - 股票代碼: {key}, 公司名稱: {data_v1.get(key, 'N/A')}")
    else:
        print(f"\n'{os.path.basename(file_path_v2)}' 並沒有比 '{os.path.basename(file_path_v1)}' 缺少任何項目。")

    if added_in_v2:
        print(f"\n'{os.path.basename(file_path_v2)}' 比 '{os.path.basename(file_path_v1)}' 多了以下項目：")
        for key in sorted(list(added_in_v2)): # 排序輸出，方便查看
            print(f"  - 股票代碼: {key}, 公司名稱: {data_v2.get(key, 'N/A')}")
    else:
        print(f"\n'{os.path.basename(file_path_v2)}' 並沒有比 '{os.path.basename(file_path_v1)}' 增加任何項目。")

    print("\n--- 檢查完成 ---")

# --- 如何使用 ---
if __name__ == "__main__":
    # 請將 'your_v1_file.json' 和 'your_v2_file.json' 替換為您的實際檔案路徑
    # 範例 (請替換成您實際的檔案路徑):
    v1_file = 'enriched_missing_stocks_v1.json'
    v2_file = 'enriched_missing_stocks_v2.json'

    # 您需要確保這兩個檔案實際存在於程式碼運行目錄或指定完整路徑
    # 例如，如果檔案在同一目錄下，可以直接寫檔名
    # 如果在子目錄中，例如 data/v1.json，則寫 'data/v1.json'

    check_json_diff(v1_file, v2_file)

    # 也可以測試另一個範例，假設 v2_missing_example.json 真的缺少一些項目
    # check_json_diff('enriched_missing_stocks_v1.json', 'enriched_missing_stocks_v2_missing_example.json')