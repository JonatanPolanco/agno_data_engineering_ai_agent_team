"""
Script para verificar y diagnosticar la memoria contextual.
"""
import sqlite3
from src.config import settings

def check_session_memory(user: str, session_id: str):
    """Verifica el estado de la memoria para una sesión."""
    table_name = f"{settings.db_table_prefix}_{user}_{session_id}"
    
    try:
        conn = sqlite3.connect(settings.db_file_path)
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Contar mensajes en la sesión
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            message_count = cursor.fetchone()[0]
            
            # Verificar estructura de la tabla
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"✅ Sesión encontrada: {table_name}")
            print(f"📊 Mensajes almacenados: {message_count}")
            print(f"🏗️ Estructura de la tabla:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
        else:
            print(f"❌ Tabla no encontrada: {table_name}")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando memoria: {e}")

if __name__ == "__main__":
    # Ejemplo de uso
    check_session_memory("jonatan", "jonatan_20250908_174627_bd6b2175")