"""
pytest 測試 /api/advanced_search/ranking API
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_ranking_revenue_annual():
    """測試年度營收排行榜查詢"""
    response = client.get("/api/advanced_search/ranking", params={
        "ranking_type": "revenue",
        "year": 2023,
        "report_type": "annual",
        "page": 1
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "data" in data
    assert "metadata" in data
    assert data["metadata"]["ranking_type"] == "revenue"
    assert data["metadata"]["report_type"] == "annual"
    assert data["metadata"]["page"] == 1
    assert data["metadata"]["page_size"] == 30
    assert isinstance(data["data"], list)
    assert len(data["data"]) <= 30

def test_ranking_operating_income_quarterly():
    """測試季度營業利益排行榜查詢"""
    response = client.get("/api/advanced_search/ranking", params={
        "ranking_type": "operating_income",
        "year": 2023,
        "report_type": "quarterly",
        "quarter": 2,
        "page": 1
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["metadata"]["ranking_type"] == "operating_income"
    assert data["metadata"]["report_type"] == "quarterly"
    assert data["metadata"]["quarter"] == 2
    assert data["metadata"]["page"] == 1
    assert isinstance(data["data"], list)

def test_ranking_sector_filter():
    """測試產業篩選查詢"""
    response = client.get("/api/advanced_search/ranking", params={
        "ranking_type": "revenue",
        "year": 2023,
        "report_type": "annual",
        "sector_name": "半導體業",
        "page": 1
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["metadata"]["sector_name"] == "半導體業"
    for row in data["data"]:
        assert row["sector_name"] == "半導體業"

def test_ranking_invalid_ranking_type():
    """測試無效的排行榜類型"""
    response = client.get("/api/advanced_search/ranking", params={
        "ranking_type": "invalid_type",
        "year": 2023,
        "report_type": "annual",
        "page": 1
    })
    assert response.status_code == 400

def test_ranking_invalid_year():
    """測試無效年份"""
    response = client.get("/api/advanced_search/ranking", params={
        "ranking_type": "revenue",
        "year": 1800,
        "report_type": "annual",
        "page": 1
    })
    assert response.status_code == 400

def test_ranking_invalid_report_type():
    """測試無效財報期間"""
    response = client.get("/api/advanced_search/ranking", params={
        "ranking_type": "revenue",
        "year": 2023,
        "report_type": "invalid",
        "page": 1
    })
    assert response.status_code == 400

def test_ranking_missing_quarter():
    """測試季度查詢缺少季度參數"""
    response = client.get("/api/advanced_search/ranking", params={
        "ranking_type": "revenue",
        "year": 2023,
        "report_type": "quarterly",
        "page": 1
    })
    assert response.status_code == 400

def test_ranking_invalid_quarter():
    """測試無效季度"""
    response = client.get("/api/advanced_search/ranking", params={
        "ranking_type": "revenue",
        "year": 2023,
        "report_type": "quarterly",
        "quarter": 5,
        "page": 1
    })
    assert response.status_code == 400

def test_ranking_pagination():
    """測試分頁功能"""
    response1 = client.get("/api/advanced_search/ranking", params={
        "ranking_type": "revenue",
        "year": 2023,
        "report_type": "annual",
        "page": 1
    })
    response2 = client.get("/api/advanced_search/ranking", params={
        "ranking_type": "revenue",
        "year": 2023,
        "report_type": "annual",
        "page": 2
    })
    assert response1.status_code == 200
    assert response2.status_code == 200
    data1 = response1.json()["data"]
    data2 = response2.json()["data"]
    # 若有超過30筆，兩頁資料不應重複
    if len(data1) == 30 and len(data2) > 0:
        assert data1 != data2

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 