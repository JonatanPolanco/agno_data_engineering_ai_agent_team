from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.storage.sqlite import SqliteStorage

# Importación corregida - ahora desde src.tools
from src.tools.vector_embedding import VertexSearchTool
from src.tools.prompts import WEB_SEARCH, RAG, CODE_STANDARDS_PROMPT
from src.config import settings
from datetime import datetime

def create_web_agent(user: str, session_id: str, storage: SqliteStorage) -> Agent:
    agent = Agent(
        name="Web Agent",
        role="Experto en documentación técnica actualizada sobre ingeniería de datos",
        model=Gemini(id=settings.default_llm_flash, api_key=settings.google_api_key),
        tools=[DuckDuckGoTools()],
        instructions=WEB_SEARCH + f"""
        
        CONTEXTO DE SESIÓN:
        - Usuario: {user}
        - Session ID: {session_id}
        - Fecha: {datetime.now().strftime('%Y-%m-%d')}
        
        REGLAS DE CONTEXTO:
        - Siempre considera el historial de la conversación antes de buscar.
        - Si el usuario referencia búsquedas anteriores, prioriza continuidad.
        - No repitas información ya proporcionada en conversaciones previas.
        """,
        show_tool_calls=True,
        markdown=True
    )
    # ✅ REMOVIDO: agent.storage = storage - Ahora usa el storage del team
    agent.user_id = user
    agent.session_id = session_id
    return agent

def create_rag_agent(user: str, session_id: str, storage: SqliteStorage) -> Agent:
    # Crear la herramienta con la configuración centralizada
    search_tool = VertexSearchTool(
        project_id=settings.google_project_id,
        data_store_id=settings.data_store_id
    )
    
    agent = Agent(
        name="RAG Agent",
        role="Experto en investigación y sintetización de información.",
        model=Gemini(id=settings.default_llm_pro, api_key=settings.google_api_key),
        tools=[search_tool],
        instructions=RAG + f"""
        
        CONTEXTO DE SESIÓN:
        - Usuario: {user}
        - Session ID: {session_id}
        
        REGLAS DE CONTEXTO:
        - Revisa el historial de conversación para entender el contexto completo.
        - Sintetiza información considerando preguntas y respuestas anteriores.
        - No repitas información ya proporcionada en esta conversación.
        
        Herramienta disponible: VertexSearchTool para consultar libros técnicos.
        Usa esta herramienta para búsquedas en la base de conocimiento vectorial.
        """,
        show_tool_calls=True,
        markdown=True
    )
    # ✅ REMOVIDO: agent.storage = storage - Ahora usa el storage del team
    agent.user_id = user
    agent.session_id = session_id
    return agent

def create_code_standards_agent(user: str, session_id: str, storage: SqliteStorage) -> Agent:
    agent = Agent(
        name="Code Standards Agent",
        role="Senior Code Reviewer y Generator especializado en estándares enterprise",
        model=Gemini(id=settings.default_llm_pro, api_key=settings.google_api_key),
        instructions=CODE_STANDARDS_PROMPT + f"""
        
        CONTEXTO DE SESIÓN:
        - Usuario: {user}  
        - Session ID: {session_id}
        
        REGLAS DE CONTEXTO:
        - Al generar código, considera el historial técnico de la conversación.
        - Mantén consistencia con referencias a código anterior si existe.
        - No repitas explicaciones ya dadas en respuestas previas.
        """,
        show_tool_calls=True,
        markdown=True
    )
    # ✅ REMOVIDO: agent.storage = storage - Ahora usa el storage del team
    agent.user_id = user
    agent.session_id = session_id
    return agent

def get_all_agents(user: str, session_id: str, storage: SqliteStorage):
    """Retorna todos los agentes configurados."""
    return (
        create_web_agent(user, session_id, storage),
        create_rag_agent(user, session_id, storage),
        create_code_standards_agent(user, session_id, storage)
    )