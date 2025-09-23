import sqlite3
from rich.console import Console
from rich.table import Table
import logging
from datetime import datetime, timedelta

from src.config import settings

logger = logging.getLogger(__name__)

### CAMBIO: Toda la lógica ha sido reescrita para ser segura y operar en tablas fijas.

def get_db_connection():
    """Establece una conexión con la base de datos SQLite."""
    try:
        conn = sqlite3.connect(settings.db_file_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Error conectando a la base de datos en '{settings.db_file_path}': {e}", exc_info=True)
        return None

def clear_session_history(user: str, session_id: str) -> bool:
    """Limpia el historial de una sesión específica de forma segura."""
    tables_to_clear = ["agent_memory", "team_memory"]
    
    try:
        conn = get_db_connection()
        if not conn: 
            return False
        cursor = conn.cursor()
        
        for table in tables_to_clear:
            logger.info(f"Limpiando tabla '{table}' para sesión '{session_id}'...")
            cursor.execute(
                f"DELETE FROM {table} WHERE user_id = ? AND session_id = ?",
                (user, session_id)
            )
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.OperationalError:
        logger.warning("Una de las tablas de memoria no existe (esto puede ser normal).")
        return True
    except Exception as e:
        logger.error(f"Error clearing session history for '{session_id}': {e}", exc_info=True)
        return False


def list_user_sessions(user: str, console: Console, detailed: bool = False):
    """Lista las sesiones existentes para un usuario de forma segura."""
    try:
        conn = get_db_connection()
        if not conn:
            console.print(f"[red]No se pudo conectar a la base de datos.[/red]")
            return

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT session_id, COUNT(*) as message_count, MAX(created_at) as last_activity
            FROM team_memory
            WHERE user_id = ?
            GROUP BY session_id
            ORDER BY last_activity DESC
            """,
            (user,)
        )
        sessions = cursor.fetchall()
        conn.close()

        if sessions:
            table = Table(title=f"Sesiones para el usuario [cyan]{user}[/cyan]")
            table.add_column("Session ID", style="yellow")
            table.add_column("Mensajes", justify="right", style="magenta")
            table.add_column("Última Actividad", style="green")

            for session in sessions:
                if session["last_activity"]:
                    last_activity_str = datetime.fromtimestamp(session['last_activity']).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    last_activity_str = "N/A"
                table.add_row(session['session_id'], str(session['message_count']), last_activity_str)
            
            console.print(table)
        else:
            console.print(f"[yellow]No se encontraron sesiones para el usuario '{user}'.[/yellow]")

    except sqlite3.OperationalError:
        console.print(f"[yellow]No hay historial de sesiones todavía. Inicia un chat para crear uno.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error al listar sesiones: {e}[/red]")


def cleanup_old_sessions(user: str, older_than_days: int, console: Console) -> int:
    """Limpia sesiones antiguas para un usuario de forma segura."""
    console.print("[yellow]La función de limpieza automática aún no está implementada en el nuevo esquema seguro.[/yellow]")
    return 0
