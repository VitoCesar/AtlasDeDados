from fastapi.testclient import TestClient
from app import app


def test_health_lists_both_sources():
    with TestClient(app) as client:
        data = client.get("/api/health").json()
        assert data["status"] == "ok"
        assert data["fontes"] == {"vendas": 203_882, "violencia": 2_691}


def test_frontend_assets_are_versioned_to_prevent_stale_api_calls():
    with TestClient(app) as client:
        html = client.get("/").text
        assert "app.js?v=2.0.1" in html
        assert "styles.css?v=2.0.1" in html
        javascript = client.get("/static/app.js").text
        assert "/api/${source}/filtros" in javascript
        assert 'fetch("/api/filtros")' not in javascript


def test_violence_filters_are_json_serializable():
    with TestClient(app) as client:
        response = client.get("/api/violencia/filtros")
        assert response.status_code == 200
        data = response.json()
        assert data["anos"] == [2025]
        assert data["meses"][0] == {"valor": 1, "nome": "Jan"}
        assert data["meses"][-1] == {"valor": 12, "nome": "Dez"}


def test_sales_totals_are_preserved():
    with TestClient(app) as client:
        response = client.get("/api/vendas/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert round(data["resumo"]["faturamento_total"], 2) == 64_172_843.26
        assert data["resumo"]["quantidade_total"] == 405_089
        assert data["resumo"]["produto_mais_vendido"]["produto"] == "DVD M360 Preto"


def test_violence_dashboard_has_all_requested_dimensions():
    with TestClient(app) as client:
        response = client.get("/api/violencia/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["resumo"]["ocorrencias"] == 2_691
        assert data["resumo"]["quantidade_informada"] == 310
        assert round(data["resumo"]["quantidade_kg"], 5) == 115.82319
        for key in ["por_municipio", "por_natureza", "por_dia", "por_mes", "por_ano", "por_dia_semana", "por_meio_empregado", "por_genero", "por_idade", "por_escolaridade", "por_raca"]:
            assert key in data and data[key]


def test_violence_filters_and_validation():
    with TestClient(app) as client:
        filtered = client.get("/api/violencia/dashboard", params={"municipio": "Ibiapina", "mes": 1}).json()
        assert 0 < filtered["resumo"]["ocorrencias"] < 2_691
        assert [row["municipio"] for row in filtered["por_municipio"]] == ["Ibiapina"]
        assert client.get("/api/violencia/dashboard", params={"mes": 13}).status_code == 422
