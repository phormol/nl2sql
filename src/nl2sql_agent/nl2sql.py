from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from .db import is_safe_select, ensure_limit


SYSTEM_PROMPT = (
    "Você é um tradutor NL2SQL para DuckDB. Gere APENAS SQL válido para DuckDB, "
    "sem comentários nem explicações. Não use DDL nem DML, apenas SELECT/CTEs. "
    "Evite funções não suportadas. Use nomes de colunas/tabelas exatamente como no esquema."
)


@dataclass
class NL2SQLResult:
    sql: str


class NL2SQL:
    def __init__(self, llm):
        self.llm = llm

    def build_user_prompt(self, question: str, schema_text: str) -> str:
        return (
            "Esquema das tabelas (DuckDB):\n" + schema_text + "\n\n" +
            "Tarefa: Escreva uma única consulta SQL (DuckDB) que responde à pergunta.\n" +
            "Regras: SOMENTE SQL. Deve começar com SELECT ou WITH. Sem comentários.\n\n" +
            f"Pergunta: {question}\n"
        )

    def generate_sql(self, question: str, schema_text: str) -> NL2SQLResult:
        user_prompt = self.build_user_prompt(question, schema_text)
        raw = self.llm.generate(SYSTEM_PROMPT, user_prompt)
        sql = raw.strip().strip('`').strip()
        # Some models wrap in code fences; strip common prefixes
        if sql.lower().startswith("sql"):
            sql = sql[3:].lstrip(':').strip()
        # Safety post-checks are handled by db helpers
        sql = ensure_limit(sql)
        return NL2SQLResult(sql=sql)

    def is_sql_safe(self, sql: str) -> bool:
        return is_safe_select(sql)
