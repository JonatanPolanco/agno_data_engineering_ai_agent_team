from agno.team.team import Team
from agno.storage.sqlite import SqliteStorage
from agno.agent import Agent
from agno.models.google import Gemini
from src.agents.definitions import get_all_agents
from src.config import settings
from datetime import datetime
import uuid

def generate_session_id(user: str) -> str:
    """Genera un session_id único para el usuario."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    return f"{user}_{timestamp}_{short_uuid}"

def build_team(user: str, session_id: str) -> Team:
    """
    Crea un equipo coordinado de agentes con memoria contextual compartida.
    """
    # Storage compartido para TODO el equipo (contexto unificado)
    team_storage = SqliteStorage(
        table_name=f"{settings.db_table_prefix}_{user}_{session_id}",
        db_file=settings.db_file_path
    )
    
    # ✅ CORRECCIÓN: Pasar los parámetros requeridos
    web_agent, rag_agent, code_agent = get_all_agents(user, session_id, team_storage)
    
    # ✅ CONFIGURACIÓN CRÍTICA: Deshabilitar storage individual en agentes
    # para evitar el warning "You shouldn't use storage in multiple modes"
    for agent in [web_agent, rag_agent, code_agent]:
        agent.storage = None  # Los agentes usarán el storage del team
    
    return Team(
        members=[web_agent, rag_agent, code_agent],
        model=Gemini(
            id=settings.default_llm_pro,
            api_key=settings.google_api_key,
        ),
        storage=team_storage,  # Memoria compartida para TODO el equipo
        user_id=user,
        session_id=session_id,
        mode="coordinate",
        success_criteria="""
        Proveer una respuesta técnica clara, estructurada y accionable para ingenieros de datos senior.
        Si se requiere código, DEBE cumplir estándares enterprise de nivel senior.
        Mantener el contexto de la conversación a lo largo de múltiples interacciones.
        SIEMPRE revisar el historial completo antes de responder.
        """,
        instructions=f"""
        Eres el Orquestador de un equipo multi-agente de Ingeniería de Datos.
        
        CONTEXTO ACTUAL: Sesión {session_id} - Usuario: {user}
        FECHA: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        HISTORIAL DISPONIBLE: Tienes acceso al historial completo de esta conversación.
        
        REGLAS ESTRICTAS DE CONTEXTO:
        1. ✅ SIEMPRE revisa el historial completo de la conversación antes de responder
        2. ✅ Si el usuario hace referencia a algo anterior, busca en el contexto específico
        3. ✅ Mantén continuidad en referencias a trabajos previos
        4. ✅ No repitas información ya proporcionada
        5. ✅ Responde en el contexto de la conversación en curso
        
        REGLA PARA CÓDIGO:
        Si la consulta requiere generación de código, SIEMPRE involucra al Code Standards Agent.
        El código resultante debe ser production-ready y seguir estándares senior.
        
        FORMATO DE RESPUESTA:
        ## 📌 Resumen Ejecutivo Contextual
        - Puntos clave considerando el contexto histórico
        
        ## 📚 Conocimiento Interno (RAG)
        - Información del knowledge base (si aplica)
        
        ## 🌐 Documentación Externa (Web)  
        - Información de búsqueda web (si aplica)
        
        ## 💡 Recomendaciones Contextualizadas
        - Acciones considerando el historial completo
        - Referencias a conversaciones anteriores si son relevantes
        """,
        add_datetime_to_instructions=True,
        show_tool_calls=True,
        markdown=True,
        enable_agentic_context=True,  # ¡CRÍTICO: Habilita contexto agéntico!
        show_members_responses=False,
    )