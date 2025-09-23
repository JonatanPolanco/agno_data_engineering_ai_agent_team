# main.py

import typer
from rich.console import Console
from rich.panel import Panel
import logging
import sys

# --- Importaciones modulares limpias y correctas ---
# La lógica del equipo (creación de agentes, etc.) está en team_builder
from src.core.team_builder import build_team, generate_session_id 
# Ya no necesitamos una capa de DB utils si la memoria la maneja Agno,
# pero podrías mantenerla si tienes otras utilidades.
# from src.storage.db_utils import ... 

# Ya no necesitamos la lógica de la KB aquí, solo el orquestador
# (A menos que quieras un comando build-kb que llame a una función en otro módulo)

console = Console()

# --- Configuración de Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# --- CLI App ---
app = typer.Typer(help="CLI para el equipo de agentes de IA para Ingeniería de Datos.")

# --- Funciones de UI ---
def print_welcome_banner(session_id: str, user: str, is_new_session: bool = True):
    """Muestra un banner de bienvenida."""
    # (Tu función de banner es excelente, la mantenemos igual)
    session_type = "Nueva sesión" if is_new_session else "Sesión existente"
    console.print(Panel(
        f"[bold green]🚀 Equipo Multi-Agente de Ingeniería de Datos[/bold green]\n\n"
        f"👤 [bold]Usuario:[/bold] [cyan]{user}[/cyan]\n"
        f"📋 [bold]Session ID:[/bold] [yellow]{session_id}[/yellow]\n"
        f"🔄 [bold]Tipo:[/bold] [green]{session_type}[/green]\n\n"
        f"🎯 [bold]Conectado a:[/bold] Vertex AI Search Data Store\n\n"
        f"💡 [bold]Comandos:[/bold] 'exit', 'new'",
        title="Sistema de Soporte Senior para Ingeniería de Datos",
        border_style="blue",
        padding=(1, 2)
    ))

# --- Comandos de la CLI ---

@app.command()
def chat(
    user: str = typer.Option("default_user", help="ID de usuario"),
    session: str = typer.Option(None, help="ID de una sesión existente para continuarla"),
):
    """Chat interactivo con el equipo de agentes de IA."""
    
    is_new_session = session is None
    session_id = session if session else generate_session_id(user)
    
    print_welcome_banner(session_id, user, is_new_session)

    try:
        # La lógica de construcción del equipo está ahora encapsulada
        team = build_team(user, session_id)
        if not team:
            raise Exception("No se pudo construir el equipo de agentes. Revisa los logs.")

        logger.info(f"Equipo inicializado para el usuario '{user}' con sesión '{session_id}'.")

    except Exception as e:
        logger.error(f"Error fatal al inicializar el equipo: {str(e)}", exc_info=True)
        console.print(Panel(
            f"[red]❌ Error al inicializar el equipo:[/red] {str(e)}\n\n"
            f"💡 [bold]Asegúrate de que:[/bold]\n"
            f"• Tus credenciales de Google Cloud están configuradas (`gcloud auth application-default login`).\n"
            f"• Las variables de entorno en `.env` (PROJECT_ID, etc.) son correctas.",
            title="Error de Inicialización", border_style="red"
        ))
        raise typer.Exit(code=1)

    conversation_count = 0
    while True:
        try:
            query = console.input(f"[bold]📝 Consulta ({conversation_count + 1}) > [/bold] ")
            
            if query.lower() in ["exit", "quit", "salir"]:
                console.print(f"[blue]👋 Adiós. Sesión '{session_id}' finalizada.[/blue]")
                break
                
            elif query.lower() in ["new", "nuevo"]:
                new_session_id = generate_session_id(user)
                console.print(f"[green]🆕 Nueva sesión creada: {new_session_id}[/green]")
                console.print(f"[yellow]Reinicia el chat con: python main.py chat --user {user} --session {new_session_id}[/yellow]")
                break
                
            elif not query.strip():
                continue

            with console.status("[cyan]🤖 Orquestando agentes...", spinner="dots"):
                # La interacción principal es simple y limpia
                response = team.run(query)
                conversation_count += 1
            
            response_content = getattr(response, "content", str(response))
            
            console.print(Panel(
                response_content,
                title=f"[bold magenta]📊 Respuesta del Equipo ({conversation_count})[/bold magenta]",
                border_style="magenta"
            ))
            
        except KeyboardInterrupt:
            console.print(f"\n[yellow]⏹️ Interrupción recibida. Sesión '{session_id}' finalizada.[/yellow]")
            break
            
        except Exception as e:
            logger.error(f"Error procesando la consulta: {str(e)}", exc_info=True)
            console.print(Panel(f"[red]❌ Error al procesar consulta:[/red] {str(e)}", border_style="red"))


if __name__ == "__main__":
    app()
