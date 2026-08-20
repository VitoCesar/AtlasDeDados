from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from observability import install_observability

BASE_DIR = Path(__file__).resolve().parent
SALES_FILE = BASE_DIR / "data" / "Vendas.xlsx"
VIOLENCE_FILE = BASE_DIR / "data" / "Violencia_2025.xlsx"
MONTH_NAMES = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
TEXT_FIXES = {
    "Tiangu�": "Tianguá", "Vi�osa do Cear�": "Viçosa do Ceará", "S�o Benedito": "São Benedito", "Croat�": "Croatá",
    "Apreens�o de Armas de Fogo": "Apreensão de Armas de Fogo", "Ind�genas": "Indígenas", "FEMINIC�DIO": "FEMINICÍDIO",
    "PRECONCEITO DE RA�A OU DE COR - CONDUTA HOMOF�BICA": "PRECONCEITO DE RAÇA OU DE COR - CONDUTA HOMOFÓBICA",
    "PRECONCEITO DE RA�A OU DE COR - CONDUTA TRANSF�BICA": "PRECONCEITO DE RAÇA OU DE COR - CONDUTA TRANSFÓBICA",
    "S�bado": "Sábado", "Ter�a": "Terça", "N�o Informado": "Não Informado", "N�o Informada": "Não Informada",
    "Coca�na": "Cocaína", "Ensino M�dio Completo": "Ensino Médio Completo", "Ensino M�dio Incompleto": "Ensino Médio Incompleto",
    "N�o Alfabetizado": "Não Alfabetizado", "Ind�gena": "Indígena",
}


