import asyncio
from agno.storage.sqlite import SqliteStorage
from src.config import settings
from src.agents.definitions import create_rag_agent

async def main():
    user = "test_user"
    session_id = "session_003"

    storage = SqliteStorage(
        table_name=f"rag_test_{user}_{session_id}",
        db_file=settings.db_file_path,
    )

    rag_agent = create_rag_agent(user, session_id, storage)

    query = "ETL vs ELT"

    print(f"🔍 Enviando consulta al RAG Agent:\n{query}\n")

    response = await rag_agent.arun(query)
    print("📢 Respuesta del RAG Agent:\n")
    print(response.content)

if __name__ == "__main__":
    asyncio.run(main())
