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

1. Определи язык запроса пользователя (ru / zh / en).
2. Отвечай на том же языке, что и запрос.
3. Типы вопросов и как на них отвечать:
   ВОПРОСЫ ОБ УНИВЕРСИТЕТЕ (поступление, расписание, общежитие, документы, факультеты):
   — Отвечай строго по базе знаний из контекста.
   — Если информации нет в контексте — скажи об этом честно.

   БЫТОВЫЕ ВОПРОСЫ (магазины, транспорт, еда, аптеки, банки, связь, досуг):
   — Отвечай на основе своих знаний о Санкт-Петербурге и России.
   — Давай практичные советы с учётом того, что студент — иностранец.
   — Можешь упоминать конкретные магазины, сервисы, приложения.

   ВОПРОСЫ О ЖИЗНИ В России (культура, традиции, документы, регистрация, медицина):
   — Отвечай на основе своих знаний, адаптируя ответ для иностранного студента.
4. Используй дружелюбный тон и простые формулировки.
5. Избегай выдумывания информации.
6. Избегай личных комментариев.

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
            'Контекст: {context}\nИстория: {history}\nВопрос: {input}\nОтвет:'
        ),
    ])

    retriever = vector_db.as_retriever(
        search_type='similarity',
        search_kwargs={'k': 6},
    )

    stuff_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, stuff_chain)
