import redis
import json
from config import REDIS_URL

r = redis.from_url(REDIS_URL, decode_responses=True)
CONTEXT_TTL = 3600  # 1 час


def get_user_context(vk_id: int) -> list:
    data = r.get(f'context:{vk_id}')
    return json.loads(data) if data else []


def save_user_context(vk_id: int, context: list):
    r.setex(f'context:{vk_id}', CONTEXT_TTL, json.dumps(context,
                                                        ensure_ascii=False))


def get_user_language(vk_id: int) -> str:
    return r.get(f'lang:{vk_id}') or 'ru'


def set_user_language(vk_id: int, lang: str):
    r.set(f'lang:{vk_id}', lang)


def clear_user_context(user_id: int):
    r.delete(f'context:{user_id}')
    r.delete(f'lang:{user_id}')
    print(f"Контекст очищен для пользователя {user_id}")