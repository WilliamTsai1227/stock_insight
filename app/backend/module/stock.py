import re
from fastapi import HTTPException
from typing import Dict, Any
from datetime import datetime, date
from decimal import Decimal

class Stock:
    # 國家代碼對照表
    COUNTRY_CODE_MAP = {
        'tw': 'Taiwan',
        'us': 'USA',
        'hk': 'Hong_Kong',
        'jp': 'Japan',
        'cn': 'China'
    }

    @staticmethod
    def validate_stock_symbol(stock_symbol: str) -> bool:
        """
        驗證股票代碼格式
        只允許英文字母和數字
        """
        if not stock_symbol:
            return False
        return bool(re.match(r'^[A-Za-z0-9]+$', stock_symbol))

    @staticmethod
    def validate_country_code(country_code: str) -> bool:
        """
        驗證國家代碼格式
        只允許英文字母
        """
        if not country_code:
            return False
        return bool(re.match(r'^[a-zA-Z]+$', country_code))

    @staticmethod
    def get_country_name(country_code: str) -> str:
        """
        根據國家代碼獲取國家名稱
        """
        country_code = country_code.lower()
        if country_code not in Stock.COUNTRY_CODE_MAP:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的國家代碼：{country_code}。支援的代碼：{', '.join(Stock.COUNTRY_CODE_MAP.keys())}"
            )
        return Stock.COUNTRY_CODE_MAP[country_code]

    @staticmethod
    def format_stock_data(record_or_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化股票資料
        處理各種資料類型並轉換為字典。
        直接接收 asyncpg.Record 物件（已轉換為字典）或普通的字典。
        """
        # 如果傳入的是 asyncpg.Record 物件，先轉換成字典。
        # 我們已經將其轉換為 dict(result_record) 再傳入，
        # 所以這裡直接假定輸入是字典。
        stock_info = dict(record_or_dict) # 複製一份，避免修改原始輸入

        # 移除不需要的欄位
        fields_to_remove = ['company_id', 'country_id', 'sector_id']
        for field in fields_to_remove:
            stock_info.pop(field, None)

        # 處理日期格式
        date_fields = ['founding_date', 'listed_date', 'otc_listed_date', 'last_updated']
        for field in date_fields:
            if stock_info.get(field):
                if isinstance(stock_info[field], (datetime, date)):
                    stock_info[field] = stock_info[field].isoformat()

        # 處理數字格式
        number_fields = [
            'outstanding_common_shares',
            'private_placement_common_shares',
            'preferred_shares'
        ]
        for field in number_fields:
            if stock_info.get(field) is not None:
                if isinstance(stock_info[field], Decimal):
                    stock_info[field] = int(stock_info[field])
                elif isinstance(stock_info[field], (int, float)):
                    stock_info[field] = int(stock_info[field])

        # 處理布林值
        boolean_fields = ['is_verified']
        for field in boolean_fields:
            if stock_info.get(field) is not None:
                # asyncpg 從資料庫讀取 bool 會是 bool 類型
                stock_info[field] = bool(stock_info[field])
            else:
                stock_info[field] = False  # 如果資料庫中是空值，設為 False

        # 處理空值 (通常 asyncpg 不會返回空字串，而是 None)
        for field, value in stock_info.items():
            if value is None or (isinstance(value, str) and value == ''):
                stock_info[field] = None

        return stock_info

    @staticmethod
    def get_stock_info_query() -> str:
        """
        獲取股票基本資訊查詢 SQL
        使用 asyncpg 兼容的 $N 佔位符
        """
        return """
            SELECT 
                c.*,
                s.sector_name,
                co.country_name
            FROM Companies AS c
            LEFT JOIN Sectors AS s ON c.sector_id = s.sector_id
            LEFT JOIN Countrys AS co ON c.country_id = co.country_id
            WHERE c.stock_symbol = $1 AND co.country_name = $2
        """ 