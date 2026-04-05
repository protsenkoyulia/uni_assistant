from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from core.rag.vector_store import load_vector_db
from core.rag.chain import build_rag_chain
from core.services.context_cache import (
    get_user_language, set_user_language,
    get_user_context, save_user_context,
    clear_user_context
)
from core.services.translation import translate
from shared.models import IncomingMessage, OutgoingMessage

app = FastAPI(title="UniHelper Core API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

vector_db = load_vector_db()
rag_chain = build_rag_chain(vector_db)


@app.post('/api/chat', response_model=OutgoingMessage)
async def chat(message: IncomingMessage):
    user_id = message.user_id
    user_text = message.text.strip()
    lang = message.lang or get_user_language(user_id)

    try:
        context = get_user_context(user_id)
        recent_context = context[-5:] if context else []

        history = ''
        if recent_context:
            history = 'История диалога:\n'
            for msg in recent_context:
                role = 'Студент' if msg['role'] == 'user' else 'Ассистент'
                history += f"{role}: {msg['content'][:150]}...\n"
            history += "\n"

        response = rag_chain.invoke({'input': user_text, 'history': history})
        answer = response.get('answer', 'Не удалось получить ответ')

        context.extend([
            {'role': 'user', 'content': user_text},
            {'role': 'assistant', 'content': answer},
        ])
        save_user_context(user_id, context[-10:])

        return OutgoingMessage(
            platform=message.platform,
            user_id=user_id,
            text=answer,
            lang=lang
        )

    except Exception as e:
        print(f"Ошибка в Core API: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@app.post('/api/clear/{user_id}')
async def clear(user_id: str):
    clear_user_context(user_id)
    return {
        'status': 'success',
        'message': 'История очищена'
    }


@app.post('/api/translate', response_model=OutgoingMessage)
async def translate_endpoint(message: IncomingMessage):
    user_id = message.user_id
    text_to_translate = message.text.strip()
    lang = message.lang or get_user_language(user_id)

    context = get_user_context(user_id)
    recent_context = context[-5:] if context else []

    context_str = "\n".join(
        f"""{'Пользователь' if msg['role'] == 'user' else 'Бот'}:
          {msg['content']}"""
        for msg in recent_context
    )
    try:
        loop = asyncio.get_event_loop()
        translated = await loop.run_in_executor(
            None,
            translate,
            text_to_translate,
            lang,
            context_str,
        )

        if lang == 'ru':
            msg = 'Перевод с учётом контекста диалога\n\n'
        elif lang == 'en':
            msg = 'Context-aware translation\n\n'
        else:
            msg = '结合对话上下文的翻译\n\n'

        return OutgoingMessage(
            platform=message.platform,
            user_id=user_id,
            text=msg + translated,
            lang=lang
        )

    except Exception as e:
        print(f"Ошибка перевода: {e}")
        raise HTTPException(status_code=500, detail="Ошибка перевода")


@app.post('/api/set_language')
async def set_lang(data: dict):
    user_id = data.get('user_id')
    lang = data.get('lang')
    if user_id and lang in ['ru', 'zh', 'en']:
        set_user_language(user_id, lang)
        return {'status': 'success'}
    raise HTTPException(status_code=400, detail='Неверные данные')
