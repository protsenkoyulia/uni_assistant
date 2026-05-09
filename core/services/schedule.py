# services/schedule.py
import httpx
from typing import Union, Optional

BASE_URL = "https://digital.etu.ru/api/schedule/objects/publicated"


async def get_schedule(group_id: Union[str, int], week: Optional[int] = None) -> str:
    params = {
        "groups": str(group_id),
        "withSubjectCode": "true",
        "withURL": "true"
    }

    if week is not None:
        params["week"] = week

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(BASE_URL, params=params)
            print(f"API Status: {response.status_code} | Group: {group_id}")

            data = response.json()

            if not data or not isinstance(data, list) or len(data) == 0:
                return f"Расписание для группы **{group_id}** пока не опубликовано."

            return format_schedule(data, group_id)

    except Exception as e:
        print(f"Ошибка при получении расписания: {e}")
        return "Не удалось загрузить расписание. Попробуйте позже."


def format_schedule(data: list, group_id: str) -> str:
    lines = [f"Группа: {group_id}\n"]

    for group_item in data:
        if not isinstance(group_item, dict):
            continue

        schedule_objects = group_item.get("scheduleObjects") or []
        if not schedule_objects:
            continue

        days: dict = {}

        for obj in schedule_objects:
            if not isinstance(obj, dict):
                continue

            lesson = obj.get("lesson") or {}
            subject = lesson.get("subject") or {}
            teacher = lesson.get("teacher") or {}
            aud_res = lesson.get("auditoriumReservation") or {}
            res_time = aud_res.get("reservationTime") or {}

            day_code = res_time.get("weekDay") or "UNKNOWN"

            subj_type = (subject.get("subjectType") or "—").strip()
            subj_title = (subject.get("title") or "—").strip()
            teacher_name = (teacher.get("initials") or "—").strip()
            room = (aud_res.get("auditoriumNumber") or "—").strip()

            lesson_key = (day_code, subj_type, subj_title, teacher_name, room)

            entry = f"    {subj_type} — {subj_title}\n       {teacher_name}\n       Аудитория: {room}\n"

            if day_code not in days:
                days[day_code] = {}
            days[day_code][lesson_key] = entry

        day_order = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        day_names = {
            "MON": "Понедельник",
            "TUE": "Вторник",
            "WED": "Среда",
            "THU": "Четверг",
            "FRI": "Пятница",
            "SAT": "Суббота",
            "SUN": "Воскресенье"
        }

        for day_code in day_order:
            if day_code in days and days[day_code]:
                lines.append(f"📍 {day_names.get(day_code, day_code)}:")
                for entry in days[day_code].values():
                    lines.append(entry)
                lines.append("")

    if len(lines) < 3:
        return f"Расписание для группы {group_id} пока пустое или не опубликовано."

    return "\n".join(lines)
