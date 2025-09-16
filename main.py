""" 
Autor: Jonatan Polanco
Fecha: Septiembre de 2025 
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
import logging
import sys
from datetime import datetime
import uuid

# Importaciones modulares
from src.core.team_builder import build_team, generate_session_id
from src.storage.db_utils import list_user_sessions, clear_session_history

console = Console()

# Configurar logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# CLI
app = typer.Typer(help="CLI para equipo de agentes de IA para Ingeniería de Datos.")

def print_welcome_banner(session_id: str, user: str, is_new_session: bool = True):
    """Muestra un banner de bienvenida con información de la sesión."""
    session_type = "Nueva sesión" if is_new_session else "Sesión existente"
    
    console.print(Panel(
        f"[bold green]🚀 Equipo Multi-Agente de Ingeniería de Datos[/bold green]\n\n"
        f"👤 [bold]Usuario:[/bold] [cyan]{user}[/cyan]\n"
        f"📋 [bold]Session ID:[/bold] [yellow]{session_id}[/yellow]\n"
        f"🔄 [bold]Tipo:[/bold] [green]{session_type}[/green]\n\n"
        f"🎯 [bold]Agentes disponibles:[/bold]\n"
        f"  • 🤖 RAG Agent (Conocimiento interno)\n"
        f"  • 🌐 Web Agent (Búsqueda en documentación)\n"
        f"  • 💻 Code Standards Agent (Generación de código)\n\n"
        f"💡 [bold]Comandos especiales:[/bold]\n"
        f"  • [cyan]exit[/cyan] - Salir del chat\n"
        f"  • [cyan]clear[/cyan] - Limpiar contexto de esta sesión\n"
        f"  • [cyan]new[/cyan] - Crear nueva sesión\n",
        title="Sistema de Soporte Senior para Ingeniería de Datos",
        border_style="blue",
        padding=(1, 2)
    ))

@app.command()
def chat(
    user: str = typer.Option("default_user", help="ID de usuario"),
    session: str = typer.Option(None, help="Session ID específica (opcional)"),
    clear_history: bool = typer.Option(False, help="Limpiar historial de sesión existente")
):
    """Chat interactivo con el equipo orquestado (multi-agente)."""
    
    is_new_session = session is None
    session_id = session if session else generate_session_id(user)
    
    # Limpiar historial si se solicita
    if clear_history and session:
        if clear_session_history(user, session_id):
            console.print(f"[yellow]🗑️ Historial de sesión {session_id} limpiado[/yellow]")
        else:
            console.print(f"[red]❌ Error limpiando historial de sesión {session_id}[/red]")
    
    print_welcome_banner(session_id, user, is_new_session)

    try:
        team = build_team(user, session_id)
        logger.info(f"Team initialized for user '{user}' with session '{session_id}'")
        console.print(f"[green]✅[/green] Equipo inicializado con memoria contextual")
        
    except Exception as e:
        logger.error(f"Error initializing team: {e}", exc_info=True)
        console.print(Panel(
            f"[red]❌ Error al inicializar el equipo:[/red] {e}\n\n"
            f"💡 [bold]Posibles soluciones:[/bold]\n"
            f"• Verifica que las variables de entorno estén configuradas\n"
            f"• Asegúrate de que las dependencias estén instaladas\n"
            f"• Revisa los permisos de Google Cloud",
            title="Error de Inicialización",
            border_style="red"
        ))
        raise typer.Exit(code=1)

    conversation_count = 0
    
    while True:
        try:
            prompt = f"[bold]📝 Consulta ({conversation_count + 1}) > [/bold] "
            query = console.input(prompt)
            
            # Comandos especiales
            if query.lower() in ["exit", "quit", "salir"]:
                console.print(f"[blue]💾 Sesión guardada como: {session_id}[/blue]")
                logger.info(f"Session {session_id} ended after {conversation_count} conversations")
                break
                
            elif query.lower() in ["clear", "limpiar"]:
                conversation_count = 0
                console.print("[yellow]🔄 Contexto reiniciado para esta sesión[/yellow]")
                continue
                
            elif query.lower() in ["new", "nuevo"]:
                new_session_id = generate_session_id(user)
                console.print(f"[green]🆕 Nueva sesión creada: {new_session_id}[/green]")
                console.print("[yellow]Reinicia el chat con: --session {new_session_id}[/yellow]")
                break
                
            elif not query.strip():
                console.print("[yellow]⚠️ La consulta no puede estar vacía[/yellow]")
                continue

            # Procesar consulta
            with console.status(
                "[cyan]🤖 Orquestando agentes con contexto...[/cyan]", 
                spinner="dots"
            ):
                response = team.run(query)
                conversation_count += 1
                logger.info(f"Processed query #{conversation_count} for session {session_id}")

            # Mostrar respuesta
            response_content = getattr(response, "content", str(response))
            
            console.print(Panel(
                response_content,
                title=f"[bold magenta]📊 Respuesta del Equipo ({conversation_count})[/bold magenta]",
                border_style="magenta",
                padding=(1, 2)
            ))
            
            # Sugerencia después de varias consultas
            if conversation_count % 3 == 0:
                console.print(
                    "[dim]💡 Tip: Usa 'clear' para reiniciar el contexto o 'exit' para salir[/dim]"
                )
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⏹️ Interrupción recibida. Guardando contexto...[/yellow]")
            logger.info(f"Session {session_id} interrupted by user")
            break
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            console.print(Panel(
                f"[red]❌ Error al procesar consulta:[/red] {e}\n\n"
                f"💡 [bold]Sugerencias:[/bold]\n"
                f"• Revisa tu conexión a internet\n"
                f"• Verifica los permisos de Google Cloud\n"
                f"• Intenta reformular tu pregunta",
                title="Error de Procesamiento",
                border_style="red"
            ))

@app.command()
def list_sessions(
    user: str = typer.Option("default_user", help="ID de usuario"),
    detailed: bool = typer.Option(False, help="Mostrar información detallada")
):
    """Lista las sesiones existentes para un usuario."""
    console.print(Panel(
        f"[bold]📋 Sesiones para usuario:[/bold] [cyan]{user}[/cyan]",
        border_style="blue"
    ))
    list_user_sessions(user, console, detailed)

@app.command()
def cleanup_sessions(
    user: str = typer.Option("default_user", help="ID de usuario"),
    older_than_days: int = typer.Option(30, help="Eliminar sesiones más antiguas que X días")
):
    """Limpia sesiones antiguas para un usuario."""
    from src.storage.db_utils import cleanup_old_sessions
    
    console.print(Panel(
        f"[bold]🧹 Limpiando sesiones antiguas para:[/bold] [cyan]{user}[/cyan]\n"
        f"[bold]📅 Más antiguas que:[/bold] [yellow]{older_than_days}[/yellow] días",
        border_style="yellow"
    ))
    
    deleted_count = cleanup_old_sessions(user, older_than_days, console)
    
    if deleted_count > 0:
        console.print(f"[green]✅ {deleted_count} sesiones eliminadas[/green]")
    else:
        console.print("[blue]💡 No se encontraron sesiones para eliminar[/blue]")

@app.command()
def test_connection():
    """Prueba la conexión con los servicios de Google Cloud."""
    from src.tools.embedding_search import VertexSearchToolClient
    from src.config import settings
    
    console.print(Panel(
        "[bold]🔧 Probando conexiones...[/bold]",
        border_style="blue"
    ))
    
    try:
        # Test configuración
        console.print(f"[bold]⚙️ Configuración:[/bold]")
        console.print(f"  • Project ID: [cyan]{settings.google_project_id}[/cyan]")
        console.print(f"  • Data Store ID: [cyan]{settings.data_store_id}[/cyan]")
        console.print(f"  • DB Path: [cyan]{settings.db_file_path}[/cyan]")
        
        # Test Vector Search
        console.print(f"\n[bold]🔍 Probando Vertex AI Search...[/bold]")
        tool = VertexSearchToolClient(
            project_id=settings.google_project_id,
            data_store_id=settings.data_store_id
        )
        
        test_query = "data engineering best practices"
        result = tool.search(test_query, page_size=1)
        
        if "error" in result.lower():
            console.print(f"[red]❌ Error en Vertex AI: {result}[/red]")
        else:
            console.print(f"[green]✅ Vertex AI Search conectado correctamente[/green]")
            console.print(f"[dim]Muestra: {result[:100]}...[/dim]")
        
        console.print(f"\n[green]🎉 Todas las conexiones funcionan correctamente![/green]")
        
    except Exception as e:
        console.print(Panel(
            f"[red]❌ Error de conexión:[/red] {e}\n\n"
            f"💡 [bold]Verifica:[/bold]\n"
            f"• Variables de entorno configuradas\n"
            f"• Permisos de Google Cloud\n"
            f"• Credenciales de autenticación",
            title="Error de Conexión",
            border_style="red"
        ))
        raise typer.Exit(code=1)

@app.command()
def version():
    """Muestra la versión e información del sistema."""
    import agno
    import google.cloud.discoveryengine
    
    console.print(Panel(
        f"[bold]📦 Sistema Multi-Agente para Ingeniería de Datos[/bold]\n\n"
        f"🔢 [bold]Versión:[/bold] [cyan]1.0.0[/cyan]\n"
        f"🐍 [bold]Python:[/bold] [yellow]{sys.version}[/yellow]\n"
        f"🤖 [bold]Agno:[/bold] [green]{agno.__version__}[/green]\n"
        f"☁️ [bold]Google Cloud:[/bold] [blue]{google.cloud.discoveryengine.__version__}[/blue]\n\n"
        f"📚 [bold]Características:[/bold]\n"
        f"  • 🎯 Orquestación multi-agente\n"
        f"  • 📊 RAG con Vertex AI Search\n"
        f"  • 🌐 Búsqueda web en tiempo real\n"
        f"  • 💻 Generación de código enterprise\n"
        f"  • 💾 Persistencia con SQLite",
        title="Información del Sistema",
        border_style="green"
    ))

def main():
    """Función principal con manejo de errores global."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 ¡Hasta pronto![/yellow]")
    except Exception as e:
        logger.critical(f"Unhandled error in main: {e}", exc_info=True)
        console.print(Panel(
            f"[red]💥 Error crítico:[/red] {e}\n\n"
            f"📝 [bold]Por favor reporta este error:[/bold]\n"
            f"• Session: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"• Error: {type(e).__name__}",
            title="Error Crítico",
            border_style="red"
        ))
        raise typer.Exit(code=1)

if __name__ == "__main__":
    main()