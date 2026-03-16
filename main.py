import nest_asyncio
import asyncio
from pathlib import Path
from rag.loader import load_documents, split_documents
from rag.vector_store import create_vector_db, close

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


async def main():
    from bot_tg.tg_handler import start_bot
    init_rag()
    print('Бот запущен!')
    await start_bot()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        close()
