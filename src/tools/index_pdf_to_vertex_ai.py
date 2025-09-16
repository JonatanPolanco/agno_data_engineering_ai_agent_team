import os
import re
import tempfile
import pymupdf
from datetime import datetime
from google.cloud import storage
from google.cloud import discoveryengine_v1 as discovery
from google.protobuf.struct_pb2 import Struct
from src.config import settings

# Configuración desde settings
PROJECT_ID = settings.google_project_id
LOCATION = "global"
DATA_STORE_ID = settings.data_store_id
BUCKET_NAME = "data_engineering_books"

# Cliente GCS
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# Cliente Vertex AI Search
discovery_client = discovery.DocumentServiceClient()
parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}/branches/default_branch"


def sanitize_id(name: str) -> str:
    """Convierte cualquier nombre en un ID válido para Vertex AI Search."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)


def compute_confidence(published, tier: str, text: str) -> float:
    """Calcula score de confianza basado en recency + source + calidad de texto."""
    # Recency
    if published:
        age_days = (datetime.now() - published).days
        if age_days <= 365:
            recency_score = 1.0
        elif age_days <= 730:
            recency_score = 0.7
        else:
            recency_score = 0.4
    else:
        recency_score = 0.6  # desconocido

    # Source reliability
    tier_map = {"1": 1.0, "2": 0.8, "3": 0.6}
    reliability_score = tier_map.get(str(tier), 0.5)

    # Content quality
    has_pii = bool(re.search(r"\b[\w.-]+@[\w.-]+\.\w{2,}\b", text))
    quality_score = 1.0 if len(text) > 500 and not has_pii else 0.7

    return round(0.5 * recency_score + 0.3 * reliability_score + 0.2 * quality_score, 2)


def extract_published(blob) -> datetime | None:
    """Intenta extraer fecha de publicación del blob metadata o updated."""
    if blob.time_created:
        return blob.time_created
    if blob.updated:
        return blob.updated
    return None


def index_pdf_from_gcs(blob_name, book_title, author="Desconocido"):
    """
    Descarga un PDF desde GCS, lo divide en páginas y lo indexa en Vertex AI Search.
    """
    local_path = os.path.join(tempfile.gettempdir(), os.path.basename(blob_name))
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    print(f"Descargado: {blob_name}")

    doc = pymupdf.open(local_path)

    base_id = os.path.splitext(os.path.basename(blob_name))[0]
    safe_id = sanitize_id(base_id)

    # Extraer fecha publicada a nivel documento
    published = extract_published(blob)

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if not text:
            continue

        # Metadata enriquecida
        struct_data = Struct()
        pii_detected = bool(re.search(r"\b[\w.-]+@[\w.-]+\.\w{2,}\b", text))
        confidence_score = compute_confidence(published, "1", text)  # tier=1 por docs internas

        struct_data.update({
            "title": book_title,
            "author": author,
            "page": page_num,
            "content": text,
            "uri": f"gs://{BUCKET_NAME}/{blob_name}",
            "published": published.isoformat() if published else None,
            "pii_detected": pii_detected,
            "confidence_score": confidence_score,
        })

        document = discovery.Document(
            id=f"{safe_id}-p{page_num}",
            struct_data=struct_data,
            content=discovery.Document.Content(
                mime_type="text/plain",
                raw_bytes=text.encode("utf-8")
            )
        )

        request = discovery.CreateDocumentRequest(
            parent=parent,
            document=document,
            document_id=document.id,
        )

        try:
            discovery_client.create_document(request=request)
            print(f"Indexada página {page_num} de {book_title} (conf={confidence_score})")
        except Exception as e:
            print(f"Error indexando {book_title} p.{page_num}: {e}")


def index_all_pdfs():
    """Recorre todos los PDFs en el bucket y los indexa en Vertex AI Search."""
    blobs = storage_client.list_blobs(BUCKET_NAME, prefix="")
    for blob in blobs:
        if blob.name.endswith(".pdf"):
            book_title = os.path.splitext(os.path.basename(blob.name))[0]
            author = "Desconocido"
            index_pdf_from_gcs(blob.name, book_title, author)


if __name__ == "__main__":
    print("Iniciando indexación...")
    index_all_pdfs()
