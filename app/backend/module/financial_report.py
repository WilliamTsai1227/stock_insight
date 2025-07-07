import re
from fastapi import HTTPException
from typing import Dict, Any
from datetime import datetime, date
from decimal import Decimal

class Financial_report:
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
        if country_code not in Financial_report.COUNTRY_CODE_MAP:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的國家代碼：{country_code}。支援的代碼：{', '.join(Financial_report.COUNTRY_CODE_MAP.keys())}"
            )
        return Financial_report.COUNTRY_CODE_MAP[country_code]
    
    @staticmethod
    def validate_report_type(report_type: str) -> bool:
        """
        驗證財報種類是否為 'balance_sheets', 'income_statements', 'cash_flow' 之一
        """
        table_name = report_type.lower()
        if report_type == "balance_sheets":
            table_name = "Balance_Sheets"
        elif report_type == "income_statements":
            table_name = "Income_Statements"
        elif report_type == "cash_flow": # 這裡假設您資料庫的表名是 Cash_Flow_Statements
            table_name = "Cash_Flow_Statements"
        allowed_tables = ["Balance_Sheets", "Income_Statements", "Cash_Flow_Statements"]
        if table_name not in allowed_tables:
            return False
        return True
    
    @staticmethod
    def validate_report_period(report_period: str) -> bool:
        """
        驗證財報期間是否為 'quarterly' 或 'accumulated' 之一
        """
        valid_report_periods = ['quarterly', 'accumulated']
        if report_period not in valid_report_periods:
            return False
        return True
    @staticmethod
    def decimal_to_float(obj):
        if isinstance(obj, dict):
            return {k: Financial_report.decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [Financial_report.decimal_to_float(i) for i in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj