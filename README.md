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

## Fluxo obrigatório de contribuição

Toda correção, melhoria ou nova funcionalidade começa em uma issue. O trabalho deve ocorrer em branch dedicada e ser entregue por pull request. A descrição do PR precisa mencionar a issue com `Closes #123` ou `Refs #123`. Deploys devem usar apenas commits revisados e aprovados por PR. Consulte `AGENTS.md` e os templates em `.github/`.

## Qualidade e testes

```powershell
pip install -r requirements-dev.txt
npm install
ruff check .
python scripts/check_architecture.py
npm run lint
npm run deadcode
coverage run -m pytest -q
npx playwright install chromium
npm run test:e2e
```

Biome analisa JavaScript, Commitlint valida commits convencionais, Knip detecta código/dependências sem uso, o contrato arquitetural impede dependências e segredos indevidos, e Stryker executa testes de mutação com `npm run test:mutation`. O CI publica cobertura no Codecov.

## Observabilidade

Logs são estruturados em JSON e toda resposta inclui `x-request-id`. Sentry e OpenTelemetry ficam desativados quando suas variáveis não estão presentes. Copie `.env.example` para configurar:

- `SENTRY_DSN`: erros e tracing no Sentry.
- `OTEL_EXPORTER_OTLP_ENDPOINT`: endpoint OTLP. Use o agente Datadog em `http://localhost:4318` ou `https://otlp.nr-data.net` para New Relic.
- `OTEL_EXPORTER_OTLP_HEADERS`: cabeçalhos de autenticação exigidos pelo provedor.

Nenhuma credencial deve ser adicionada ao repositório.

## Carregamento e motion

A interface usa skeletons durante consultas, barra de progresso acessível, cancelamento de requisições obsoletas e renderização lazy dos painéis via `IntersectionObserver`. Entradas e saídas são rápidas e discretas; `prefers-reduced-motion` preserva todos os estados sem movimento perceptível.

O faturamento é calculado como `PrecoUnitario × Qtd. Vendida`. O continente é extraído do trecho após o último ` - ` da coluna `Localidade`. Espaços extras nas marcas são removidos para evitar categorias duplicadas.
