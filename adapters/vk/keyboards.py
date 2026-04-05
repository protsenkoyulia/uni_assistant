from vkbottle import Keyboard, Text, KeyboardButtonColor


def get_main_keyboard(lang: str = 'ru') -> str:
    labels = {
        'ru': {'ask': 'Задать вопрос', 'translate': 'Перевод',
               'schedule': 'Расписание', 'help': 'Помощь', 'language': 'Язык'},
        'zh': {'ask': '提问', 'translate': '🌐 翻译',
               'schedule': '课程表', 'help': '帮助', 'language': '语言'},
        'en': {'ask': 'Ask question', 'translate': 'Translate',
               'schedule': 'Schedule', 'help': 'Help', 'language': 'Language'},
    }
    lb = labels.get(lang, labels['ru'])
    keyboard = (
        Keyboard(one_time=False)
        .add(Text(lb['ask']), color=KeyboardButtonColor.PRIMARY)
        .add(Text(lb['translate']), color=KeyboardButtonColor.SECONDARY)
        .row()
        .add(Text(lb['schedule']), color=KeyboardButtonColor.SECONDARY)
        .add(Text(lb['help']), color=KeyboardButtonColor.SECONDARY)
        .row()
        .add(Text(lb['language']), color=KeyboardButtonColor.POSITIVE)
    )
    return keyboard.get_json()


def get_language_keyboard() -> str:
    keyboard = (
        Keyboard(one_time=True)
        .add(Text('🇷🇺 Русский'), color=KeyboardButtonColor.SECONDARY)
        .add(Text('🇨🇳 中文'), color=KeyboardButtonColor.SECONDARY)
        .add(Text('🇬🇧 English'), color=KeyboardButtonColor.SECONDARY)
    )
    return keyboard.get_json()
