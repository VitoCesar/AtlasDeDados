# Atlas de Vendas — FastAPI

Dashboard interativo criado a partir de `data/Vendas.xlsx` com Python, FastAPI, HTML, CSS e JavaScript puro.

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

- `GET /api/health`: saúde da API e total de registros.
- `GET /api/filtros`: anos, meses, marcas, continentes e período disponível.
- `GET /api/dashboard`: todos os indicadores e séries agregadas.

Parâmetros opcionais de `/api/dashboard`: `ano`, `mes`, `marca` e `continente`.

## Testes

```powershell
pytest -q
```

O faturamento é calculado como `PrecoUnitario × Qtd. Vendida`. O continente é extraído do trecho após o último ` - ` da coluna `Localidade`. Espaços extras nas marcas são removidos para evitar categorias duplicadas.
