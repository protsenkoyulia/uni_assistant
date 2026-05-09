import os
import redis
import json
from pathlib import Path
from core.config import REDIS_URL


r = redis.from_url(REDIS_URL, decode_responses=True)


def log_request(question: str, answer: str, lang: str):
    entry = json.dumps({
        "question": question[:300],
        "answer": answer[:300],
        "lang": lang,
        "ts": str(__import__("datetime").datetime.now()),
    }, ensure_ascii=False)
    r.lpush("stats:requests", entry)
    r.ltrim("stats:requests", 0, 999) # последние 1000 запросов
    r.incr(f"stats:lang:{lang}")
    r.incr("stats:total")


def get_stats() -> dict:
    total = int(r.get("stats:total") or 0)
    lang_ru = int(r.get("stats:lang:ru") or 0)
    lang_zh = int(r.get("stats:lang:zh") or 0)
    lang_en = int(r.get("stats:lang:en") or 0)

    recent_raw = r.lrange("stats:requests", 0, 19)
    recent = [json.loads(x) for x in recent_raw]

    return {
        "total": total,
        "by_lang": {"ru": lang_ru, "zh": lang_zh, "en": lang_en},
        "recent": recent,
    }


def list_knowledge_files(data_dir: str = "./data/knowledge_base") -> list[dict]:
    path = Path(data_dir)
    if not path.exists():
        return []
    files = []
    for f in sorted(path.glob("*.docx")):
        stat = f.stat()
        files.append({
            "name": f.name,
            "size_kb": round(stat.st_size / 1024, 1),
            "modified": str(__import__("datetime").datetime.fromtimestamp(stat.st_mtime))[:16],
        })
    return files


def delete_knowledge_file(filename: str, data_dir: str = "./data/knowledge_base") -> bool:
    path = Path(data_dir) / filename
    if path.exists() and path.suffix == ".docx":
        path.unlink()
        return True
    return False


def rebuild_needed() -> bool:
    vector_path = Path("./vector_db/KnowledgeBase")
    return not vector_path.exists()