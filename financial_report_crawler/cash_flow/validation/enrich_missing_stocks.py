import json
import os

def enrich_missing_stock_info(
    missing_codes_file_path='missing_stock_codes.json',
    companies_list_file_path='companies_list_source.json',
    output_enriched_file_path='enriched_missing_stocks.json'
):
    """
    讀取包含缺失股票代碼的 JSON 檔案，並從公司列表檔案中尋找對應的公司名稱，
    然後將結果儲存到一個新的 JSON 檔案中。
    輸出格式為字典 {"股票代碼": "公司名稱"}。
    """
    
    # 1. 載入缺失股票代碼檔案
    if not os.path.exists(missing_codes_file_path):
        print(f"錯誤：找不到輸入檔案 '{missing_codes_file_path}'。請確認檔案路徑是否正確。")
        return
    
    try:
        with open(missing_codes_file_path, 'r', encoding='utf-8') as f:
            missing_codes_data = json.load(f)
            missing_stock_codes = missing_codes_data.get('data', [])
    except json.JSONDecodeError:
        print(f"錯誤：無法解析輸入檔案 '{missing_codes_file_path}'。請確認其為有效的 JSON 格式。")
        return
    except Exception as e:
        print(f"讀取輸入檔案 '{missing_codes_file_path}' 時發生未知錯誤：{e}")
        return

    if not missing_stock_codes:
        print(f"'{missing_codes_file_path}' 中沒有任何缺失的股票代碼。")
        # 即使沒有缺失，也創建一個空的輸出檔案
        with open(output_enriched_file_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4) # 輸出為空字典
        return

    # 2. 載入公司列表檔案
    if not os.path.exists(companies_list_file_path):
        print(f"錯誤：找不到公司列表檔案 '{companies_list_file_path}'。請確認檔案路徑是否正確。")
        return

    try:
        with open(companies_list_file_path, 'r', encoding='utf-8') as f:
            companies_list = json.load(f)
    except json.JSONDecodeError:
        print(f"錯誤：無法解析公司列表檔案 '{companies_list_file_path}'。請確認其為有效的 JSON 格式。")
        return
    except Exception as e:
        print(f"讀取公司列表檔案 '{companies_list_file_path}' 時發生未知錯誤：{e}")
        return

    # 3. 比對並生成包含公司名稱的字典
    # 使用字典推導式 (dictionary comprehension) 創建新字典
    enriched_missing_stocks_dict = {
        code: companies_list.get(code, "未知公司名稱") # 如果找不到名稱，給定預設值
        for code in sorted(missing_stock_codes) # 排序股票代碼以確保輸出順序
    }
    
    # 4. 儲存結果到新的 JSON 檔案
    try:
        with open(output_enriched_file_path, 'w', encoding='utf-8') as f:
            json.dump(enriched_missing_stocks_dict, f, ensure_ascii=False, indent=4)
        print(f"已成功將缺失股票的代碼與名稱儲存到 '{output_enriched_file_path}'。")
    except Exception as e:
        print(f"寫入輸出檔案時發生錯誤：{e}")

if __name__ == "__main__":
    enrich_missing_stock_info()