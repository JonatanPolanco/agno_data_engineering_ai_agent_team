"""
Debug avanzado de la memoria compartida.
"""
import sqlite3
from src.config import settings

def debug_memory(user: str, session_id: str):
    """Debug completo de la memoria."""
    table_name = f"{settings.db_table_prefix}_{user}_{session_id}"
    
    try:
        conn = sqlite3.connect(settings.db_file_path)
        cursor = conn.cursor()
        
        print(f"Debug de memoria: {table_name}")
        print("=" * 60)
        
        # 1. Verificar tabla
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        table_exists = cursor.fetchone()
        print(f"Tabla existe: {bool(table_exists)}")
        
        if table_exists:
            # 2. Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"Total de mensajes: {count}")
            
            # 3. Mostrar últimos 5 mensajes
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY created_at DESC LIMIT 5")
            recent_messages = cursor.fetchall()
            
            print(f"\nÚltimos 5 mensajes:")
            for i, msg in enumerate(recent_messages):
                print(f"  {i+1}. {msg[2][:100]}...")  # memory column
                
            # 4. Verificar agentes con acceso
            cursor.execute(f"SELECT DISTINCT agent_id FROM {table_name} WHERE agent_id IS NOT NULL")
            agents = cursor.fetchall()
            print(f"\nAgentes con acceso: {[a[0] for a in agents] if agents else 'None'}")
            
        conn.close()
        
    except Exception as e:
        print(f"Error en debug: {e}")

if __name__ == "__main__":
    debug_memory("jonatan", "jonatan_20250908_174627_bd6b2175")