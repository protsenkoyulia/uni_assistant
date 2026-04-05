import nest_asyncio
import uvicorn
import asyncio
from pathlib import Path
from core.rag.loader import load_documents, split_documents
from core.rag.vector_store import create_vector_db, close

nest_asyncio.apply()


def init_rag():
    db_path = Path('./vector_db/KnowledgeBase')
    if not db_path.exists():
        print('Создаём векторную БД первый раз')
        docs = load_documents('./data/knowledge_base')
        chunks = split_documents(docs)
        create_vector_db(chunks)
        print('Векторная БД готова!')
    else:
        print('Векторная БД уже существует, загружаем...')


async def run_api():
    from core.api import app
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=8001,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def run_tg_bot():
    from adapters.tg.tg_handler import start_bot
    await start_bot()


async def main():
    init_rag()
    print('Core API и Telegram бот запускаются...')
    await asyncio.gather(
        run_api(),
        run_tg_bot(),
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        close()
