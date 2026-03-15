import ssl
import aiohttp
from vkbottle.bot import Bot, Message
from vkbottle.bot import BotLabeler
from config import VK_TOKEN
from rag.vector_store import load_vector_db
from rag.chain import build_rag_chain
from services.context_cache import (
    get_user_language, set_user_language,
    get_user_context, save_user_context,
)
from bot.keyboards import get_main_keyboard, get_language_keyboard

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

bot = Bot(token=VK_TOKEN)
bot.http_client._session = aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(ssl=ssl_context))
labeler = BotLabeler()
bot.labeler.load(labeler)

vector_db = load_vector_db()
rag_chain = build_rag_chain(vector_db)


@labeler.message(text='/start')
async def start_handler(message: Message):
    lang = get_user_language(message.from_id)
    await message.answer(
        'Привет! Я помогу тебе адаптироваться к университету!',
        keyboard=get_main_keyboard(lang),
    )


@labeler.message(text='🌍 Язык')
@labeler.message(text='🌍 语言')
@labeler.message(text='🌍 Language')
async def language_handler(message: Message):
    await message.answer(
        'Выбери язык / Select language / 选择语言:',
        keyboard=get_language_keyboard(),
    )


@labeler.message(text='🇷🇺 Русский')
async def set_ru(message: Message):
    set_user_language(message.from_id, 'ru')
    await message.answer('Язык изменён на русский 🇷🇺',
                         keyboard=get_main_keyboard('ru'))


@labeler.message(text='🇨🇳 中文')
async def set_zh(message: Message):
    set_user_language(message.from_id, 'zh')
    await message.answer('语言已切换为中文 🇨🇳', keyboard=get_main_keyboard('zh'))


@labeler.message(text='🇬🇧 English')
async def set_en(message: Message):
    set_user_language(message.from_id, 'en')
    await message.answer('Language changed to English 🇬🇧',
                         keyboard=get_main_keyboard('en'))


@labeler.message()
async def main_handler(message: Message):
    user_id = message.from_id
    user_text = message.text.strip()
    lang = get_user_language(user_id)

    await bot.api.messages.set_activity(peer_id=message.peer_id, type='typing')

    try:
        response = rag_chain.invoke({'input': user_text})
        answer = response.get('answer', 'Не удалось получить ответ')

        context = get_user_context(user_id)
        context.extend([
            {'role': 'user', 'content': user_text},
            {'role': 'assistant', 'content': answer},
        ])
        save_user_context(user_id, context[-20:])

        await message.answer(answer, keyboard=get_main_keyboard(lang))
    except Exception as e:
        print(f'Ошибка: {e}')
        await message.answer('Произошла ошибка, попробуй ещё раз')
