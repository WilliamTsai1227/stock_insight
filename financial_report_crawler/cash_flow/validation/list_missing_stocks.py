import json
import os

def list_missing_stock_codes_to_json(
    input_json_file_path='missing_cash_flow_data_v2.json',
    output_json_file_path='missing_stock_codes_v2.json'
):
    """
    讀取 missing_cash_flow_data.json 檔案，並將所有有缺失數據的股票代碼
    另存為一個 JSON 檔案，格式為 {"data": []}。
    """
    if not os.path.exists(input_json_file_path):
        print(f"錯誤：找不到輸入檔案 '{input_json_file_path}'。請確認檔案路徑是否正確。")
        return

    try:
        with open(input_json_file_path, 'r', encoding='utf-8') as f:
            missing_data = json.load(f)
    except json.JSONDecodeError:
        print(f"錯誤：無法解析輸入檔案 '{input_json_file_path}'。請確認其為有效的 JSON 格式。")
        return
    except Exception as e:
        print(f"讀取輸入檔案時發生未知錯誤：{e}")
        return

    # 從輸入 JSON 中提取所有股票代碼
    stock_codes = sorted(list(missing_data.keys())) # 排序以保持一致性

    # 構建 {"data": []} 格式的輸出數據
    output_data = {"data": stock_codes}

    # 將結果保存到 JSON 檔案
    try:
        with open(output_json_file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        print(f"有缺失數據的股票代碼已成功保存到 '{output_json_file_path}'。")
        if not stock_codes:
            print("檔案中沒有缺失數據的股票代碼。")
    except Exception as e:
        print(f"寫入輸出檔案時發生錯誤：{e}")

if __name__ == "__main__":
    list_missing_stock_codes_to_json()