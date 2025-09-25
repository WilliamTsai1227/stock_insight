# tests/unit/module/test_advanced_search.py

import pytest
from api.advanced_search import AdvancedSearch
from decimal import Decimal

# 測試 validate_ranking_type 方法
def test_validate_ranking_type():
    assert AdvancedSearch.validate_ranking_type("revenue") == True
    assert AdvancedSearch.validate_ranking_type("basic_eps") == True
    assert AdvancedSearch.validate_ranking_type("diluted_eps") == True
    assert AdvancedSearch.validate_ranking_type("short_term_investments") == True
    assert AdvancedSearch.validate_ranking_type("invalid_type") == False

# 測試 validate_year 方法
def test_validate_year():
    assert AdvancedSearch.validate_year(2024) == True
    assert AdvancedSearch.validate_year(1899) == False
    assert AdvancedSearch.validate_year(2026) == False

# 測試validate_quarter 方法
def test_validate_quarter():
    assert AdvancedSearch.validate_quarter(1) == True    
    assert AdvancedSearch.validate_quarter(2) == True    
    assert AdvancedSearch.validate_quarter(3) == True    
    assert AdvancedSearch.validate_quarter(4) == True    
    assert AdvancedSearch.validate_quarter("wjww") == False
    assert AdvancedSearch.validate_quarter(5) == False
    assert AdvancedSearch.validate_quarter(None) == True
        

# 測試 decimal_to_float 方法
def test_decimal_to_float():
    data = [
        {"value": Decimal("123.45"), "name": "test"},
        {"value": 100, "name": "test2"},
    ]
    expected = [
        {"value": 123.45, "name": "test"},
        {"value": 100, "name": "test2"},
    ]
    result = AdvancedSearch.decimal_to_float(data)
    assert result == expected
    assert isinstance(result[0]['value'], float)
    assert isinstance(result[1]['value'], int)

# 測試 _validate_report_type_for_ranking 方法
def test_validate_report_type_for_ranking():
    # 現金流量表只支援 accumulated
    assert AdvancedSearch._validate_report_type_for_ranking('Cash_Flow_Statements', 'accumulated') == True
    assert AdvancedSearch._validate_report_type_for_ranking('Cash_Flow_Statements', 'quarterly') == False
    
    # 資產負債表只支援 quarterly
    assert AdvancedSearch._validate_report_type_for_ranking('Balance_Sheets', 'quarterly') == True
    assert AdvancedSearch._validate_report_type_for_ranking('Balance_Sheets', 'accumulated') == False
    
    # 損益表支援兩種
    assert AdvancedSearch._validate_report_type_for_ranking('Income_Statements', 'quarterly') == True
    assert AdvancedSearch._validate_report_type_for_ranking('Income_Statements', 'accumulated') == True
    assert AdvancedSearch._validate_report_type_for_ranking('Income_Statements', 'invalid') == False