import os
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

from .db import setup_sample_data, list_tables_and_columns, schema_ddl, run_select
from .llm import LLM, LLMConfig
from .nl2sql import NL2SQL

app = typer.Typer(add_completion=False, help="Agente NL2SQL com Ollama + LangChain + DuckDB")
console = Console()


def init_env():
    load_dotenv()


@app.command()
def setup(csv: str = typer.Option("./data/orders.csv", help="Caminho do CSV de exemplo"),
          table: str = typer.Option("orders", help="Nome da tabela"),
          db: Optional[str] = typer.Option(None, help="Caminho do arquivo DuckDB")):
    """Carrega dados de exemplo para o DuckDB."""
    init_env()
    count = setup_sample_data(csv_path=csv, table_name=table, db_path=db)
    console.print(f"Tabela '{table}' carregada com {count} linhas.")


@app.command()
def schema(db: Optional[str] = typer.Option(None, help="Caminho do arquivo DuckDB")):
    """Exibe as tabelas e colunas do esquema."""
    init_env()
    rows = list_tables_and_columns(db_path=db)
    if not rows:
        console.print("Nenhuma tabela encontrada. Rode: python -m nl2sql_agent setup")
        raise typer.Exit(code=1)
    table = Table(title="Esquema (main)")
    table.add_column("Tabela")
    table.add_column("Colunas")
    for t, cols in rows:
        table.add_row(t, cols)
    console.print(table)


@app.command()
def ask(
    question: Optional[str] = typer.Argument(None, help="Pergunta em linguagem natural"),
    show_sql: bool = typer.Option(False, help="Mostrar SQL gerado"),
    db: Optional[str] = typer.Option(None, help="Caminho do arquivo DuckDB"),
    model: Optional[str] = typer.Option(None, help="Nome do modelo (OLLAMA_MODEL ou GROQ_MODEL)"),
    base_url: Optional[str] = typer.Option(None, help="URL do servidor Ollama (se provider=ollama)"),
    provider: str = typer.Option("ollama", help="Provedor LLM: 'ollama' ou 'groq'"),
    sql: Optional[str] = typer.Option(None, help="Executar SQL diretamente (pula LLM)"),
):
    """Gera SQL via LLM e executa no DuckDB."""
    init_env()

    os.environ["LLM_PROVIDER"] = provider.lower()
    if model:
        if provider.lower() == "groq":
            os.environ["GROQ_MODEL"] = model
        else:
            os.environ["OLLAMA_MODEL"] = model
    if base_url and provider.lower() == "ollama":
        os.environ["OLLAMA_BASE_URL"] = base_url

    if sql:
        final_sql = sql
    else:
        if not question:
            console.print("Forneça uma pergunta ou use --sql para executar diretamente.")
            raise typer.Exit(code=2)
        llm = LLM(LLMConfig())
        agent = NL2SQL(llm)
        ddl = schema_ddl(db_path=db)
        result = agent.generate_sql(question, ddl)
        final_sql = result.sql

    if show_sql:
        console.rule("SQL")
        console.print(final_sql)

    df = run_select(final_sql, db_path=db)
    if df.empty:
        console.print("Sem resultados.")
        return
    # Print as table
    from rich import box
    t = Table(box=box.MINIMAL_HEAVY_HEAD)
    for col in df.columns:
        t.add_column(str(col))
    for _, row in df.iterrows():
        t.add_row(*[str(v) for v in row.values.tolist()])
    console.print(t)


if __name__ == "__main__":
    app()