def clean_text(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().replace(TEXT_FIXES)


def load_sales(path: Path = SALES_FILE) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Planilha1", usecols="A:I")
    df.columns = ["data", "produto", "categoria", "preco_unitario", "custo_unitario", "marca", "quantidade", "cliente", "localidade"]
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["preco_unitario"] = pd.to_numeric(df["preco_unitario"], errors="coerce")
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce")
    df = df.dropna(subset=["data", "produto", "preco_unitario", "quantidade"]).copy()
    for column in ["produto", "categoria", "marca", "cliente", "localidade"]:
        df[column] = clean_text(df[column])
    df["faturamento"] = df["preco_unitario"] * df["quantidade"]
    df["ano"] = df["data"].dt.year.astype(int)
    df["mes"] = df["data"].dt.month.astype(int)
    df["ano_mes"] = df["data"].dt.to_period("M").astype(str)
    df["continente"] = df["localidade"].str.rsplit(" - ", n=1).str[-1]
    return df


def load_violence(path: Path = VIOLENCE_FILE) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Planilha1")
    df.columns = ["municipio", "natureza", "dia", "mes", "ano", "dia_semana", "meio_empregado", "genero", "idade", "escolaridade", "raca", "quantidade", "quantidade_kg"]
    text_columns = ["municipio", "natureza", "dia_semana", "meio_empregado", "genero", "idade", "escolaridade", "raca"]
    for column in text_columns:
        df[column] = clean_text(df[column]).fillna("Não Informada")
    for column in ["dia", "mes", "ano", "quantidade", "quantidade_kg"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=["municipio", "natureza", "dia", "mes", "ano"]).copy()
    df[["dia", "mes", "ano"]] = df[["dia", "mes", "ano"]].astype(int)
    df["data"] = pd.to_datetime(dict(year=df["ano"], month=df["mes"], day=df["dia"]), errors="coerce")
    return df


def records(frame: pd.DataFrame) -> list[dict]:
    return frame.to_dict(orient="records")


def distribution(df: pd.DataFrame, column: str, limit: int | None = None, chronological: bool = False) -> list[dict]:
    grouped = df.groupby(column, dropna=False).size().reset_index(name="ocorrencias")
    grouped[column] = grouped[column].astype(str)
    grouped = grouped.sort_values(column if chronological else "ocorrencias", ascending=chronological)
    if limit:
        grouped = grouped.head(limit)
    return records(grouped)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sales = load_sales()
    app.state.violence = load_violence()
    yield
    app.state.sales = app.state.violence = None


app = FastAPI(title="API Atlas de Dados", description="Dashboards de vendas e violência construídos a partir de arquivos Excel.", version="2.0.0", lifespan=lifespan)
install_observability(app)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/fontes", tags=["Sistema"])
async def sources():
    return [{"id": "vendas", "nome": "Vendas"}, {"id": "violencia", "nome": "Violência 2025"}]


@app.get("/api/health", tags=["Sistema"])
async def health(request: Request):
    return {"status": "ok", "fontes": {"vendas": len(request.app.state.sales), "violencia": len(request.app.state.violence)}}


@app.get("/api/{source}/filtros", tags=["Dashboard"])
async def filters(source: str, request: Request):
    if source == "vendas":
        df = request.app.state.sales
        return {"anos": sorted(df.ano.unique().tolist()), "meses": [{"valor": m, "nome": MONTH_NAMES[m]} for m in range(1, 13)], "marcas": sorted(df.marca.unique().tolist()), "continentes": sorted(df.continente.unique().tolist()), "periodo": {"inicio": df.data.min().date().isoformat(), "fim": df.data.max().date().isoformat()}}
    if source == "violencia":
        df = request.app.state.violence
        months = [int(month) for month in sorted(df.mes.unique())]
        return {"anos": [int(year) for year in sorted(df.ano.unique())], "meses": [{"valor": month, "nome": MONTH_NAMES[month]} for month in months], "municipios": sorted(df.municipio.unique().tolist()), "naturezas": sorted(df.natureza.unique().tolist()), "dias_semana": sorted(df.dia_semana.unique().tolist()), "meios": sorted(df.meio_empregado.unique().tolist()), "generos": sorted(df.genero.unique().tolist()), "periodo": {"inicio": df.data.min().date().isoformat(), "fim": df.data.max().date().isoformat()}}
    raise HTTPException(404, "Fonte não encontrada")


@app.get("/api/vendas/dashboard", tags=["Vendas"])
async def sales_dashboard(request: Request, ano: Annotated[int | None, Query(ge=2000, le=2100)] = None, mes: Annotated[int | None, Query(ge=1, le=12)] = None, marca: str | None = None, continente: str | None = None):
    df = request.app.state.sales
    if ano is not None: df = df[df.ano == ano]
    if mes is not None: df = df[df.mes == mes]
    if marca: df = df[df.marca == marca.strip()]
    if continente: df = df[df.continente == continente.strip()]
    time_series = df.groupby("ano_mes", as_index=False).agg(faturamento=("faturamento", "sum"), quantidade=("quantidade", "sum")).sort_values("ano_mes")
    brands = df.groupby("marca", as_index=False).faturamento.sum().sort_values("faturamento", ascending=False)
    continents = df.groupby("continente", as_index=False).faturamento.sum().sort_values("faturamento", ascending=False)
    products = df.groupby("produto", as_index=False).agg(quantidade=("quantidade", "sum"), faturamento=("faturamento", "sum")).sort_values(["quantidade", "faturamento"], ascending=False)
    return {"resumo": {"faturamento_total": float(df.faturamento.sum()), "quantidade_total": float(df.quantidade.sum()), "produto_mais_vendido": None if products.empty else products.iloc[0].to_dict(), "registros": len(df)}, "por_ano_mes": records(time_series), "por_marca": records(brands), "por_continente": records(continents)}


@app.get("/api/violencia/dashboard", tags=["Violência"])
async def violence_dashboard(request: Request, ano: Annotated[int | None, Query(ge=2000, le=2100)] = None, mes: Annotated[int | None, Query(ge=1, le=12)] = None, municipio: str | None = None, natureza: str | None = None, dia_semana: str | None = None, meio_empregado: str | None = None, genero: str | None = None):
    df = request.app.state.violence
    filters_map = {"ano": ano, "mes": mes, "municipio": municipio, "natureza": natureza, "dia_semana": dia_semana, "meio_empregado": meio_empregado, "genero": genero}
    for column, value in filters_map.items():
        if value is not None and value != "": df = df[df[column] == (value.strip() if isinstance(value, str) else value)]
    month = df.groupby("mes").size().reindex(range(1, 13), fill_value=0).rename("ocorrencias").reset_index()
    month["rotulo"] = month.mes.map(MONTH_NAMES)
    day = df.groupby("dia").size().reindex(range(1, 32), fill_value=0).rename("ocorrencias").reset_index()
    numeric_age = pd.to_numeric(df.idade, errors="coerce")
    age_groups = pd.cut(numeric_age, bins=[-1, 17, 24, 34, 44, 59, 200], labels=["0–17", "18–24", "25–34", "35–44", "45–59", "60+"])
    ages = age_groups.value_counts(sort=False).rename_axis("idade").reset_index(name="ocorrencias")
    uninformed_age = int(numeric_age.isna().sum())
    if uninformed_age: ages.loc[len(ages)] = ["Não informada", uninformed_age]
    return {"resumo": {"ocorrencias": len(df), "quantidade_informada": float(df.quantidade.fillna(0).sum()), "quantidade_kg": float(df.quantidade_kg.fillna(0).sum()), "municipios": int(df.municipio.nunique()), "vitimas_com_idade": int(numeric_age.notna().sum())}, "por_mes": records(month), "por_dia": records(day), "por_municipio": distribution(df, "municipio"), "por_natureza": distribution(df, "natureza"), "por_ano": distribution(df, "ano", chronological=True), "por_dia_semana": distribution(df, "dia_semana"), "por_meio_empregado": distribution(df, "meio_empregado"), "por_genero": distribution(df, "genero"), "por_idade": records(ages), "por_escolaridade": distribution(df, "escolaridade"), "por_raca": distribution(df, "raca")}
