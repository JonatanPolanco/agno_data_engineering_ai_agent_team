from typing import List, Dict, Any
from agno.knowledge.base import Knowledge
from src.tools.embedding_search import query_datastore
from src.config import settings

class VertexKnowledge(Knowledge):
    """KnowledgeBase para usar Vertex AI Search como fuente de verdad."""

    def __init__(self, project_id: str, data_store_id: str, location: str = settings.google_location):
        super().__init__(name="vertex_ai_knowledge")
        self.project_id = project_id
        self.data_store_id = data_store_id
        self.location = location

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Ejecuta búsqueda en Vertex AI Search y retorna documentos en formato estándar."""
        results = query_datastore(query, page_size=top_k)

        docs = []
        for r in results:
            if "error" in r:
                continue
            docs.append({
                "id": r.get("id", ""),
                "title": r.get("title", "Desconocido"),
                "author": r.get("author", "Desconocido"),
                "page": r.get("page", "?"),
                "excerpt": r.get("content", "")[:300],
                "score": r.get("score", 0.0),
                "uri": r.get("uri", ""),
            })
        return docs
