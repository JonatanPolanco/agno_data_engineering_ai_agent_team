from src.tools.embedding_search import query_datastore

if __name__ == "__main__":
    query = "ETL vs ELT"
    print(f"🔍 Probando búsqueda: {query}\n")

    results = query_datastore(query, page_size=1329)

    for i, doc in enumerate(results, 1):
        print(f"\n📄 Resultado {i}")
        for k, v in doc.items():
            print(f"   {k}: {str(v)[:120]}")
