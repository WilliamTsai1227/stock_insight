import pytest
from httpx import AsyncClient
from main import app


BASE_URL = "https://stockinsight-ai.com/"


# ========== 正確情境測試 ==========
@pytest.mark.asyncio
async def test_ranking_valid_request(mocker):
    # 模擬 DB 回傳資料
    mock_data = [
        {
            "stock_symbol": "2330",
            "company_name": "台積電",
            "sector_name": "半導體",
            "country_name": "台灣",
            "revenue": 1000000,
            "year": 2024,
            "quarter": 4,
            "report_type": "accumulated",
            "rank": 1,
        }
    ]

    # mock postgresql_pool.get_connection().fetch
    async def mock_fetch(query, *params):
        return mock_data

    mock_conn = mocker.AsyncMock()
    mock_conn.fetch.side_effect = mock_fetch
    mocker.patch(
        "module.postgresql_connection_pool.postgresql_pool.get_connection",
        return_value=mock_conn,
    )

    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        resp = await ac.get(
            "/api/advanced_search/ranking",
            params={
                "ranking_type": "revenue",
                "year": 2024,
                "report_type": "annual",
                "quarter": 4,
                "limit": 10,
                "page": 1,
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert len(data["data"]) == 1
    assert data["data"][0]["company_name"] == "台積電"


# ========== 錯誤情境測試 ==========
@pytest.mark.asyncio
async def test_invalid_ranking_type():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        resp = await ac.get(
            "/api/advanced_search/ranking",
            params={"ranking_type": "not_exist", "year": 2024, "report_type": "annual"},
        )
    assert resp.status_code == 400
    assert "不支援的排行榜類型" in resp.text


@pytest.mark.asyncio
async def test_invalid_year():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        resp = await ac.get(
            "/api/advanced_search/ranking",
            params={"ranking_type": "revenue", "year": 1800, "report_type": "annual"},
        )
    assert resp.status_code == 400
    assert "年份必須介於 1900 和 2100" in resp.text


@pytest.mark.asyncio
async def test_invalid_quarter():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        resp = await ac.get(
            "/api/advanced_search/ranking",
            params={
                "ranking_type": "revenue",
                "year": 2024,
                "quarter": 5,
                "report_type": "quarterly",
            },
        )
    assert resp.status_code == 400
    assert "季度必須介於 1 到 4" in resp.text


@pytest.mark.asyncio
async def test_invalid_report_type():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        resp = await ac.get(
            "/api/advanced_search/ranking",
            params={
                "ranking_type": "revenue",
                "year": 2024,
                "report_type": "wrong_type",
            },
        )
    assert resp.status_code == 400
    assert "報告類型必須是" in resp.text
