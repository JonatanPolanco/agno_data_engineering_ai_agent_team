""" 
Autor: Jonatan Polanco
Fecha: 03 de Septiembre de 2025 
Proyecto: Equipo Multi-Agente de IA para Soporte Senior en Ingeniería de Datos 
------------------------------------------------------------------------ 

Este proyecto implementa un orquestador y un conjunto de agentes especializados 
(Arquitectura, ETL/ELT, Analítica & SQL, DataOps/QA, Estratégico y Search (web & documents)),
apoyados por modelos Gemini (2.5 Pro y 2.5 Flash) y RAG en Vertex AI.

Regla operativa clave: Antes de generar código (HOW) cada propuesta debe producir un
Decision Memo respondiendo: WHAT, WHY, WHO, WHERE, WHEN. Sólo tras validar
impacto/risgo (Estratégico + DataOps/QA) se genera e implementa código.

Objetivo: Dar soporte senior a ingenieros de analítica y de datos mediante: 
- Recomendaciones técnicas y de arquitectura. 
- Generación y validación de código (Gemini 2.5 pro). 
- Auditoría de estándares internos y calidad de datos. 
- Evaluación de riesgos e impacto en negocio. 
- Acceso a conocimiento fresco vía web search.

El orquestador enruta cada tarea al agente adecuado, combina RAG especializado (libros y documentación oficial) 
con un "Knowledge Hub" compartido y devuelve respuestas consolidadas. 
"""

import os
import typer
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv
from datetime import datetime
import uuid
from datetime import datetime
import uuid

from agno.tools.duckduckgo import DuckDuckGoTools
from agno.team.team import Team
from agno.agent import Agent
from agno.models.google import Gemini
from agno.storage.sqlite import SqliteStorage

from tools.vector_embedding import VertexSearchTool
from tools.prompts import WEB_SEARCH, RAG, LEAD_PROMPT, CODE_STANDARDS_PROMPT

# --- Configuración ---
load_dotenv()
console = Console()

