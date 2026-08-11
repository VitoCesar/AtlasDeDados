# Atlas de Dados — FastAPI

Dashboard interativo com menu **Fonte**, criado a partir de `data/Vendas.xlsx` e `data/Violencia_2025.xlsx` com Python, FastAPI, HTML, CSS e JavaScript puro.

## Como executar

Requer Python 3.11 ou superior.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload
```

Acesse `http://127.0.0.1:8000`. A primeira inicialização pode levar alguns segundos porque a API lê e normaliza as 203 mil linhas do Excel. A documentação interativa fica em `http://127.0.0.1:8000/docs`.

## Endpoints

- `GET /api/health`: saúde da API e registros por fonte.
- `GET /api/fontes`: fontes disponíveis.
- `GET /api/{fonte}/filtros`: filtros da fonte selecionada.
- `GET /api/vendas/dashboard`: indicadores de vendas.
- `GET /api/violencia/dashboard`: indicadores de violência.

O painel de violência apresenta município, natureza, dia, mês, ano, dia da semana, meio empregado, gênero, idade, escolaridade, raça e quantidade. As linhas da planilha são exibidas como **registros**; a soma da coluna `Quantidade` aparece separadamente, pois ela só está preenchida em parte da base. A coluna `Quantidade (Kg)` também possui indicador próprio.

## Testes

```powershell
pytest -q
```

O faturamento é calculado como `PrecoUnitario × Qtd. Vendida`. O continente é extraído do trecho após o último ` - ` da coluna `Localidade`. Espaços extras nas marcas são removidos para evitar categorias duplicadas.
