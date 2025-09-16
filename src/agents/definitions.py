from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.storage.sqlite import SqliteStorage
from src.tools.vertex_knowledge import VertexKnowledge

from src.tools.prompts import WEB_SEARCH, RAG, LEAD_PROMPT, CODE_STANDARDS_ENHANCED
from src.config import settings

import subprocess

def build_context_block(user: str, session_id: str) -> str:
    """Bloque de contexto estándar que se inyecta en todos los agentes."""
    return f"""
    ## CONTEXTO DE SESIÓN
    - 🆔 Session: {session_id}
    - 👤 Usuario: {user}
    - 🧠 Memoria: Resumen técnico relevante del historial (no todo crudo)
    - 🤝 Coordinación: Considera análisis previo de RAG + Web Agents
    """


agent_knowledge = VertexKnowledge(
    project_id=settings.google_project_id,
    data_store_id=settings.data_store_id,
    location=settings.google_location,
)


# === AGENTES ===

def create_web_agent(user: str, session_id: str, storage: SqliteStorage) -> Agent:
    """Agente especializado en inteligencia externa (fuentes confiables web)."""
    return Agent(
        name="Web Agent",
        role="Agente de inteligencia externa especializado en documentación oficial y fuentes confiables.",
        model=Gemini(id=settings.default_llm_pro, api_key=settings.google_api_key),
        tools=[DuckDuckGoTools()],
        instructions=WEB_SEARCH + build_context_block(user, session_id),
        show_tool_calls=True,
        markdown=True,
        storage=storage,
        user_id=user,
        session_id=session_id,
    )


def create_rag_agent(user: str, session_id: str, storage: SqliteStorage) -> Agent:
    """Agente de conocimiento interno con integración nativa a Vertex AI Search."""
    return Agent(
        name="RAG Agent",
        role="Agente de conocimiento interno. Usa Vertex AI Search para consultas.",
        model=Gemini(id=settings.default_llm_pro, api_key=settings.google_api_key),
        knowledge=agent_knowledge,
        search_knowledge=True,  
        instructions=RAG + build_context_block(user, session_id),
        show_tool_calls=True,
        markdown=True,
        storage=storage,
        user_id=user,
        session_id=session_id,
    )


def create_lead_agent(user: str, session_id: str, storage: SqliteStorage) -> Agent:
    """Orquestador del sistema multi-agente."""
    return Agent(
        name="Lead Agent",
        role=(
            "Orquestador senior del sistema multi-agente. "
            "Coordina a RAG Agent (conocimiento interno), Web Agent (fuentes externas) y Code Standards Agent (generación). "
            "Tu misión es: consolidar hallazgos, detectar discrepancias, calcular un scorecard de confianza, "
            "y generar SIEMPRE un Decision Memo válido antes de permitir cualquier acción de código."
        ),
        model=Gemini(id=settings.default_llm_pro, api_key=settings.google_api_key),
        instructions=LEAD_PROMPT + build_context_block(user, session_id),
        show_tool_calls=True,
        markdown=True,
        storage=storage,
        user_id=user,
        session_id=session_id,
    )


def create_code_standards_agent(user: str, session_id: str, storage: SqliteStorage) -> Agent:
    """Agente enterprise de revisión y generación de código."""
    return Agent(
        name="Code Standards Agent",
        role="Agente enterprise de revisión y generación de código. Solo produce artefactos si existe Decision Memo aprobado.",
        model=Gemini(id=settings.default_llm_pro, api_key=settings.google_api_key),
        instructions=CODE_STANDARDS_ENHANCED + build_context_block(user, session_id),
        show_tool_calls=True,
        markdown=True,
        storage=storage,
        user_id=user,
        session_id=session_id,
    )


# === FACTORY PRINCIPAL ===

def get_all_agents(user: str, session_id: str):
    """Retorna todos los agentes configurados para un usuario y sesión."""
    table_name = f"agent_memory_{user}_{session_id}"

    web_storage = SqliteStorage(table_name=table_name, db_file=settings.db_file_path)
    rag_storage = SqliteStorage(table_name=table_name, db_file=settings.db_file_path)
    lead_storage = SqliteStorage(table_name=table_name, db_file=settings.db_file_path)
    code_storage = SqliteStorage(table_name=table_name, db_file=settings.db_file_path)

    return (
        create_web_agent(user, session_id, web_storage),
        create_rag_agent(user, session_id, rag_storage),
        create_lead_agent(user, session_id, lead_storage),
        create_code_standards_agent(user, session_id, code_storage),
    )
