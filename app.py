from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "Vendas.xlsx"
MONTH_NAMES = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}


def load_sales(path: Path = DATA_FILE) -> pd.DataFrame:
    """Carrega e normaliza a planilha de vendas."""
    df = pd.read_excel(path, sheet_name="Planilha1", usecols="A:I")
    df = df.rename(
        columns={
            "Data da Venda": "data",
            "Produto": "produto",
            "Categoria": "categoria",
            "PrecoUnitario": "preco_unitario",
            "Custo Unitário": "custo_unitario",
            "Marca": "marca",
            "Qtd. Vendida": "quantidade",
            "Nome Cliente": "cliente",
            "Localidade": "localidade",
        }
    )

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["preco_unitario"] = pd.to_numeric(df["preco_unitario"], errors="coerce")
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce")
    df = df.dropna(subset=["data", "produto", "preco_unitario", "quantidade"]).copy()

    for column in ["produto", "categoria", "marca", "cliente", "localidade"]:
        df[column] = df[column].astype("string").str.strip()

    df["faturamento"] = df["preco_unitario"] * df["quantidade"]
    df["ano"] = df["data"].dt.year.astype(int)
    df["mes"] = df["data"].dt.month.astype(int)
    df["ano_mes"] = df["data"].dt.to_period("M").astype(str)
    df["continente"] = df["localidade"].str.rsplit(" - ", n=1).str[-1]
    return df


def records(frame: pd.DataFrame) -> list[dict]:
    return frame.to_dict(orient="records")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sales = load_sales()
    yield
    app.state.sales = None


app = FastAPI(
    title="API do Dashboard de Vendas",
    description="Indicadores calculados a partir do arquivo Vendas.xlsx.",
    version="1.0.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/health", tags=["Sistema"])
async def health(request: Request):
    return {"status": "ok", "registros": len(request.app.state.sales)}


@app.get("/api/filtros", tags=["Dashboard"])
async def filters(request: Request):
    df = request.app.state.sales
    return {
        "anos": sorted(df["ano"].unique().tolist()),
        "meses": [{"valor": month, "nome": MONTH_NAMES[month]} for month in range(1, 13)],
        "marcas": sorted(df["marca"].dropna().unique().tolist()),
        "continentes": sorted(df["continente"].dropna().unique().tolist()),
        "periodo": {
            "inicio": df["data"].min().date().isoformat(),
            "fim": df["data"].max().date().isoformat(),
        },
    }


@app.get("/api/dashboard", tags=["Dashboard"])
async def dashboard_data(
    request: Request,
    ano: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    mes: Annotated[int | None, Query(ge=1, le=12)] = None,
    marca: str | None = None,
    continente: str | None = None,
):
    df = request.app.state.sales
    if ano is not None:
        df = df[df["ano"] == ano]
    if mes is not None:
        df = df[df["mes"] == mes]
    if marca:
        df = df[df["marca"] == marca.strip()]
    if continente:
        df = df[df["continente"] == continente.strip()]

    total_revenue = float(df["faturamento"].sum())
    total_quantity = float(df["quantidade"].sum())

    time_series = (
        df.groupby("ano_mes", as_index=False)
        .agg(faturamento=("faturamento", "sum"), quantidade=("quantidade", "sum"))
        .sort_values("ano_mes")
    )
    brand_revenue = (
        df.groupby("marca", as_index=False)["faturamento"]
        .sum()
        .sort_values("faturamento", ascending=False)
    )
    continent_revenue = (
        df.groupby("continente", as_index=False)["faturamento"]
        .sum()
        .sort_values("faturamento", ascending=False)
    )
    top_products = (
        df.groupby("produto", as_index=False)
        .agg(quantidade=("quantidade", "sum"), faturamento=("faturamento", "sum"))
        .sort_values(["quantidade", "faturamento"], ascending=False)
    )
    top_product = None if top_products.empty else top_products.iloc[0].to_dict()

    return {
        "resumo": {
            "faturamento_total": total_revenue,
            "quantidade_total": total_quantity,
            "produto_mais_vendido": top_product,
            "registros": int(len(df)),
        },
        "por_ano_mes": records(time_series),
        "por_marca": records(brand_revenue),
        "por_continente": records(continent_revenue),
        "filtros_aplicados": {
            "ano": ano, "mes": mes, "marca": marca, "continente": continente
        },
    }
