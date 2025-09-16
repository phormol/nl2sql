import os
import pandas as pd
import streamlit as st

# Ensure local src/ is importable if running without installation
try:
    import nl2sql_agent  # type: ignore
except ImportError:
    import sys, pathlib
    root = pathlib.Path(__file__).parent
    src = root / "src"
    if src.is_dir() and str(src) not in sys.path:
        sys.path.insert(0, str(src))

from nl2sql_agent.db import (
    DEFAULT_DB_PATH,
    setup_sample_data,
    list_tables_and_columns,
    schema_ddl,
    run_select,
)
from nl2sql_agent.llm import LLM, LLMConfig
from nl2sql_agent.nl2sql import NL2SQL


st.set_page_config(page_title="NL2SQL DuckDB", page_icon="🦆", layout="wide")
st.title("NL2SQL para DuckDB 🦆")

with st.sidebar:
    st.header("Configurações")

    db_path = st.text_input("Caminho do DuckDB", value=DEFAULT_DB_PATH)

    provider = st.selectbox("Provedor LLM", options=["ollama", "groq"], index=0)

    # Parâmetros comuns de amostragem
    temperature = st.number_input(
        "temperature", value=float(os.getenv("LLM_TEMPERATURE", os.getenv("OLLAMA_TEMPERATURE", "0"))),
        min_value=0.0, max_value=2.0, step=0.1
    )
    top_p = st.number_input(
        "top_p", value=float(os.getenv("LLM_TOP_P", os.getenv("OLLAMA_TOP_P", "0.9"))),
        min_value=0.0, max_value=1.0, step=0.05
    )

    if provider == "ollama":
        with st.expander("Modelo (Ollama)", expanded=True):
            base_url = st.text_input("OLLAMA_BASE_URL", value=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
            model = st.text_input("OLLAMA_MODEL", value=os.getenv("OLLAMA_MODEL", "llama3.1"))
            groq_api_key = ""
            groq_model = ""
    else:
        with st.expander("Modelo (Groq)", expanded=True):
            groq_api_key = st.text_input("GROQ_API_KEY", value=os.getenv("GROQ_API_KEY", ""), type="password")
            groq_model = st.text_input("GROQ_MODEL", value=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"))
            base_url = ""
            model = ""

    st.divider()
    st.caption("Dica: Use o botão abaixo para carregar o CSV de exemplo em DuckDB.")
    if st.button("Carregar dados de exemplo", use_container_width=True):
        try:
            count = setup_sample_data(csv_path="./data/orders.csv", table_name="orders", db_path=db_path)
            st.success(f"Tabela 'orders' carregada com {count} linhas.")
        except Exception as e:
            st.error(f"Falha ao carregar dados: {e}")


@st.cache_data(show_spinner=False)
def get_schema_text(db_path: str) -> str:
    return schema_ddl(db_path=db_path)


@st.cache_resource(show_spinner=False)
def get_agent(cfg: LLMConfig) -> NL2SQL:
    llm = LLM(cfg)
    return NL2SQL(llm)


tab_query, tab_schema = st.tabs(["Perguntar", "Esquema"])

with tab_schema:
    try:
        rows = list_tables_and_columns(db_path=db_path)
        if not rows:
            st.info("Nenhuma tabela encontrada. Use a barra lateral para carregar dados.")
        else:
            df_schema = pd.DataFrame(rows, columns=["Tabela", "Colunas"])
            st.dataframe(df_schema, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao listar esquema: {e}")

with tab_query:
    question = st.text_area("Pergunta em linguagem natural", placeholder="Ex.: Qual o total de vendas por país?", height=100)

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        run_clicked = st.button("Gerar e executar", type="primary")
    with col2:
        show_sql = st.toggle("Mostrar SQL", value=True)

    if run_clicked:
        try:
            cfg = LLMConfig(
                provider=provider,
                base_url=base_url,
                model=model,
                groq_api_key=groq_api_key,
                groq_model=groq_model,
                temperature=temperature,
                top_p=top_p,
            )
            agent = get_agent(cfg)
            ddl = get_schema_text(db_path)

            with st.status("Gerando SQL…", expanded=False):
                result = agent.generate_sql(question, ddl)
                sql = result.sql

            if show_sql:
                st.code(sql, language="sql")

            with st.spinner("Executando consulta no DuckDB…"):
                df = run_select(sql, db_path=db_path)

            if df is None or len(df) == 0:
                st.info("Sem resultados.")
            else:
                st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Erro: {e}")

st.caption("Powered by LangChain + Ollama/Groq + DuckDB")
