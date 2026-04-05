from langchain_gigachat import GigaChat
from langchain_core.messages import HumanMessage
from core.config import AUTH_KEY_GIGACHAT, MODEL_GIGACHAT

_llm = GigaChat(
    credentials=AUTH_KEY_GIGACHAT,
    model=MODEL_GIGACHAT,
    verify_ssl_certs=False,
    temperature=0.3,
    max_tokens=1000,
)


def build_translation_prompt(
        text: str, lang: str, context_str: str) -> str:
    return (
       f"""Ты — профессиональный многоязычный переводчик.
                 Текущий язык общения пользователя: {lang.upper()}
                 (ru=русский, zh=китайский, en=английский).

                 Контекст диалога (для сохранения смысла и стиля):
                 {context_str if context_str else "Контекста нет"}

                 Переведи следующий текст на ВСЕ три языка: русский,
                 китайский (упрощённый), английский.
                 Сохраняй эмоции, стиль и точный смысл.
                 Если текст уже на одном из этих языков —
                 всё равно переведи на остальные.

                 Текст:
                 {text}

                 Формат ответа строго такой:
                 Русский: [перевод]
                 中文: [перевод]
                 English: [перевод]"""
    )


def translate(text: str, user_lang: str, context_str: str = "") -> str:
    prompt = build_translation_prompt(text, user_lang, context_str)
    result = _llm.invoke([HumanMessage(content=prompt)])
    return result.content.strip()
