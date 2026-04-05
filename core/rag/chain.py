from langchain_gigachat import GigaChat
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from core.config import AUTH_KEY_GIGACHAT, MODEL_GIGACHAT

SYSTEM_PROMPT = """
Ты — интеллектуальный ассистент для китайских студентов,
обучающихся в российских университетах.

Строго соблюдай следующие правила:

1. Автоматически определи язык запроса пользователя (ru / zh / en).
2. Отвечай на том же языке, что и запрос.
3. Отвечай на основе базы знаний и контекста.
4. Если в контексте есть частичный ответ — используй его, не говори что информации нет
5. Если ответ полностью отсутствует в базе знаний и контектсе, сообщи:
   "Запрашиваемая информация отсутствует в текущей базе знаний." 
6. Используй дружелюбный тон и простые формулировки.
7. Избегай выдумывания информации.
8. Избегай личных комментариев.

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
        max_tokens=500
    )

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(
            'Контекст: {context}\nИстория: {history}\nВопрос: {input}\nОтвет:'
        ),
    ])

    retriever = vector_db.as_retriever(
        search_type='similarity',
        search_kwargs={'k': 10},
    )

    stuff_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, stuff_chain)
