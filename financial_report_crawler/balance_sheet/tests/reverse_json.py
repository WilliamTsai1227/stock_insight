import json

def reverse_json_order(input_filename, output_filename):
    """
    反轉 JSON 檔案中鍵值對的順序。

    Args:
        input_filename (str): 輸入 JSON 檔案的路徑。
        output_filename (str): 輸出 JSON 檔案的路徑。
    """
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 將字典轉換為鍵值對的列表
        items = list(data.items())

        # 反轉列表的順序
        reversed_items = items[::-1]

        # 將反轉後的列表轉換回字典
        reversed_data = dict(reversed_items)

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(reversed_data, f, ensure_ascii=False, indent=4)
        print(f"檔案 '{input_filename}' 已成功反轉並儲存至 '{output_filename}'。")

    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{input_filename}'。")
    except json.JSONDecodeError:
        print(f"錯誤：無法解析檔案 '{input_filename}'。請確認它是有效的 JSON 格式。")
    except Exception as e:
        print(f"發生未知錯誤：{e}")

# 設定輸入和輸出檔案名稱
input_file = 'companies_list_source_v2.json'
output_file = 'companies_list_source_v2_reverse.json'

# 執行反轉操作
reverse_json_order(input_file, output_file)