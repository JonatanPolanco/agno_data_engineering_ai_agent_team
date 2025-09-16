import requests
import json
import subprocess
import logging
from typing import Any, Dict, List
from src.config import settings
from agno.tools import Toolkit

logger = logging.getLogger(__name__)

# === HELPERS ===

def get_gcp_token() -> str:
    """Obtiene el token de acceso de GCP usando gcloud CLI."""
    try:
        token = subprocess.getoutput("gcloud auth print-access-token")
        if token.startswith("ERROR") or not token:
            raise Exception("No se pudo obtener token de GCP")
        return token
    except Exception as e:
        logger.error(f"Error obteniendo token GCP: {e}")
        raise

def parse_doc_id(doc_id: str):
    """Parsea el id para obtener título y página."""
    # Ejemplo: Book-Databricks-Certified-Data-Engineer-Associate-Study-Guide-p10
    parts = doc_id.split("-p")
    title = parts[0] if parts else doc_id
    page = parts[1] if len(parts) > 1 else "?"
    return title, page

def query_datastore(query: str, page_size: int = 1329):
    """Consulta a Vertex AI DataStore y devuelve fragmentos relevantes con metadatos."""
    try:
        token = get_gcp_token()

        url = (
            f"https://discoveryengine.googleapis.com/v1alpha/projects/"
            f"{settings.google_project_id}/locations/{settings.google_location}"
            f"/collections/default_collection/engines/{settings.data_store_id}"
            f"/servingConfigs/default_search:search"
        )

        payload = {
            "query": query,
            "pageSize": page_size,
            "queryExpansionSpec": {"condition": "AUTO"},
            "spellCorrectionSpec": {"mode": "AUTO"},
            "languageCode": "en-US",
            "contentSearchSpec": {
                "extractiveContentSpec": {"maxExtractiveAnswerCount": 2}
            },
            "userInfo": {"timeZone": "America/Bogota"},
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code != 200:
            raise Exception(f"Error API: {response.status_code} - {response.text}")
            
        results = response.json().get("results", [])

        docs = []
        for doc in results:
            doc_id = doc.get("document", {}).get("id", "unknown")
            title, page = parse_doc_id(doc_id)

            snippet = (
                doc.get("document", {})
                .get("derivedStructData", {})
                .get("extractiveContent", "")
            )
            if not snippet:
                snippet = doc.get("document", {}).get("content", "")

            docs.append({
                "id": doc_id,
                "title": title,
                "page": page,
                "content": snippet,
                "author": "Desconocido", 
                "uri": "",
                "score": 0.0
            })
        
        logger.info(f"Búsqueda exitosa: '{query}' - {len(docs)} resultados")
        return docs
        
    except Exception as e:
        logger.error(f"Error en query_datastore: {e}")
        return [{"error": str(e), "query": query}]

# === CLASE PARA MANTENER COMPATIBILIDAD ===

class VertexSearchToolClient(Toolkit):
    """Cliente mejorado para Vertex AI Search usando HTTP requests directos."""

    def __init__(
        self,
        project_id: str,
        data_store_id: str,
        location: str = settings.google_location
    ):
        super().__init__(name="vertex_search")
        self.project_id = project_id
        self.data_store_id = data_store_id
        self.location = location

    def search_structured(self, query: str, page_size: int = 10) -> List[Dict[str, Any]]:
        """Búsqueda estructurada usando la nueva implementación."""
        return query_datastore(query, page_size)

    def run(self, query: str, page_size: int = 10) -> List[Dict[str, Any]]:
        """Método run que mantiene compatibilidad con el código existente."""
        logger.info(f"Ejecutando búsqueda: '{query}'")
        results = self.search_structured(query=query, page_size=page_size)
        
        # Log para debugging
        if results and not any("error" in str(result) for result in results):
            logger.info(f"Resultados obtenidos: {len(results)}")
            for i, result in enumerate(results[:2]):
                logger.info(f"  {i+1}: {result.get('title')} (pág. {result.get('page')})")
        
        return results

# Instancia global
vertex_search = VertexSearchToolClient(
    project_id=settings.google_project_id,
    data_store_id=settings.data_store_id,
    location=getattr(settings, 'google_location', 'global')
)