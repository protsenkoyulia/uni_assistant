from aiogram import Bot, Dispatcher
from aiogram.filters import Command, or_f
from aiogram import F
from aiogram.types import Message
from config import TG_TOKEN
from rag.vector_store import load_vector_db
from rag.chain import build_rag_chain
from services.context_cache import (
    get_user_language, set_user_language,
    get_user_context, save_user_context,
    clear_user_context
)
from bot_tg.keyboards import get_main_keyboard, get_language_keyboard

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

vector_db = load_vector_db()
rag_chain = build_rag_chain(vector_db)


@dp.message(Command('start'))
async def start_handler(message: Message):
    lang = get_user_language(message.from_user.id)
    await message.answer(
        '👋 Привет! Я помогу тебе адаптироваться к университету!',
        reply_markup=get_main_keyboard(lang),
    )


@dp.message(or_f(
    F.text.in_(["Помощь", "帮助", "Help"]),
    Command('help')
))
async def help_handler(message: Message):
    lang = get_user_language(message.from_user.id)
    await message.answer(
        '📌 Просто напиши свой вопрос, и я отвечу!\n'
        'Команды:\n'
        '/start — приветствие\n'
        '/help или «Помощь» — эта справка\n'
        '/language или «Язык» — смена языка\n'
        '/clear или «Очистить» — очистить историю',
        reply_markup=get_main_keyboard(lang),
    )


@dp.message(or_f(
        F.text.in_(["Язык", "语言", "Language"]),
        Command('language')
))
async def language_command(message: Message):
    await message.answer(
        'Выбери язык / Select language / 选择语言:',
        reply_markup=get_language_keyboard(),
    )


@dp.message(or_f(
    F.text.in_(["Очистить", "清空", "Clear"]),
    Command('clear')
))
async def clear_handler(message: Message):
    clear_user_context(message.from_user.id)
    lang = get_user_language(message.from_user.id)
    await message.answer(
        'История диалога очищена',
        reply_markup=get_main_keyboard(lang)
        )


@dp.message(or_f(
    F.text.in_(["Перевод", "翻译", "Translate"]),
    Command('translate')
))
async def translate_handler(message: Message):
    user_id = message.from_user.id
    user_lang = get_user_language(user_id)

    text_to_translate = ""
    if len(message.text.split(maxsplit=1)) > 1:
        text_to_translate = message.text.split(maxsplit=1)[1].strip()

    if not text_to_translate:
        await message.answer(
            "Чтобы перевести текст:\n"
            "Напиши: /translate Привет, как дела?\n"
            "Я переведу на русский, китайский и английский "
            "с учётом контекста диалога."
        )
        return

    context = get_user_context(user_id)
    recent_context = context[-6:] if context else []

    context_str = "\n".join(
        f"{'Пользователь' if msg['role'] == 'user' else 'Бот'}: {msg['content']}"
        for msg in recent_context
    )

    prompt = f"""Ты — профессиональный многоязычный переводчик.
                 Текущий язык общения пользователя: {user_lang.upper()}
                 (ru=русский, zh=китайский, en=английский).

                 Контекст диалога (для сохранения смысла и стиля):
                 {context_str if context_str else "Контекста нет"}

                 Переведи следующий текст на ВСЕ три языка: русский,
                 китайский (упрощённый), английский.
                 Сохраняй эмоции, стиль и точный смысл.
                 Если текст уже на одном из этих языков —
                 всё равно переведи на остальные.

                 Текст:
                 {text_to_translate}

                 Формат ответа строго такой:
                 Русский: [перевод]
                 Китайский: [перевод]
                 Английский: [перевод]"""

    await bot.send_chat_action(chat_id=message.chat.id, action='typing')

    try:
        response = rag_chain.invoke({'input': prompt})
        translated = response.get('answer', '').strip()

        await message.answer(
            f"**Перевод с учётом контекста диалога**\n\n"
            f"{translated}",
            reply_markup=get_main_keyboard(user_lang)
        )

    except Exception as e:
        print(f"Ошибка перевода: {e}")
        await message.answer(
            "Не удалось выполнить перевод 😔\n"
            "Попробуй позже или напиши текст короче."
        )


@dp.message(lambda m: m.text == '🌍 Язык' or
            m.text == '🌍 语言' or m.text == '🌍 Language')
async def language_button(message: Message):
    await message.answer(
        'Выбери язык / Select language / 选择语言:',
        reply_markup=get_language_keyboard(),
    )


@dp.message(lambda m: m.text == '🇷🇺 Русский')
async def set_ru(message: Message):
    set_user_language(message.from_user.id, 'ru')
    await message.answer('Язык изменён на русский 🇷🇺',
                         reply_markup=get_main_keyboard('ru'))


@dp.message(lambda m: m.text == '🇨🇳 中文')
async def set_zh(message: Message):
    set_user_language(message.from_user.id, 'zh')
    await message.answer('语言已切换为中文 🇨🇳', reply_markup=get_main_keyboard('zh'))


@dp.message(lambda m: m.text == '🇬🇧 English')
async def set_en(message: Message):
    set_user_language(message.from_user.id, 'en')
    await message.answer('Language changed to English 🇬🇧',
                         reply_markup=get_main_keyboard('en'))


@dp.message()
async def main_handler(message: Message):
    user_id = message.from_user.id
    user_text = message.text.strip()
    lang = get_user_language(user_id)

    if user_text in [
        'Помощь', '帮助', 'Help',
        'Язык', '语言', 'Language',
        'Очистить', '清空', 'Clear',
        '🇷🇺 Русский', '🇨🇳 中文', '🇬🇧 English',
    ]:
        return

    await bot.send_chat_action(chat_id=message.chat.id, action='typing')

    try:
        context = get_user_context(user_id)
        recent_context = context[-10:] if context else []

        history = ""
        if recent_context:
            history = "История диалога (обязательно учитывай):\n"
            for msg in recent_context:
                role = "Студент" if msg['role'] == 'user' else "Ассистент"
                history += f"{role}: {msg['content']}\n"
            history += "\n"

        input = f"""{history}
                       Текущий вопрос студента: {user_text}"""

        response = rag_chain.invoke({'input': input})
        answer = response.get('answer', 'Не удалось получить ответ')

        context.extend([
            {'role': 'user', 'content': user_text},
            {'role': 'assistant', 'content': answer},
        ])
        save_user_context(user_id, context[-20:])

        await message.answer(answer, reply_markup=get_main_keyboard(lang))

    except Exception as e:
        print(f'Ошибка: {e}')
        await message.answer('Произошла ошибка, попробуй ещё раз')


async def start_bot():
    await dp.start_polling(bot)
