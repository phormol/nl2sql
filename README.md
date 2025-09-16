# NL2SQL com Ollama/Groq + LangChain + DuckDB

Este projeto cria um agente que converte perguntas em linguagem natural em consultas SQL (NL2SQL) e executa-as em um banco local DuckDB, usando modelos via Ollama/Groq e a orquestração do LangChain.

## Requisitos

- Python 3.10–3.12
- Ollama instalado (Windows): https://ollama.com/download
- Modelo Ollama (sugestões): `llama3.1:8b-instruct` ou `llama3.1`.
- PowerShell (padrão no Windows)
- (Opcional) Conta na Groq e uma `GROQ_API_KEY` se preferir usar a API da Groq em vez do Ollama

## Instalação

1) Crie e ative um ambiente virtual (opcional, recomendado)

```powershell
python -m venv .venv
```

2) Instale as dependências

```powershell

pip install -r requirements.txt
```

3) Baixe um modelo no Ollama (ex.: llama3.1)

```powershell
ollama pull llama3.1
```

## Uso rápido

$env:PYTHONPATH="src"


- Preparar dados de exemplo no DuckDB:

```powershell
python -m nl2sql_agent setup
```

- Ver esquema (tabelas e colunas):

```powershell
python -m nl2sql_agent schema
```

- Fazer uma pergunta em linguagem natural e obter resposta (gera SQL, valida e executa):

```powershell
python -m nl2sql_agent ask "Quais são os 5 produtos mais vendidos por receita?"
```

### Usar com Groq (opcional)

Defina as variáveis de ambiente (via `.env.local` ou direto no PowerShell) e rode o mesmo comando `ask`.

- Via `.env.local` usando python-dotenv:

```powershell
# Edite .env.local e inclua, por exemplo:
# LLM_PROVIDER=groq
# GROQ_API_KEY=<sua_chave>
# GROQ_MODEL=llama-3.1-8b-instant

python -m dotenv -f .env.local run -- python -m nl2sql_agent ask "Quantas vezes o produto Monitor foi vendido?"
```

- Ou definindo variáveis no PowerShell (sem .env):

```powershell
$env:LLM_PROVIDER="groq"; $env:GROQ_API_KEY="<sua_chave>"; $env:GROQ_MODEL="llama-3.1-8b-instant"; \
python -m nl2sql_agent ask "Quantas vezes o produto Monitor foi vendido?"
```

## Configuração

- Variáveis (.env – opcional):

```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
DUCKDB_PATH=./db/nl2sql.duckdb
# Provider do LLM: 'ollama' (padrão) ou 'groq'
LLM_PROVIDER=ollama

# Groq (somente se usar Groq)
# NUNCA commite suas chaves em repositório público
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
```

## Limitações e segurança

- O agente valida para executar apenas consultas de leitura (SELECT) e adiciona LIMIT padrão.
- Para cargas maiores, ajuste LIMIT ou filtros.

## Estrutura

- `src/nl2sql_agent/cli.py` – CLI Typer
- `src/nl2sql_agent/llm.py` – wrapper do LLM (Ollama)
- `src/nl2sql_agent/db.py` – conexão DuckDB e utilitários
- `src/nl2sql_agent/nl2sql.py` – prompt e execução NL→SQL
- `data/` – CSV de exemplo
- `db/` – arquivo DuckDB

## Dicas

- Se o Ollama não estiver rodando, abra o app Ollama ou inicie o serviço.
- Para debugar, use `--verbose` ou veja o SQL gerado com `--show-sql` no `ask`.

## Interface Web (Streamlit)

Opcionalmente, você pode usar uma interface web simples para perguntar em linguagem natural e ver o SQL e os resultados.

1) Instale as dependências (no mesmo ambiente):

```powershell
pip install -r requirements.txt
```

2) Rode a app:

```powershell
streamlit run streamlit_app.py
```

3) Use a barra lateral para:
- Definir o caminho do banco DuckDB (padrão `./db/nl2sql.duckdb`)
- Selecionar o provedor LLM: `ollama` ou `groq`
- Ajustar configurações do provedor escolhido (Ollama: URL/modelo; Groq: API key/modelo) e parâmetros (temperature, top_p)
- Carregar os dados de exemplo (`./data/orders.csv`) na tabela `orders`

4) Na aba "Perguntar", escreva sua pergunta. Ative "Mostrar SQL" para visualizar a consulta gerada.

Requisitos: 
- Para Ollama: o serviço precisa estar rodando e o modelo escolhido disponível (`ollama pull <modelo>`).
- Para Groq: é necessário definir `GROQ_API_KEY` e escolher um `GROQ_MODEL` válido.

