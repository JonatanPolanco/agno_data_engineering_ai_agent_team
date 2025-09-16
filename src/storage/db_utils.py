import sqlite3
from rich.console import Console
import logging

# Configurar logging
logger = logging.getLogger(__name__)


def create_user_session_table(user: str, session_id: str):
    """Crea la tabla de sesión para un usuario si no existe."""
    from src.config import settings

    table_name = f"{settings.db_table_prefix}_{user}_{session_id}"

    try:
        conn = sqlite3.connect(settings.db_file_path)
        cursor = conn.cursor()

        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            session_id TEXT PRIMARY KEY,
            user_id TEXT,
            memory TEXT,
            session_data TEXT,
            extra_data TEXT,
            created_at INTEGER,
            updated_at INTEGER,
            team_session_id TEXT,
            team_id TEXT,
            team_data TEXT
        )
        """)

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Error creating session table '{table_name}': {e}")
        return False


def clear_session_history(user: str, session_id: str):
    """Limpia el historial de una sesión específica."""
    from src.config import settings

    table_name = f"{settings.db_table_prefix}_{user}_{session_id}"
    try:
        conn = sqlite3.connect(settings.db_file_path)
        cursor = conn.cursor()

        cursor.execute(f"DELETE FROM {table_name} WHERE 1=1")

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Error clearing session history: {e}")
        return False


def list_user_sessions(user: str, console: Console):
    """Lista las sesiones existentes para un usuario."""
    from src.config import settings

    try:
        conn = sqlite3.connect(settings.db_file_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
            (f"{settings.db_table_prefix}_{user}_%",)
        )
        sessions = cursor.fetchall()

        if sessions:
            console.print(f"[green]Sesiones encontradas para usuario '{user}':[/green]")
            for session in sessions:
                session_name = session[0].replace(f"{settings.db_table_prefix}_{user}_", "")
                console.print(f"  • {session_name}")
        else:
            console.print(f"[yellow]No se encontraron sesiones para usuario '{user}'[/yellow]")

        conn.close()

    except Exception as e:
        console.print(f"[red]Error al listar sesiones: {e}[/red]")


def check_session_table_columns(user: str, session_id: str, console: Console):
    """Muestra las columnas de la tabla de sesión y verifica si coinciden con la estructura esperada."""
    from src.config import settings

    table_name = f"{settings.db_table_prefix}_{user}_{session_id}"
    try:
        conn = sqlite3.connect(settings.db_file_path)
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()

        if columns:
            console.print(f"[green]Columnas de {table_name}:[/green]")
            for col in columns:
                console.print(f"  • {col[1]} ({col[2]})")
        else:
            console.print(f"[yellow]La tabla {table_name} no existe o está vacía[/yellow]")

        conn.close()
        return columns

    except Exception as e:
        console.print(f"[red]Error al consultar columnas de la tabla: {e}[/red]")
        return []
