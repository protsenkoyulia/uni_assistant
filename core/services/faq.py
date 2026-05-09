import json
from pathlib import Path
from typing import Optional

FAQ_PATH = Path("./data/faq.json")


def load_faq() -> list[dict]:
    if not FAQ_PATH.exists():
        return []
    with open(FAQ_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_faq(items: list[dict]):
    FAQ_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FAQ_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def search_faq(query: str, lang: str = "ru") -> Optional[dict]:
    query_lower = query.lower()
    items = load_faq()

    best_match = None
    best_score = 0

    for item in items:
        keywords = [k.lower() for k in item.get("keywords", [])]
        score = sum(1 for kw in keywords if kw in query_lower)

        exact = any(kw in query_lower for kw in keywords if len(kw.split()) > 1)
        if (score >= 2 or exact) and score > best_score:
            best_score = score
            best_match = item

    if not best_match:
        return None
    
    return {
        "question": best_match["question"].get(lang, best_match["question"].get("ru", "")),
        "answer": best_match["answer"].get(lang, best_match["answer"].get("ru", "")),
        "id": best_match["id"],
    }


def get_all_faq(lang: str = "ru") -> list[dict]:
    items = load_faq()
    return [
        {
            "id": item["id"],
            "question": item["question"].get(lang, item["question"].get("ru", "")),
            "answer": item["answer"].get(lang, item["answer"].get("ru", "")),
        }
        for item in items
    ]


def add_faq(keywords: list[str], question: dict, answer: dict) -> int:
    items = load_faq()
    new_id = max((i["id"] for i in items), default=0) + 1
    items.append({
        "id": new_id,
        "keywords": keywords,
        "question": question,
        "answer": answer,
    })
    save_faq(items)
    return new_id


def delete_faq(faq_id: int) -> bool:
    items = load_faq()
    new_items = [i for i in items if i["id"] != faq_id]
    if len(new_items) == len(items):
        return False
    save_faq(new_items)
    return True
