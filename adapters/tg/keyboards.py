from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    labels = {
        'ru': {
            'translate': 'Перевод',
            'schedule':  'Расписание',
            'help':      'Помощь',
            'language':  'Язык',
            'clear':     'Очистить',
        },
        'zh': {
            'translate': '翻译',
            'schedule':  '课程表',
            'help':      '帮助',
            'language':  '语言',
            'clear':     '清空',
        },
        'en': {
            'translate': 'Translate',
            'schedule':  'Schedule',
            'help':      'Help',
            'language':  'Language',
            'clear':     'Clear',
        },
    }
    lb = labels.get(lang, labels['ru'])

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=lb['translate'])],
            [KeyboardButton(text=lb['schedule']),
             KeyboardButton(text=lb['help'])],
            [KeyboardButton(text=lb['language']),
             KeyboardButton(text=lb['clear'])],
        ],
        resize_keyboard=True,
    )


def get_language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text='🇷🇺 Русский'),
            KeyboardButton(text='🇨🇳 中文'),
            KeyboardButton(text='🇬🇧 English'),
        ]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
