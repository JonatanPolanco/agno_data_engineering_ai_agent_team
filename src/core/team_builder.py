from agno.team.team import Team
from agno.storage.sqlite import SqliteStorage
from agno.agent import Agent
from agno.models.google import Gemini
from src.agents.definitions import get_all_agents
from src.tools.prompts import LEAD_PROMPT
from src.config import settings
from datetime import datetime
import uuid

def generate_session_id(user: str) -> str:
    """Genera un session_id único para el usuario."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    return f"{user}_{timestamp}_{short_uuid}"

def build_team(user: str, session_id: str) -> Team:
    # Obtener los 4 agentes (ahora sin pasar storage)
    web_agent, rag_agent, lead_agent, code_agent = get_all_agents(user, session_id)
    
    # Storage del Team
    table_name = f"{settings.db_table_prefix}_{user}_{session_id}"
    team_storage = SqliteStorage(table_name=table_name, db_file=settings.db_file_path)
    
    
    # Construir el Team con los 4 miembros (Lead primero para visibilidad)
    return Team(
        members=[lead_agent, web_agent, rag_agent, code_agent],
        model=Gemini(
            id=settings.default_llm_pro,
            api_key=settings.google_api_key,
        ),
        storage=team_storage,
        user_id=user,
        session_id=session_id,
        mode="coordinate",
        success_criteria="""
            Proveer una respuesta técnica clara, estructurada y accionable para ingenieros de datos senior.
            En el caso de no tener informacion del agente RAG, indicar que no se encontró información relevante.
            """,
        instructions=LEAD_PROMPT + f"""

        CONTEXTO ACTUAL: Sesión {session_id} - Usuario: {user}
        FECHA: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        HISTORIAL DISPONIBLE: Tienes acceso al historial técnico de la sesión (resumido cuando aplique).

        REGLAS ESTRICTAS DE COORDINACIÓN:
        1. Antes de delegar, proporciona contexto relevante (no enviar el historial completo si es muy largo).
        2. El Lead Agent es responsable del Decision Memo; el Team orchestration debe delegar la generación y validar ACKs.
        3. Si existe discrepancia entre RAG y Web, marca la discrepancia y solicita validación adicional.
        4. Code Agent sólo debe ejecutarse si el Decision Memo está aprobado y los ACKs no bloquean.
        """,
        add_datetime_to_instructions=True,
        show_tool_calls=True,
        markdown=True,
        enable_agentic_context=True,
        show_members_responses=True,
    )
