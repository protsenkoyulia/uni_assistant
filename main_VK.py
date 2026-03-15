from pathlib import Path
from bot.vk_handler import bot
from rag.loader import load_documents, split_documents
from rag.vector_store import create_vector_db, close


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


if __name__ == '__main__':
    try:
        init_rag()
        print('Бот запущен!')
        bot.run_forever()
    finally:
        close()
