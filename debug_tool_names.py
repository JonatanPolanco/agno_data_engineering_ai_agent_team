def debug_tool_names():
    """Verifica los nombres reales de las funciones de las herramientas."""
    from src.tools.vector_embedding import VertexSearchToolClient
    from src.config import settings
    
    tool = VertexSearchToolClient(
        project_id=settings.google_project_id,
        data_store_id=settings.data_store_id
    )
    
    print("🔧 Nombres de funciones disponibles:")
    for func_name, func in tool.get_tools().items():
        print(f"   • {func_name}: {func}")
    
    # Probemos con el agente
    from src.agents.definitions import create_rag_agent
    from agno.storage.sqlite import SqliteStorage
    
    rag_agent = create_rag_agent("test", "test", SqliteStorage(":memory:"))
    print(f"\n🔧 Herramientas del agente: {[t.name for t in rag_agent.tools]}")
    
    # Verificar las funciones de cada herramienta
    for tool in rag_agent.tools:
        print(f"\n🔧 Funciones de {tool.name}:")
        if hasattr(tool, 'get_tools'):
            for func_name, func in tool.get_tools().items():
                print(f"   • {func_name}")

if __name__ == "__main__":
    debug_tool_names()