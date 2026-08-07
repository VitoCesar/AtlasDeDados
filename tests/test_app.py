from fastapi.testclient import TestClient

from app import app


def test_health_and_dashboard_totals():
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["registros"] == 203_882

        response = client.get("/api/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert round(data["resumo"]["faturamento_total"], 2) == 64_172_843.26
        assert data["resumo"]["quantidade_total"] == 405_089
        assert data["resumo"]["produto_mais_vendido"]["produto"] == "DVD M360 Preto"


def test_filters_change_result():
    with TestClient(app) as client:
        response = client.get("/api/dashboard", params={"ano": 2018, "continente": "Europa"})
        assert response.status_code == 200
        data = response.json()
        assert data["resumo"]["registros"] > 0
        assert all(row["ano_mes"].startswith("2018-") for row in data["por_ano_mes"])
        assert [row["continente"] for row in data["por_continente"]] == ["Europa"]


def test_invalid_month_is_rejected():
    with TestClient(app) as client:
        assert client.get("/api/dashboard", params={"mes": 13}).status_code == 422
