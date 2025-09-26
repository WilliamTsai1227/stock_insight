# tests/unit/module/test_advanced_search.py

import pytest
from api.advanced_search import AdvancedSearch
from decimal import Decimal


def test_validate_ranking_type():
    assert AdvancedSearch.validate_ranking_type("revenue") == True
    assert AdvancedSearch.validate_ranking_type("basic_eps") == True
    assert AdvancedSearch.validate_ranking_type("diluted_eps") == True
    assert AdvancedSearch.validate_ranking_type("short_term_investments") == True
    assert AdvancedSearch.validate_ranking_type("invalid_type") == False
    assert AdvancedSearch.validate_ranking_type(123) is False
    assert AdvancedSearch.validate_ranking_type(None) is False
    assert AdvancedSearch.validate_ranking_type(["revenue"]) is False


def test_validate_year():
    assert AdvancedSearch.validate_year(2024) == True
    assert AdvancedSearch.validate_year(1899) == False
    assert AdvancedSearch.validate_year(2026) == False
    assert AdvancedSearch.validate_year("2024") is False
    assert AdvancedSearch.validate_year(None) is False
    assert AdvancedSearch.validate_year(2000.5) is False


def test_validate_quarter():
    assert AdvancedSearch.validate_quarter(1) == True    
    assert AdvancedSearch.validate_quarter(2) == True    
    assert AdvancedSearch.validate_quarter(3) == True    
    assert AdvancedSearch.validate_quarter(4) == True    
    assert AdvancedSearch.validate_quarter("wjww") == False
    assert AdvancedSearch.validate_quarter(5) == False
    assert AdvancedSearch.validate_quarter(None) == True
    assert AdvancedSearch.validate_quarter(0) is False
    assert AdvancedSearch.validate_quarter(-1) is False
        


def test_decimal_to_float():
    # 1. 單一 Decimal
    assert AdvancedSearch.decimal_to_float(Decimal("1.23")) == 1.23
    assert isinstance(AdvancedSearch.decimal_to_float(Decimal("1.23")), float)

    # 2. 字典包含 Decimal
    data_dict = {"price": Decimal("99.99"), "name": "apple"}
    expected_dict = {"price": 99.99, "name": "apple"}
    result_dict = AdvancedSearch.decimal_to_float(data_dict)
    assert result_dict == expected_dict
    assert isinstance(result_dict["price"], float)

    # 3. List 包含 Decimal
    data_list = [Decimal("5.5"), Decimal("10.1"), "banana"]
    expected_list = [5.5, 10.1, "banana"]
    result_list = AdvancedSearch.decimal_to_float(data_list)
    assert result_list == expected_list
    assert isinstance(result_list[0], float)
    assert isinstance(result_list[1], float)

    # 4. 巢狀結構 (dict + list + Decimal)
    data_nested = {
        "a": [Decimal("1.1"), {"b": Decimal("2.2")}],
        "c": {"d": [Decimal("3.3"), "pear"]},
    }
    expected_nested = {
        "a": [1.1, {"b": 2.2}],
        "c": {"d": [3.3, "pear"]},
    }
    result_nested = AdvancedSearch.decimal_to_float(data_nested)
    assert result_nested == expected_nested
    assert isinstance(result_nested["a"][0], float)
    assert isinstance(result_nested["a"][1]["b"], float)
    assert isinstance(result_nested["c"]["d"][0], float)

    # 5. 不應該被轉換的值
    assert AdvancedSearch.decimal_to_float("hello") == "hello"
    assert AdvancedSearch.decimal_to_float(123) == 123
    assert AdvancedSearch.decimal_to_float(None) is None
    assert AdvancedSearch.decimal_to_float(True) is True

    # 6. 空值
    assert AdvancedSearch.decimal_to_float([]) == []
    assert AdvancedSearch.decimal_to_float({}) == {}

    # 7.測試大數字 Decimal
    big_num = Decimal("12345678901234567890.123456789")
    result = AdvancedSearch.decimal_to_float(big_num)
    assert isinstance(result, float)
    # 檢查數值在合理範圍內（允許小數精度誤差）
    assert abs(result - float(big_num)) < 1e-6




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

    assert AdvancedSearch._validate_report_type_for_ranking("Unknown_Report", "quarterly") is False
    assert AdvancedSearch._validate_report_type_for_ranking("", "accumulated") is False
    assert AdvancedSearch._validate_report_type_for_ranking(None, "quarterly") is False



def test_convert_report_period():
    assert AdvancedSearch.convert_report_period("annual") == "accumulated"
    assert AdvancedSearch.convert_report_period("quarterly") == "quarterly"



def test_get_default_quarter():
    assert AdvancedSearch.get_default_quarter("accumulated") == 4
    assert AdvancedSearch.get_default_quarter("quarterly") is None



def test_validate_sector_name():
    assert AdvancedSearch.validate_sector_name("半導體") is True
    assert AdvancedSearch.validate_sector_name("Tech 123") is True
    assert AdvancedSearch.validate_sector_name("abc$%^") is False
    assert AdvancedSearch.validate_sector_name("") is False



def test_validate_limit():
    assert AdvancedSearch.validate_limit(1) is True
    assert AdvancedSearch.validate_limit(500) is True
    assert AdvancedSearch.validate_limit(1000) is True
    assert AdvancedSearch.validate_limit(0) is False
    assert AdvancedSearch.validate_limit(1001) is False