"""
測試 /api/advanced_search/stock_ranking API
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_stock_ranking_basic():
    """測試基本的股票排名查詢"""
    response = client.get("/api/advanced_search/stock_ranking", params={
        "stock_symbol": "2330",
        "year": 2023,
        "report_type": "annual",
        "statement_type": "cash_flow"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "data" in data
    
    # 驗證回傳資料結構
    stock_data = data["data"]
    assert "stock_info" in stock_data
    assert "query_params" in stock_data
    assert "rankings" in stock_data
    assert "summary" in stock_data
    
    # 驗證股票資訊
    stock_info = stock_data["stock_info"]
    assert stock_info["stock_symbol"] == "2330"
    assert "country" in stock_info
    assert "sector" in stock_info
    
    # 驗證查詢參數
    query_params = stock_data["query_params"]
    assert query_params["year"] == 2023
    assert query_params["report_type"] == "annual"
    assert query_params["quarter"] == 4  # annual 應該自動設定為第4季

def test_stock_ranking_quarterly():
    """測試季度查詢"""
    response = client.get("/api/advanced_search/stock_ranking", params={
        "stock_symbol": "2330",
        "year": 2023,
        "report_type": "quarterly",
        "quarter": 1,
        "statement_type": "income_statement"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    
    query_params = data["data"]["query_params"]
    assert query_params["report_type"] == "quarterly"
    assert query_params["quarter"] == 1

def test_stock_ranking_invalid_stock():
    """測試無效的股票代碼"""
    response = client.get("/api/advanced_search/stock_ranking", params={
        "stock_symbol": "INVALID",
        "year": 2023,
        "report_type": "annual",
        "statement_type": "cash_flow"
    })
    
    assert response.status_code == 404
    assert "未找到股票代碼" in response.json()["detail"]

def test_stock_ranking_invalid_year():
    """測試無效的年份"""
    response = client.get("/api/advanced_search/stock_ranking", params={
        "stock_symbol": "2330",
        "year": 1800,  # 無效年份
        "report_type": "annual",
        "statement_type": "cash_flow"
    })
    
    assert response.status_code == 400
    assert "年份格式不正確" in response.json()["detail"]

def test_stock_ranking_invalid_report_type():
    """測試無效的財報期間"""
    response = client.get("/api/advanced_search/stock_ranking", params={
        "stock_symbol": "2330",
        "year": 2023,
        "report_type": "invalid",
        "statement_type": "cash_flow"
    })
    
    assert response.status_code == 400
    assert "不支援的財報期間" in response.json()["detail"]

def test_stock_ranking_missing_quarter():
    """測試季度模式缺少季度參數"""
    response = client.get("/api/advanced_search/stock_ranking", params={
        "stock_symbol": "2330",
        "year": 2023,
        "report_type": "quarterly",
        "statement_type": "income_statement"
        # 缺少 quarter 參數
    })
    
    assert response.status_code == 400
    assert "必須指定季度" in response.json()["detail"]

def test_stock_ranking_invalid_quarter():
    """測試無效的季度"""
    response = client.get("/api/advanced_search/stock_ranking", params={
        "stock_symbol": "2330",
        "year": 2023,
        "report_type": "quarterly",
        "quarter": 5,  # 無效季度
        "statement_type": "income_statement"
    })
    
    assert response.status_code == 400
    assert "季度格式不正確" in response.json()["detail"]

def test_stock_ranking_rankings_structure():
    """測試排行榜資料結構"""
    response = client.get("/api/advanced_search/stock_ranking", params={
        "stock_symbol": "2330",
        "year": 2023,
        "report_type": "annual",
        "statement_type": "cash_flow"
    })
    
    assert response.status_code == 200
    data = response.json()["data"]
    rankings = data["rankings"]
    
    # 驗證至少有一些排行榜資料
    assert len(rankings) > 0
    
    # 驗證每個排行榜的結構
    for ranking_key, ranking_data in rankings.items():
        assert "description" in ranking_data
        assert "table" in ranking_data
        assert "field" in ranking_data
        
        # 如果有排名資料
        if ranking_data.get("rank") is not None:
            assert "value" in ranking_data
            assert "rank" in ranking_data
            assert "total_count" in ranking_data
            assert isinstance(ranking_data["rank"], int)
            assert isinstance(ranking_data["total_count"], int)
        else:
            # 如果沒有排名資料
            assert "note" in ranking_data
            assert ranking_data["note"] == "該指標在此期間無資料"

def test_stock_ranking_summary():
    """測試摘要資訊"""
    response = client.get("/api/advanced_search/stock_ranking", params={
        "stock_symbol": "2330",
        "year": 2023,
        "report_type": "annual",
        "statement_type": "cash_flow"
    })
    
    assert response.status_code == 200
    data = response.json()["data"]
    summary = data["summary"]
    
    assert "total_metrics" in summary
    assert "metrics_with_rank" in summary
    assert "metrics_without_data" in summary
    
    assert isinstance(summary["total_metrics"], int)
    assert isinstance(summary["metrics_with_rank"], int)
    assert isinstance(summary["metrics_without_data"], int)
    
    # 驗證總數邏輯
    assert summary["total_metrics"] == summary["metrics_with_rank"] + summary["metrics_without_data"]

if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v"]) 