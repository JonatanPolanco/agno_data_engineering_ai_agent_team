# src/agents/definitions.py


import logging
from typing import Optional, List, Dict, Any

# --- Imports nativos y correctos de Agno 2.0 ---
from agno.agent import Agent
from google.cloud import discoveryengine_v1 as discoveryengine

from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools

from src.config import settings
from src.tools.prompts import (CODE_STANDARDS_ENHANCED, LEAD_PROMPT, RAG,
                               WEB_SEARCH)

logger = logging.getLogger(__name__)

# === ENVIRONMENT ===
GOOGLE_API_KEY = settings.google_api_key
DEFAULT_MODEL = settings.default_llm_flash
DEFAULT_MODEL_PRO = settings.default_llm_pro


if not GOOGLE_API_KEY:
    raise RuntimeError("❌ GOOGLE_API_KEY no está definido en .env ni en el entorno.")

# ==============================================================================
#  LÓGICA DE CONSTRUCCIÓN Y CREACIÓN DE AGENTES (ESTILO AGNO 2.0)
# ==============================================================================

def vertex_ai_search_retriever(
    query: str, agent: Optional[Agent] = None, num_documents: int = 5, **kwargs
) -> Optional[List[Dict[str, Any]]]:
    try:
        client = discoveryengine.SearchServiceClient()
        serving_config = client.serving_config_path(
            project=settings.google_project_id,
            location=settings.google_location,
            data_store=settings.data_store_id,
            serving_config="default_config",
        )

        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=num_documents,
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
                    max_extractive_answer_count=1
                )
            ),
        )
        response = client.search(request=request)

        # Esto nos mostrará la estructura real de un resultado.
        if response.results:
            print("--- DEBUG: Estructura del primer resultado de Vertex AI ---")
            print(response.results[0].document)
            print("---------------------------------------------------------")
        
        retrieved_documents = []
        for i, result in enumerate(response.results):
            doc = result.document
            
            content_text = ""
            if doc.derived_struct_data and 'extractive_answers' in doc.derived_struct_data and doc.derived_struct_data['extractive_answers']:
                content_text = doc.derived_struct_data['extractive_answers'][0]['content']
            elif doc.struct_data and 'content' in doc.struct_data:
                content_text = doc.struct_data['content']

            # Usamos `doc.name` o un placeholder si 'uri' no está en los metadatos.
            # `doc.name` es un identificador único del recurso en Google Cloud.
            source_uri = doc.struct_data.get("uri", doc.name) 
            
            payload = {
                "title": doc.struct_data.get("title", ""),
                "content": content_text,
                "author": doc.struct_data.get("author", ""),
                "uri": source_uri, # Usamos la variable corregida
                "page": doc.struct_data.get("page", 0)
            }
            
            score = 1.0 - (i * 0.1)
            retrieved_documents.append({
                "id": doc.id,
                "score": score,
                "payload": payload
            })
        
        return retrieved_documents

    except Exception as e:
        print(f"Error durante la búsqueda en Vertex AI Search: {str(e)}")
        return None
    
def build_context_block(user: str, session_id: str) -> str:
    return f"""
    - CONTEXTO DE SESIÓN -
    - Session: {session_id}
    - Usuario: {user}
    """


# --- Las funciones de creación de agentes ahora son más simples y correctas ---

def create_rag_agent(user: str, session_id: str) -> Optional[Agent]:
    return Agent(
        # Pasamos directamente la función que devuelve una lista de diccionarios.
        knowledge_retriever=vertex_ai_search_retriever, 
        search_knowledge=True,
        instructions="Basado en el siguiente contexto extraído de la base de conocimiento, responde la pregunta del usuario.",
        model=Gemini(id=settings.default_llm_flash, api_key=settings.google_api_key)
    )

def create_web_agent(user: str, session_id: str) -> Agent:
    return Agent(
        name="Web Agent", role="Agente externo en documentación oficial.",
        model=Gemini(id=DEFAULT_MODEL, api_key=GOOGLE_API_KEY),
        tools=[DuckDuckGoTools()],
        instructions=WEB_SEARCH + build_context_block(user, session_id),
        user_id=user, 
        session_id=session_id,
    )

def create_lead_agent(user: str, session_id: str) -> Agent:
    return Agent(
        name="Lead Agent", role="Orquestador multi-agente.",
        model=Gemini(id=DEFAULT_MODEL, api_key=GOOGLE_API_KEY),
        instructions=LEAD_PROMPT + build_context_block(user, session_id),
        user_id=user, 
        session_id=session_id,
    )

def create_code_standards_agent(user: str, session_id: str) -> Agent:
    return Agent(
        name="Code Standards Agent", role="Agente de revisiÃ³n de cÃ³digo.",
        model=Gemini(id=DEFAULT_MODEL, api_key=GOOGLE_API_KEY),
        instructions=CODE_STANDARDS_ENHANCED + build_context_block(user, session_id),
        user_id=user,
        session_id=session_id,
    )

def get_all_agents(user: str, session_id: str) -> Dict[str, Agent]:
    agents = {
        "Lead Agent": create_lead_agent(user, session_id),
        "Web Agent": create_web_agent(user, session_id),
        "Code Standards Agent": create_code_standards_agent(user, session_id)
    }
    rag_agent = create_rag_agent(user, session_id)
    if rag_agent:
        agents["RAG Agent"] = rag_agent
    else:
        logger.error("No se pudo inicializar el RAG Agent. El equipo funcionará sin conocimiento interno.")
    return agents