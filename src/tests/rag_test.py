from src.tools.embedding_search import VertexSearchToolClient

tool = VertexSearchToolClient(
    project_id="601761127350",
    data_store_id="data-engineering-kb_1757028424076",
    location="global",
)

# Ejecutar query
response = tool.run("pyspark")  
for r in response:
    # Algunos objetos devuelven .derived_struct_data, otros .content directamente
    if hasattr(r, "derivedStructData") and "extractive_answers" in r.derivedStructData:
        print(r.derivedStructData["extractive_answers"][0]["content"])
    else:
        print(r)

