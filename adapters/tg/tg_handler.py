from aiogram import Bot, Dispatcher
from aiogram.filters import Command, or_f
from aiogram import F
from aiogram.types import Message
import httpx

from core.config import TG_TOKEN
from core.services.context_cache import (
    get_user_language, set_user_language,
)
from shared.models import IncomingMessage
from adapters.tg.keyboards import get_main_keyboard, get_language_keyboard


bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

CORE_API_URL = "http://127.0.0.1:8001"


async def send_to_core(endpoint: str, message: IncomingMessage):
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{CORE_API_URL}/api/{endpoint}",
            json=message.model_dump())
        response.raise_for_status()
        return response.json()


@dp.message(Command('start'))
async def start_handler(message: Message):
    await message.answer(
        'Привет! / Hello! / 你好!\n\n'
        'Выбери язык для общения:\n'
        'Select your language:\n'
        '请选择语言:',
        reply_markup=get_language_keyboard(),
    )


@dp.message(or_f(
    F.text.in_(["Помощь", "帮助", "Help"]),
    Command('help')
))
async def help_handler(message: Message):
    lang = get_user_language(message.from_user.id)
    if lang == 'ru':
        msg = (
            'Просто напиши свой вопрос, и я отвечу!\n'
            'Команды:\n'
            '/start — приветствие\n'
            '/help или «Помощь» — эта справка\n'
            '/language или «Язык» — смена языка\n'
            '/clear или «Очистить» — очистить историю'
        )
    elif lang == 'en':
        msg = (
            'Just write your question and I\'ll answer!\n'
            'Commands:\n'
            '/start — greeting\n'
            '/help или «Help» — this help message\n'
            '/language или «Language» — change language\n'
            '/clear или «Clear» — clear history'
        )
    else:
        msg = (
            '只需写下你的问题，我就会回答!\n'
            '命令:\n'
            '/start — 问候\n'
            '/help 或 "帮助" — 本帮助信息\n'
            '/language 或 "语言" — 切换语言\n'
            '/clear 或 "清空" — 清空历史记录'
        )
    await message.answer(
        msg,
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
    user_id = str(message.from_user.id)
    async with httpx.AsyncClient() as client:
        await client.post(f"{CORE_API_URL}/api/clear/{user_id}")
    lang = get_user_language(user_id)
    await message.answer('История очищена / Cleared / 已清空',
                         reply_markup=get_main_keyboard(lang))


@dp.message(or_f(
    F.text.in_(["Перевод", "翻译", "Translate"]),
    Command('translate')
))
async def translate_handler(message: Message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)

    text_to_translate = ""
    if len(message.text.split(maxsplit=1)) > 1:
        text_to_translate = message.text.split(maxsplit=1)[1].strip()

    hints = {
        'ru': (
            'Чтобы перевести текст:\n'
            'Напиши: /translate Текст, который нужно перевести \n'
            'Я переведу на русский, китайский и английский '
            'с учётом контекста диалога.'
        ),
        'en': (
            'To translate text:\n'
            'Write: /translate The text you want to translate \n'
            'I will translate it into Russian, Chinese, and English, '
            'taking into account the context of the dialogue.'
        ),
        'zh': (
            '要翻译文本：\n'
            '请发送：/translate 需要翻译的文本\n'
            '我会结合对话上下文，将其翻译成俄语、中文和英语。'
        )
    }
    if not text_to_translate:
        await message.answer(hints.get(lang, hints['en']))
        return

    await bot.send_chat_action(chat_id=message.chat.id, action='typing')

    try:
        result = await send_to_core('translate', IncomingMessage(
            platform='telegram',
            user_id=user_id,
            text=text_to_translate,
            lang=lang,
        ))

        await message.answer(
            result['text'],
            reply_markup=get_main_keyboard(lang)
        )

    except Exception as e:
        print(f"Ошибка перевода: {e}")
        if lang == 'zh':
            msg = '翻译失败。\n请使用 /clear 或按下"清空"按钮清空历史记录。'
        elif lang == 'en':
            msg = (
                'Translation failed.\nPlease clear history with /clear'
                ' or "Clear" button.'
            )
        else:
            msg = (
                'Не удалось выполнить перевод.\n'
                'Очистите историю диалога командой /clear'
                ' или кнопкой "Очистить".'
            )
        await message.answer(msg, reply_markup=get_main_keyboard(lang))


@dp.message(lambda m: m.text == '🇷🇺 Русский')
async def set_ru(message: Message):
    set_user_language(message.from_user.id, 'ru')
    await message.answer(
        'Язык установлен: Русский\n\n'
        'Привет! Я помогу тебе адаптироваться в университете.\n'
        'Просто напиши свой вопрос, и я отвечу!\n'
        'Команды:\n'
        '/start — приветствие\n'
        '/help или «Помощь» — эта справка\n'
        '/language или «Язык» — смена языка\n'
        '/clear или «Очистить» — очистить историю',
        reply_markup=get_main_keyboard('ru')
        )


@dp.message(lambda m: m.text == '🇨🇳 中文')
async def set_zh(message: Message):
    set_user_language(message.from_user.id, 'zh')
    await message.answer(
        '语言已设置：中文\n\n'
        '你好！我将帮助你适应大学生活。\n'
        '直接输入你的问题吧！\n'
        '命令:\n'
        '/start — 问候\n'
        '/help 或 "帮助" — 本帮助信息\n'
        '/language 或 "语言" — 切换语言\n'
        '/clear 或 "清空" — 清空历史记录',
        reply_markup=get_main_keyboard('zh')
        )


@dp.message(lambda m: m.text == '🇬🇧 English')
async def set_en(message: Message):
    set_user_language(message.from_user.id, 'en')
    await message.answer(
        'Language set: English\n\n'
        'Hello! I will help you adapt to university life.\n'
        'Just write your question and I\'ll answer!\n'
        'Commands:\n'
        '/start — greeting\n'
        '/help или «Help» — this help message\n'
        '/language или «Language» — change language\n'
        '/clear или «Clear» — clear history',
        reply_markup=get_main_keyboard('en')
        )


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
        result = await send_to_core('chat', IncomingMessage(
            platform='telegram',
            user_id=user_id,
            text=user_text,
            lang=lang,
        ))

        await message.answer(result['text'],
                             reply_markup=get_main_keyboard(lang))

    except Exception as e:
        print(f'Ошибка: {e}')
        errors = {
            'ru': (
                'Произошла ошибка, попробуй очистить историю диалога командой'
                ' /clear или кнопкой "Очистить".'
            ),
            'en': (
                'An error has occurred.\nTry clearing the dialogue history'
                'using the /clear or "Clear" button.'
            ),
            'zh': '发生错误。请尝试使用 /clear 命令或“清除”按钮清除对话历史。'
        }
        await message.answer(errors.get(lang, errors['en']),
                             reply_markup=get_main_keyboard(lang))


async def start_bot():
    await dp.start_polling(bot)
