from pathlib import Path
from langchain_community.document_loaders import Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


def load_documents(data_dir: str = './data/knowledge_base') -> list:
    """Загружает все .docx файлы из папки базы знаний."""
    docs = []
    data_path = Path(data_dir)

    for file_path in data_path.rglob('*.docx'):
        loader = Docx2txtLoader(str(file_path))
        docs.extend(loader.load())
        print(f'Загружен: {file_path.name}')

    return docs


def split_documents(docs: list) -> list:
    """Разбивает документы на чанки с перекрытием."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        add_start_index=True,
    )
    chunks = splitter.split_documents(docs)
    print(f'Количество чанков после разбиения: {len(chunks)}')
    return chunks
