from langchain_gigachat import GigaChat
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from config import AUTH_KEY_GIGACHAT, MODEL_GIGACHAT

SYSTEM_PROMPT = """
Ты — интеллектуальный ассистент для китайских студентов,
обучающихся в российских университетах.

Строго соблюдай следующие правила:

1. Отвечай ТОЛЬКО на основе предоставленного контекста.
2. Если ответ отсутствует в контексте, сообщи:
   "Запрашиваемая информация отсутствует в текущей базе знаний."
3. Автоматически определи язык запроса пользователя (ru / zh / en).
4. Отвечай на том же языке, что и запрос.
5. Используй дружелюбный тон и простые формулировки.
6. Избегай выдумывания информации.
7. Используй только знания из базы знаний и контекста.
8. Избегай личных комментариев.
9. Если вопрос продолжает предыдущий — ссылайся на него.

Важно:
- Выполняй рассуждение внутренне.
- Скрывай этапы рассуждения.
- В ответе выводи только итоговый ответ пользователю.
"""


def build_rag_chain(vector_db):
    llm = GigaChat(
        credentials=AUTH_KEY_GIGACHAT,
        model=MODEL_GIGACHAT,
        verify_ssl_certs=False,
        temperature=0.3,
        top_p=0.9,
        max_tokens=1000
    )

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            'Контекст: {context}\nВопрос: {input}\nОтвет:'
        ),
    ])

    # MMR — поиск с разнообразием результатов
    retriever = vector_db.as_retriever(
        search_type='mmr',
        search_kwargs={'k': 4, 'fetch_k': 8},
    )

    stuff_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, stuff_chain)
