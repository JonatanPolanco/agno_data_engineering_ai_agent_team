"""
Módulo para consultar un Data Store de Vertex AI Search (Discovery Engine)
que contiene embeddings de libros de ingeniería de datos.

Autor: Jonatan Polanco
Fecha: Septiembre 2025
"""

import os
from google.cloud import discoveryengine_v1 as discovery

project_id= os.environ.get("GOOGLE_PROJECT_ID")
data_store_id= os.environ.get("DATA_STORE_ID")


class VertexSearchTool:
    """Wrapper para hacer consultas al Data Store de Vertex AI Search."""

    def __init__(self, project_id: str, data_store_id: str, location: str = "global"):
        self.client = discovery.SearchServiceClient()
        self.serving_config = (
            f"projects/{project_id}/locations/{location}/collections/default_collection/"
            f"dataStores/{data_store_id}/servingConfigs/default_search"
        )

    def search(self, query: str, page_size: int = 3) -> str:
        """Ejecuta búsqueda semántica en el Data Store y devuelve texto concatenado."""
        request = discovery.SearchRequest(
            serving_config=self.serving_config,
            query=query,
            page_size=page_size,
        )
        response = self.client.search(request=request)

        results = []
        for result in response:
            # derived_struct_data es un MapComposite, lo pasamos a dict
            struct_data = dict(result.document.derived_struct_data)
            text = struct_data.get("content") or str(struct_data)
            results.append(f"- {text[:500]}...")  # truncamos para no pasarnos de tokens

        return "\n".join(results) if results else "⚠️ No encontré resultados en el Data Store."


if __name__ == "__main__":
    # 🔹 Test rápido en consola
    from dotenv import load_dotenv

    load_dotenv()
    PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
    DATA_STORE_ID = "data-engineering-books-vector-embedding_1757108351078"

    tool = VertexSearchTool(project_id=PROJECT_ID, data_store_id=DATA_STORE_ID)

    query = "explica el concepto de data pipeline"
    print(f"🔍 Consulta: {query}\n")
    print(tool.search(query))
