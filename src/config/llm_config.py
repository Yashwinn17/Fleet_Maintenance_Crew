"""
LLM Provider Factory
Supports Ollama (local), Groq (hosted), and OpenRouter (hosted).

Hierarchical CrewAI benefits from stronger manager models for tool delegation.
"""

import os

from crewai import LLM
from dotenv import load_dotenv

load_dotenv()


def _normalize_provider(provider: str | None) -> str:
    return (provider or os.getenv("LLM_PROVIDER", "ollama")).strip().lower()


def _build_ollama_llm(model: str | None = None) -> LLM:
    ollama_model = model or os.getenv("OLLAMA_MODEL", "ollama/llama3.1:8b")
    print(f"[LLM Factory] Using Ollama: {ollama_model}")
    return LLM(
        model=ollama_model,
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


def _build_groq_llm(model: str | None = None) -> LLM:
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise EnvironmentError(
            "GROQ_API_KEY is missing. Add it to your .env file to use the Groq provider."
        )
    groq_model = model or os.getenv("GROQ_MODEL", "groq/llama-3.3-70b-versatile")
    print(f"[LLM Factory] Using Groq: {groq_model}")
    return LLM(model=groq_model, api_key=groq_key, temperature=0)


def _build_openrouter_llm(model: str | None = None) -> LLM:
    or_key = os.getenv("OPENROUTER_API_KEY")
    if not or_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY is missing. Add it to your .env file to use OpenRouter."
        )
    or_model = model or os.getenv(
        "OPENROUTER_MODEL", "openrouter/meta-llama/llama-3.3-70b-instruct"
    )
    print(f"[LLM Factory] Using OpenRouter: {or_model}")
    return LLM(
        model=or_model,
        api_key=or_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
    )


def get_llm(provider: str | None = None, model: str | None = None) -> LLM:
    """
    Return an LLM instance based on provider preference and env config.

    Priority order:
    1. Explicit provider arg
    2. LLM_PROVIDER env var
    3. Default to Ollama
    """
    provider_name = _normalize_provider(provider)

    if provider_name == "ollama":
        return _build_ollama_llm(model=model)
    if provider_name == "groq":
        return _build_groq_llm(model=model)
    if provider_name == "openrouter":
        return _build_openrouter_llm(model=model)

    raise ValueError(
        f"Unsupported LLM provider '{provider_name}'. Expected 'ollama', 'groq', or 'openrouter'."
    )


def get_manager_llm(provider: str | None = None, model: str | None = None) -> LLM:
    """
    Dedicated LLM for the hierarchical process manager.
    Allows a stronger provider-specific model override for delegation.
    """
    provider_name = _normalize_provider(provider)

    if provider_name == "groq":
        manager_model = model or os.getenv(
            "GROQ_MANAGER_MODEL",
            os.getenv("GROQ_MODEL", "groq/llama-3.3-70b-versatile"),
        )
        print(f"[LLM Factory] Manager LLM: Groq ({manager_model})")
        return _build_groq_llm(model=manager_model)

    if provider_name == "openrouter":
        manager_model = model or os.getenv(
            "OPENROUTER_MANAGER_MODEL",
            os.getenv("OPENROUTER_MODEL", "openrouter/meta-llama/llama-3.3-70b-instruct"),
        )
        print(f"[LLM Factory] Manager LLM: OpenRouter ({manager_model})")
        return _build_openrouter_llm(model=manager_model)

    manager_model = model or os.getenv(
        "OLLAMA_STRONG_MODEL",
        os.getenv("OLLAMA_MODEL", "ollama/llama3.1:8b"),
    )
    print(f"[LLM Factory] Manager LLM: Ollama ({manager_model})")
    return _build_ollama_llm(model=manager_model)
