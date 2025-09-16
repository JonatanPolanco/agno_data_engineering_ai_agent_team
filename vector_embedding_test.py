from src.tools.embedding_search import VertexSearchToolClient
from src.config import settings

def test_vertex_corrected():
    """Prueba con la configuración corregida."""
    print("🔍 Probando Vertex AI Search con configuración corregida...")

    tool = VertexSearchToolClient(
        project_id=settings.google_project_id,
        data_store_id=settings.data_store_id,
        location="global",  # 👈 igual a lo que definiste en la instancia global
    )
    
    query = "ETL vs ELT"
    print(f"📋 Consulta: '{query}'")
    
    results = tool.run(query, page_size=3)
    
    if not results:
        print("❌ No se obtuvieron resultados")
        return False
        
    if "error" in str(results).lower():
        print(f"❌ Error: {results}")
        return False
    
    print(f"✅ Éxito! {len(results)} resultados reales:")
    
    for i, result in enumerate(results, 1):
        print(f"\n📄 Resultado {i}:")
        print(f"   ID: {result.get('id')}")
        print(f"   Título: {result.get('title')}")
        print(f"   Autor: {result.get('author')}")
        print(f"   Página: {result.get('page')}")
        print(f"   Score: {result.get('score')}")
        print(f"   Contenido: {result.get('content', '')[:100]}...")
    
    return True

if __name__ == "__main__":
    success = test_vertex_corrected()
    if success:
        print("\n🎉 ¡Vertex AI Search funciona correctamente!")
    else:
        print("\n❌ Hay problemas de configuración")
