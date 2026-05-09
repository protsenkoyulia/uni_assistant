import redis
import json
from core.config import REDIS_URL

r = redis.from_url(REDIS_URL, decode_responses=True)
CONTEXT_TTL = 3600  # 1 час


def get_user_context(id: int) -> list:
    data = r.get(f'context:{id}')
    return json.loads(data) if data else []


def save_user_context(id: int, context: list):
    r.setex(f'context:{id}', CONTEXT_TTL, json.dumps(context,
                                                     ensure_ascii=False))


def get_user_language(id: int) -> str:
    return r.get(f'lang:{id}') or 'en'


def set_user_language(id: int, lang: str):
    r.set(f'lang:{id}', lang)

def get_user_group(user_id: int) -> str:
    return r.get(f'group:{user_id}')


def set_user_group(user_id: int, group_id: str):
    user_id = str(user_id)
    group_id = group_id.strip()
    r.set(f'group:{user_id}', group_id, ex=60*60*24*30)


def get_cached_schedule(group_id: str) -> str:
    return r.get(f'schedule:{group_id}')

def cache_schedule(group_id: str, schedule_text: str, ttl_seconds: int = 43200):
    r.setex(f'schedule:{group_id}', ttl_seconds, schedule_text)

def clear_user_context(user_id: int):
    r.delete(f'context:{user_id}')
    r.delete(f'lang:{user_id}')
    r.delete(f'group:{user_id}')
    r.delete(f'schedule:{user_id}')
    print(f"Контекст очищен для пользователя {user_id}")
