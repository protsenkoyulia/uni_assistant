from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from core.rag.vector_store import load_vector_db
from core.rag.chain import build_rag_chain
from core.services.admin import log_request
from core.services.context_cache import (
    get_user_language, set_user_language,
    get_user_context, save_user_context,
    get_user_group, set_user_group,
    get_cached_schedule, cache_schedule,
    clear_user_context
)
from core.services.schedule import get_schedule
from core.services.translation import translate
from core.services.faq import search_faq, get_all_faq
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

    faq_result = search_faq(user_text, lang)
    if faq_result:
        log_request(user_text, faq_result['answer'], lang)
        return OutgoingMessage(
            platform=message.platform,
            user_id=user_id,
            text=f"{faq_result['question']}\n\n{faq_result['answer']}",
            lang=lang,
        )

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
        log_request(user_text, answer, lang)

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


@app.post('/api/schedule', response_model=OutgoingMessage)
async def get_schedule_endpoint(message: IncomingMessage):
    user_id = message.user_id
    lang = message.lang or get_user_language(user_id)

    provided_group = message.text.strip() if message.text and message.text.strip() else None
    try:
        if provided_group:
            set_user_group(user_id, provided_group)

        group_id = get_user_group(user_id)

        # Если группы нет — просим ввести
        if not group_id:
            texts = {
                'ru': 'Пожалуйста, введите номер вашей учебной группы (например: 5839):',
                'en': 'Please enter your group number (e.g. 5839):',
                'zh': '请输入您的组号（例如：5839）：'
            }
            return OutgoingMessage(
                platform=message.platform,
                user_id=user_id,
                text=texts.get(lang, texts['ru']),
                lang=lang,
                need_group=True
            )

        schedule_text = get_cached_schedule(group_id)
        
        if not schedule_text:
            schedule_text = await get_schedule(group_id)
            if schedule_text and "Не удалось" not in schedule_text:
                cache_schedule(group_id, schedule_text)

        if not schedule_text:
            schedule_text = "Расписание временно недоступно."

        if lang == 'zh':
            title = f"{group_id}组的课程表\n\n"
        elif lang == 'en':
            title = f"Schedule for group {group_id}\n\n"
        else:
            title = f"Расписание для группы {group_id}\n\n"

        return OutgoingMessage(
            platform=message.platform,
            user_id=user_id,
            text=title + schedule_text,
            lang=lang
        )
    except Exception as e:
        print(f"Ошибка получения расписания: {e}")
        error_messages = {
            'ru': 'Не удалось получить расписание. Попробуйте позже.',
            'en': 'Failed to get schedule. Please try again later.',
            'zh': '无法获取课程表。请稍后再试。'
        }
        raise HTTPException(
            status_code=500, 
            detail=error_messages.get(lang, error_messages['ru'])
        )

@app.post('/api/set_language')
async def set_lang(data: dict):
    user_id = data.get('user_id')
    lang = data.get('lang')
    if user_id and lang in ['ru', 'zh', 'en']:
        set_user_language(user_id, lang)
        return {'status': 'success'}
    raise HTTPException(status_code=400, detail='Неверные данные')

@app.post('/api/faq', response_model=OutgoingMessage)
async def faq_endpoint(message: IncomingMessage):
    user_id = message.user_id
    lang = message.lang or get_user_language(user_id)
    query = message.text.strip()

    result = search_faq(query, lang)

    if result:
        return OutgoingMessage(
            platform=message.platform,
            user_id=user_id,
            text=f"{result['question']}\n\n{result['answer']}",
            lang=lang,
        )

    all_faq = get_all_faq(lang)
    if not all_faq:
        texts = {
            'ru': 'FAQ пока пуст.',
            'en': 'FAQ is empty.',
            'zh': 'FAQ 暂无内容。',
        }
        return OutgoingMessage(
            platform=message.platform,
            user_id=user_id,
            text=texts.get(lang, texts['ru']),
            lang=lang,
        )

    headers = {'ru': 'Частые вопросы:', 'en': 'FAQ:', 'zh': '常见问题：'}
    text = headers.get(lang, headers['ru']) + "\n\n"
    for item in all_faq:
        text += f"• {item['question']}\n"

    return OutgoingMessage(
        platform=message.platform,
        user_id=user_id,
        text=text,
        lang=lang,
    )

@app.get('/api/faq/all')
async def faq_all(lang: str = "ru"):
    return get_all_faq(lang)
