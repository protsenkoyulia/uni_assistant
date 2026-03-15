import time
import weaviate
from langchain_weaviate import WeaviateVectorStore
from langchain_gigachat import GigaChatEmbeddings
from config import AUTH_KEY_GIGACHAT

INDEX_NAME = "KnowledgeBase"

_client = None


def get_weaviate_client():
    global _client
    if _client is None or not _client.is_connected():
        _client = weaviate.connect_to_local(
            host="localhost",
            port=8080,
        )
        _wait_for_weaviate(_client)
    return _client


def _wait_for_weaviate(client, retries: int = 10, delay: float = 2.0):
    """Ждёт пока Weaviate полностью запустится."""
    for attempt in range(retries):
        try:
            if client.is_ready():
                print("Weaviate готов")
                return
        except Exception:
            pass
        print(f"Weaviate ещё не готов, ждём... ({attempt + 1}/{retries})")
        time.sleep(delay)
    raise RuntimeError("Weaviate не запустился за отведённое время")


def get_embeddings():
    return GigaChatEmbeddings(
        credentials=AUTH_KEY_GIGACHAT,
        verify_ssl_certs=False,
        model="Embeddings"
    )


def create_vector_db(chunks: list) -> WeaviateVectorStore:
    client = get_weaviate_client()
    embeddings = get_embeddings()
    vector_db = WeaviateVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        client=client,
        index_name=INDEX_NAME,
        text_key="text",
    )
    print(f"Weaviate коллекция '{INDEX_NAME}' создана")
    return vector_db


def load_vector_db() -> WeaviateVectorStore:
    client = get_weaviate_client()
    embeddings = get_embeddings()
    return WeaviateVectorStore(
        client=client,
        index_name=INDEX_NAME,
        text_key="text",
        embedding=embeddings,
    )


def close():
    """Вызвать при завершении работы бота."""
    global _client
    if _client is not None and _client.is_connected():
        _client.close()
        _client = None
