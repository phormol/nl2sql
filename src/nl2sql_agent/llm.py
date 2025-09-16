from __future__ import annotations
from dataclasses import dataclass
import os
from typing import Optional
from langchain_ollama import ChatOllama
try:
    from langchain_core.messages import SystemMessage, HumanMessage  # langchain>=0.2
except Exception:  # fallback for older versions
    try:
        from langchain.schema import SystemMessage, HumanMessage  # type: ignore
    except Exception:
        SystemMessage = None  # type: ignore
        HumanMessage = None  # type: ignore
try:
    from langchain_groq import ChatGroq
except Exception:  # package optional
    ChatGroq = None  # type: ignore


@dataclass
class LLMConfig:
    provider: str = os.getenv("LLM_PROVIDER", "ollama")  # 'ollama' | 'groq'
    # Ollama config
    base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model: str = os.getenv("OLLAMA_MODEL", "llama3.1")
    # Groq config
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    # common sampling
    temperature: float = float(os.getenv("LLM_TEMPERATURE", os.getenv("OLLAMA_TEMPERATURE", "0")))
    top_p: float = float(os.getenv("LLM_TOP_P", os.getenv("OLLAMA_TOP_P", "0.9")))


class LLM:
    def __init__(self, cfg: Optional[LLMConfig] = None):
        self.cfg = cfg or LLMConfig()
        provider = (self.cfg.provider or "ollama").lower()
        if provider == "groq":
            if ChatGroq is None:
                raise ImportError("langchain-groq não instalado. Adicione 'langchain-groq' ao requirements.txt")
            if not self.cfg.groq_api_key:
                raise ValueError("GROQ_API_KEY não definido. Configure variável de ambiente.")
            self.client = ChatGroq(
                api_key=self.cfg.groq_api_key,
                model=self.cfg.groq_model,
                temperature=self.cfg.temperature,
                top_p=self.cfg.top_p,
            )
        else:
            # default: ollama
            self.client = ChatOllama(
                base_url=self.cfg.base_url,
                model=self.cfg.model,
                temperature=self.cfg.temperature,
                top_p=self.cfg.top_p,
            )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        # Compose messages for a chat model (prefer LangChain message objects)
        if SystemMessage and HumanMessage:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        else:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        resp = self.client.invoke(messages)
        # Extract content from BaseMessage or fallback to string
        return getattr(resp, "content", str(resp))
