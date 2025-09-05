""" 
Autor: Jonatan Polanco 
Fecha: 03 de Septiembre de 2025 
Proyecto: Equipo Multi-Agente de IA para Soporte Senior en Ingeniería de Datos 
------------------------------------------------------------------------ 

Este proyecto implementa un orquestador y un conjunto de agentes especializados 
(Arquitectura, ETL/ELT, Analítica & SQL, DataOps/QA, Estratégico y Search (web & documents)),
apoyados por modelos Gemini (2.5 Pro y 2.0 Flash) y RAG en Vertex AI.

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
con un “Knowledge Hub” compartido y devuelve respuestas consolidadas. 
"""

import os
import typer
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

from agno.tools.duckduckgo import DuckDuckGoTools
from agno.team.team import Team
from agno.agent import Agent
from agno.models.google import Gemini
from agno.storage.sqlite import SqliteStorage

from tools.vector_embedding import VertexSearchTool
from tools.prompts import WEB_SEARCH, RAG, LEAD_PROMPT

# --- Configuración ---
load_dotenv()
console = Console()
team_storage = SqliteStorage(table_name="data_engineering_team", db_file="tmp/agents.db")

PROJECT_ID = os.environ["GOOGLE_PROJECT_ID"]
DATA_STORE_ID = os.environ["DATA_STORE_ID"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

# --- Definición de Agentes ---
web_agent = Agent(
    name="Web Agent",
    role="Experto en buscar documentación técnica actualizada sobre ingeniería de datos",
    model=Gemini(
        id="gemini-2.5-pro",
        api_key=GOOGLE_API_KEY,
    ),
    tools=[DuckDuckGoTools()],
    instructions=WEB_SEARCH,
    show_tool_calls=True,
    markdown=True
)

rag_agent = Agent(
    name="RAG Agent",
    role="Experto en buscar en la base de conocimiento interna (libros técnicos de ingeniería de datos y programación).",
    model=Gemini(
        id="gemini-2.0-flash",
        api_key=GOOGLE_API_KEY,
    ),
    tools=[VertexSearchTool(project_id=PROJECT_ID, data_store_id=DATA_STORE_ID)],
    instructions=RAG,
    show_tool_calls=True,
    markdown=True
)

# --- Definición del equipo (orquestador) ---
def build_team(user: str, session_id: str) -> Team:
    """
    Crea un equipo coordinado de agentes para ingeniería de datos.
    """
    return Team(
        members=[web_agent, rag_agent],
        model=Gemini(
            id="gemini-2.5-pro",
            api_key=GOOGLE_API_KEY,
        ),
        storage=team_storage,
        user_id=user,
        session_id=session_id,
        mode="coordinate",
        success_criteria="Proveer una respuesta técnica clara, estructurada y accionable para ingenieros de datos senior.",
        instructions=LEAD_PROMPT,
        add_datetime_to_instructions=True,
        show_tool_calls=True,
        markdown=True,
        enable_agentic_context=True,
        show_members_responses=False,
    )

# --- CLI ---
app = typer.Typer(help="CLI para interactuar con el equipo de agentes de IA para Ingeniería de Datos.")

@app.command()
def chat(user: str = typer.Option("user", help="ID de usuario")):
    """Chat interactivo con el equipo orquestado (multi-agente)."""
    session_id = None
    team = build_team(user, session_id)

    console.print(Panel(
        "[bold green]Chat iniciado con el Equipo Multi-Agente[/bold green]\n"
        "El orquestador decidirá automáticamente cómo combinar RAG y Web.\n"
        "Escribe '[cyan]exit[/cyan]' para salir.",
        title="Equipo de Ingeniería de Datos",
        border_style="blue"
    ))

    while True:
        query = console.input("[bold]Tu consulta > [/bold] ")
        if query.lower() in ["exit", "quit"]:
            break

        with console.status("[cyan]Orquestando agentes...[/cyan]", spinner="dots"):
            response = team.run(query)

        console.print(Panel(
            getattr(response, "content", str(response)),
            title="[bold magenta]Respuesta del Equipo[/bold magenta]",
            border_style="magenta"
        ))

if __name__ == "__main__":
    app()
