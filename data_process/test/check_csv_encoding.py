import pandas as pd

def check_csv_decoding(filepath, encoding='cp950'):
    """
    檢查指定 CSV 檔案是否能以給定的編碼正常解碼。

    Args:
        filepath (str): CSV 檔案的路徑。
        encoding (str): 要嘗試解碼的編碼，預設為 'cp950'。

    Returns:
        bool: 如果能正常解碼則回傳 True，否則回傳 False。
    """
    print(f"正在檢查檔案: '{filepath}' 是否能以 '{encoding}' 編碼正常解碼...")
    try:
        # 嘗試讀取檔案，不預設任何 dtype，讓 Pandas 自動判斷
        _ = pd.read_csv(filepath, encoding=encoding)
        print(f"成功！檔案 '{filepath}' 可以用 '{encoding}' 編碼正常解碼。")
        return True
    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 '{filepath}'。請檢查檔案路徑。")
        return False
    except UnicodeDecodeError as e:
        print(f"錯誤: 檔案 '{filepath}' 無法使用 '{encoding}' 編碼解碼。")
        print(f"解碼錯誤詳情: {e}")
        return False
    except Exception as e:
        print(f"讀取檔案時發生未知錯誤: {e}")
        return False

# --- 主執行區塊 ---
if __name__ == "__main__":
    csv_file_to_check = 'Taiwan_OTC_Company_20250601.csv'  # <-- 請修改為你要檢查的 CSV 檔案路徑

    # 執行檢查
    is_decodable = check_csv_decoding(csv_file_to_check)

    if not is_decodable:
        print("\n建議: 如果檔案無法以 CP950 解碼，你可能需要嘗試其他編碼，例如 'utf-8' 或 'big5'。")
        print("以下是嘗試用 'utf-8' 解碼的範例 (僅供參考):")
        check_csv_decoding(csv_file_to_check, encoding='utf-8')
        print("\n以下是嘗試用 'big5' 解碼的範例 (僅供參考):")
        check_csv_decoding(csv_file_to_check, encoding='big5')