from aiogram import Router, F, Bot

from aiogram.filters import Command
from aiogram.types import Message
from core.config import ADMIN_TG_ID
from core.services.admin import get_stats, list_knowledge_files
from core.services.faq import get_all_faq, add_faq, delete_faq
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

def is_admin(message: Message) -> bool:
    return str(message.from_user.id) == str(ADMIN_TG_ID)

admin_filter = is_admin


@router.message(Command("admin"), admin_filter)
async def admin_menu(message: Message):
    await message.answer(
        "Панель администратора\n\n"
        "/stats — статистика запросов\n"
        "/files — список файлов базы знаний\n"
        "/rebuild — пересобрать векторную БД\n"
        "/faq_list — список FAQ\n"
        "/faq_add — добавить FAQ\n"
        "/faq_del <id> — удалить FAQ\n"
    )

@router.message(Command("stats"), admin_filter)
async def admin_stats(message: Message):
    data = get_stats()
    text = (
        f"Статистика:\n\n"
        f"Всего запросов: {data['total']}\n"
        f"🇷🇺 Русский: {data['by_lang']['ru']}\n"
        f"🇨🇳 Китайский: {data['by_lang']['zh']}\n"
        f"🇬🇧 Английский: {data['by_lang']['en']}\n\n"
        f"Последние вопросы:\n"
    )
    for r in data["recent"][:5]:
        text += f"• [{r['lang']}] {r['question'][:80]}\n"
    await message.answer(text)


@router.message(Command("files"), admin_filter)
async def admin_files(message: Message):
    files = list_knowledge_files()
    if not files:
        await message.answer("База знаний пуста")
        return
    text = "Файлы базы знаний:\n\n"
    for f in files:
        text += f"📄 {f['name']} ({f['size_kb']} KB)\n"
        text += f"   изменён: {f['modified']}\n"
    text += "\nЧтобы добавить файл — просто пришли .docx документ в этот чат."
    await message.answer(text)


@router.message(Command("rebuild"), admin_filter)
async def admin_rebuild(message: Message):
    await message.answer("Пересборка запущена.")
    try:
        import shutil
        from pathlib import Path
        from core.rag.loader import load_documents, split_documents
        from core.rag.vector_store import create_vector_db, get_weaviate_client

        vector_path = Path("./vector_db")
        if vector_path.exists():
            shutil.rmtree(vector_path)
        
        client = get_weaviate_client()
        if client.collections.exists("KnowledgeBase"):
            client.collections.delete("KnowledgeBase")
            await message.answer("Старая коллекция удалена из Weaviate")
        client.close()

        docs = load_documents("./data/knowledge_base")
        chunks = split_documents(docs)
        create_vector_db(chunks)

        await message.answer(f"Готово! Создано чанков: {len(chunks)}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@router.message(F.document)
async def admin_upload_doc(message: Message):
    doc = message.document
    if not doc.file_name.endswith(".docx"):
        await message.answer("Принимаю только .docx файлы")
        return

    from pathlib import Path
    dest = Path("./data/knowledge_base") / doc.file_name
    dest.parent.mkdir(parents=True, exist_ok=True)

    bot: Bot = message.bot
    file = await bot.get_file(doc.file_id)
    await bot.download_file(file.file_path, destination=str(dest))

    await message.answer(
        f"Файл {doc.file_name} загружен!\n"
        f"Не забудь выполнить /rebuild чтобы обновить базу знаний."
    )

@router.message(Command("faq_list"))
async def admin_faq_list(message: Message):
    if not is_admin(message):
        return
    items = get_all_faq("ru")
    if not items:
        await message.answer("FAQ пуст")
        return
    text = "Список FAQ:\n\n"
    for item in items:
        text += f"[{item['id']}] {item['question']}\n"
    text += "\nУдалить: /faq_del <id>"
    await message.answer(text)


@router.message(Command("faq_del"))
async def admin_faq_del(message: Message):
    if not is_admin(message):
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /faq_del <id>")
        return
    faq_id = int(parts[1])
    if delete_faq(faq_id):
        await message.answer(f"FAQ #{faq_id} удалён")
    else:
        await message.answer(f"FAQ #{faq_id} не найден")


class AddFAQ(StatesGroup):
    keywords   = State()  # ключевые слова
    question   = State()  # вопрос на ru
    answer_ru  = State()  # ответ на ru
    answer_en  = State()  # ответ на en
    answer_zh  = State()  # ответ на zh

@router.message(Command("faq_add"))
async def admin_faq_add_start(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    await state.set_state(AddFAQ.keywords)
    await message.answer(
        "Добавление нового FAQ\n\n"
        "Шаг 1/5 — Введи ключевые слова через запятую:\n"
        "Пример: заселение общежитие, как заселиться, move in dorm\n\n"
        "Отмена: /cancel"
    )

@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    if not is_admin(message):
        return
    current = await state.get_state()
    if current is None:
        await message.answer("Нет активного действия")
        return
    await state.clear()
    await message.answer("Отменено")

@router.message(AddFAQ.keywords)
async def faq_step_keywords(message: Message, state: FSMContext):
    keywords = [k.strip() for k in message.text.split(",") if k.strip()]
    if len(keywords) < 2:
        await message.answer("Введи минимум 2 ключевых слова через запятую:")
        return
    await state.update_data(keywords=keywords)
    await state.set_state(AddFAQ.question)
    await message.answer(
        f"Ключевые слова: {', '.join(keywords)}\n\n"
        "Шаг 2/5 — Введи вопрос на русском:"
    )


@router.message(AddFAQ.question)
async def faq_step_question(message: Message, state: FSMContext):
    await state.update_data(question_ru=message.text.strip())
    await state.set_state(AddFAQ.answer_ru)
    await message.answer(
        f"Вопрос: {message.text.strip()}\n\n"
        "Шаг 3/5 — Введи ответ на русском:"
    )


@router.message(AddFAQ.answer_ru)
async def faq_step_answer_ru(message: Message, state: FSMContext):
    await state.update_data(answer_ru=message.text.strip())
    await state.set_state(AddFAQ.answer_en)
    await message.answer("Шаг 4/5 — Введи ответ на английском:")


@router.message(AddFAQ.answer_en)
async def faq_step_answer_en(message: Message, state: FSMContext):
    await state.update_data(answer_en=message.text.strip())
    await state.set_state(AddFAQ.answer_zh)
    await message.answer("Шаг 5/5 — Введи ответ на китайском:")


@router.message(AddFAQ.answer_zh)
async def faq_step_answer_zh(message: Message, state: FSMContext):
    await state.update_data(answer_zh=message.text.strip())
    data = await state.get_data()

    new_id = add_faq(
        keywords=data["keywords"],
        question={
            "ru": data["question_ru"],
            "en": data["question_ru"],
            "zh": data["question_ru"],
        },
        answer={
            "ru": data["answer_ru"],
            "en": data["answer_en"],
            "zh": data["answer_zh"],
        },
    )
    await state.clear()
    await message.answer(
        f"FAQ #{new_id} добавлен!\n\n"
        f"Ключевые слова: {', '.join(data['keywords'])}\n"
        f"Вопрос: {data['question_ru']}\n\n"
        f"🇷🇺 {data['answer_ru']}\n\n"
        f"🇬🇧 {data['answer_en']}\n\n"
        f"🇨🇳 {data['answer_zh']}"
    )