PROJECT_ID = os.environ["GOOGLE_PROJECT_ID"]
DATA_STORE_ID = os.environ["DATA_STORE_ID"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

# --- Definición de Agentes ---
web_agent = Agent(
    name="Web Agent",
    role="Experto en documentación técnica actualizada sobre ingeniería de datos",
    model=Gemini(
        id="gemini-2.5-flash",
        api_key=GOOGLE_API_KEY,
    ),
    tools=[DuckDuckGoTools()],
    instructions=WEB_SEARCH,
    show_tool_calls=True,
    markdown=True
)

rag_agent = Agent(
    name="RAG Agent",
    role="Experto en investigación y sintetización de información.",
    model=Gemini(
        id="gemini-2.5-pro",
        api_key=GOOGLE_API_KEY,  # Agregué la API key que faltaba
    ),
    tools=[VertexSearchTool(project_id=PROJECT_ID, data_store_id=DATA_STORE_ID)],
    instructions=RAG,
    show_tool_calls=True,
    markdown=True
)

code_standards_agent = Agent(
    name="Code Standards Agent",
    role="Senior Code Reviewer y Generator especializado en estándares enterprise",
    model=Gemini(
        id="gemini-2.5-pro",
        api_key=GOOGLE_API_KEY,
    ),
    instructions=CODE_STANDARDS_PROMPT,
    show_tool_calls=True,
    markdown=True
)

# --- Definición del equipo (orquestador) ---
def build_team(user: str, session_id: str) -> Team:
    """
    Crea un equipo coordinado de agentes para ingeniería de datos.
    """
    # Crear storage con session_id único para mantener contexto
    team_storage = SqliteStorage(
        table_name=f"team_{user}_{session_id}", 
        db_file="tmp/agents.db"
    )
    
    return Team(
        members=[web_agent, rag_agent, code_standards_agent],
        model=Gemini(
            id="gemini-2.5-pro",
            api_key=GOOGLE_API_KEY,
        ),
        storage=team_storage,
        user_id=user,
        session_id=session_id,  # Ahora session_id persistirá durante toda la sesión
        mode="coordinate",
        success_criteria="""
        Proveer una respuesta técnica clara, estructurada y accionable para ingenieros de datos senior.
        Si se requiere código, DEBE cumplir estándares enterprise de nivel senior.
        """,
        instructions=LEAD_PROMPT + """
        
        REGLA ADICIONAL PARA CÓDIGO:
        Si la consulta requiere generación de código, SIEMPRE involucra al Code Standards Agent.
        El código resultante debe ser production-ready y seguir estándares senior.
        
        INSTRUCCIÓN DE CONTEXTO:
        Siempre revisa el historial de la conversación antes de responder.
        Si el usuario hace referencia a algo anterior ("el código", "lo que acabas de decir", etc.),
        busca en el contexto previo para entender a qué se refiere específicamente.
        Mantén continuidad en la conversación y referencias a trabajos previos.
        """,
        add_datetime_to_instructions=True,
        show_tool_calls=True,
        markdown=True,
        enable_agentic_context=True,
        show_members_responses=False,
    )

def generate_session_id(user: str) -> str:
    """Genera un session_id único para el usuario."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    short_uuid = str(uuid.uuid4())[:8]
    return f"{user}_{timestamp}_{short_uuid}"

# --- CLI ---
app = typer.Typer(help="CLI para interactuar con el equipo de agentes de IA para Ingeniería de Datos.")

@app.command()
def chat(
    user: str = typer.Option("user", help="ID de usuario"),
    session: str = typer.Option(None, help="Session ID específica (opcional)")
):
    """Chat interactivo con el equipo orquestado (multi-agente)."""
    
    # Generar o usar session_id específica
    if session:
        session_id = f"{user}_{session}"
    else:
        session_id = generate_session_id(user)
    
    console.print(Panel(
        f"[bold green]Chat iniciado con el Equipo Multi-Agente[/bold green]\n"
        f"Session ID: [cyan]{session_id}[/cyan]\n"
        f"Usuario: [yellow]{user}[/yellow]\n\n"
        "El orquestador decidirá automáticamente cómo combinar Coding, RAG y Web search.\n"
        "Escribe '[cyan]exit[/cyan]' para salir.",
        title="Equipo de Ingeniería de Datos",
        border_style="blue"
    ))

    try:
        team = build_team(user, session_id)
        console.print(f"[green]✓[/green] Equipo inicializado correctamente")
    except Exception as e:
        console.print(f"[red]✗[/red] Error al inicializar equipo: {e}")
        raise typer.Exit(code=1)

    conversation_count = 0
    
    while True:
        query = console.input(f"[bold]Tu consulta ({conversation_count + 1}) > [/bold] ")
        if query.lower() in ["exit", "quit"]:
            console.print(f"[blue]Sesión guardada como: {session_id}[/blue]")
            break

        try:
            with console.status("[cyan]Orquestando agentes...[/cyan]", spinner="dots"):
                response = team.run(query)
                conversation_count += 1

            console.print(Panel(
                getattr(response, "content", str(response)),
                title=f"[bold magenta]Respuesta del Equipo ({conversation_count})[/bold magenta]",
                border_style="magenta"
            ))
            
        except Exception as e:
            console.print(f"[red]Error al procesar consulta: {e}[/red]")
            console.print("Intenta reformular tu pregunta.")

@app.command()
def list_sessions(user: str = typer.Option("user", help="ID de usuario")):
    """Lista las sesiones existentes para un usuario."""
    import sqlite3
    
    try:
        conn = sqlite3.connect("tmp/agents.db")
        cursor = conn.cursor()
        
        # Buscar tablas que contengan el user ID
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (f"team_{user}_%",))
        sessions = cursor.fetchall()
        
        if sessions:
            console.print(f"[green]Sesiones encontradas para usuario '{user}':[/green]")
            for session in sessions:
                session_name = session[0].replace(f"team_{user}_", "")
                console.print(f"  • {session_name}")
        else:
            console.print(f"[yellow]No se encontraron sesiones para usuario '{user}'[/yellow]")
            
        conn.close()
        
    except Exception as e:
        console.print(f"[red]Error al listar sesiones: {e}[/red]")

if __name__ == "__main__":
    app()