
from agno.team.team import Team
from agno.models.google import Gemini
from src.agents.definitions import get_all_agents
from src.tools.prompts import LEAD_PROMPT
from src.config import settings
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

# ==================================================================
#  GENERACIÓN DE SESSION_ID
# ==================================================================
def generate_session_id(user: str) -> str:
    """Genera un session_id único para el usuario."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    return f"{user}_{timestamp}_{short_uuid}"

# ==================================================================
#  CONSTRUCCIÓN DEL TEAM
# ==================================================================
def build_team(user: str, session_id: str) -> Team:
    agents_dict = get_all_agents(user, session_id)
    
    if agents_dict is None:
        logger.error(f"No se pudieron crear los agentes para la sesión {session_id}.")
        return None
    
    # --- ✅ CORRECCIÓN: Accedemos a los agentes por su clave en el diccionario ---
    # No desempaquetamos. Extraemos cada agente explícitamente.
    lead_agent = agents_dict.get("Lead Agent")
    web_agent = agents_dict.get("Web Agent")
    rag_agent = agents_dict.get("RAG Agent")
    code_agent = agents_dict.get("Code Standards Agent")
    
    # Verificamos que todos los agentes necesarios se hayan creado
    if not all([lead_agent, web_agent, rag_agent, code_agent]):
        logger.error("Fallo al crear uno o más agentes necesarios para el equipo.")
        return None

    # Instrucciones principales para el equipo
    team_instructions = LEAD_PROMPT + f"""
    CONTEXTO ACTUAL: Sesión {session_id} - Usuario: {user}
    FECHA: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    REGLAS ESTRICTAS DE COORDINACIÓN:
    1. Antes de delegar, proporciona contexto relevante.
    2. El Lead Agent es responsable del Decision Memo.
    3. Si existe discrepancia entre RAG y Web, marca la discrepancia.
    4. Code Agent sólo debe ejecutarse si el Decision Memo está aprobado.
    """
    
    return Team(
        # Pasamos la lista de objetos Agent, no las cadenas de texto.
        members=[lead_agent, web_agent, rag_agent, code_agent], 
        model=Gemini(id=settings.default_llm_pro, api_key=settings.google_api_key),
        user_id=user,
        session_id=session_id,
        instructions=team_instructions,
        markdown=True
    )
