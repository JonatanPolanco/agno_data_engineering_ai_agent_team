import sqlite3
from rich.console import Console
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# src/storage/db_utils.py
def clear_session_history(user: str, session_id: str):
    """Limpia el historial de una sesión específica."""
    from src.config import settings
    
    try:
        conn = sqlite3.connect(settings.db_file_path)
        cursor = conn.cursor()
        
        table_name = f"{settings.db_table_prefix}_{user}_{session_id}"
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