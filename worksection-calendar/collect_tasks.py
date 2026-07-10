#!/usr/bin/env python3
"""
Тягне задачі, призначені на вас, з Worksection (REST API) і зберігає їх
у tasks.json поруч із ws-calendar.html.

Налаштування — у файлі .env (скопіюйте з .env.example):
  WS_SUBDOMAIN   - субдомен акаунту, напр. eco9830 (з https://eco9830.worksection.com)
  WS_APIKEY      - адміністративний API-ключ (Worksection -> Налаштування -> API)
  WS_USER_EMAIL  - ваш email у Worksection, задачі якого показувати

Нічого нікуди не відправляється, крім одного HTTPS-запиту напряму до
*.worksection.com. Жодних третіх сервісів.
"""
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV_FILE = HERE / ".env"
OUT_FILE = HERE / "tasks.json"


def load_env(path):
    env = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def ws_request(subdomain, apikey, params):
    """action=get_all_tasks запит з hash-авторизацією Worksection API."""
    query = urllib.parse.urlencode(params)
    digest = hashlib.md5((query + apikey).encode("utf-8")).hexdigest()
    url = f"https://{subdomain}.worksection.com/api/admin/v2/?{query}&hash={digest}"
    req = urllib.request.Request(url, headers={"User-Agent": "ws-calendar-collector"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def map_priority(raw):
    """Мапінг на high/normal/low. У цьому акаунті пріоритет 1 - типовий
    (стандартний), а вищі значення (3, 4...) - явно підвищена важливість."""
    try:
        p = int(raw)
    except (TypeError, ValueError):
        return "normal"
    if p <= 0:
        return "low"
    if p == 1:
        return "normal"
    return "high"


def map_status(raw):
    if raw in ("active", "done", "paused"):
        return raw
    return "active"


def trim_date(s):
    if not s:
        return None
    return s[:10]


def transform(raw_tasks):
    tasks = []
    for t in raw_tasks:
        date_end = trim_date(t.get("date_end"))
        if not date_end:
            continue  # без дедлайну немає що показувати в календарі
        date_start = (
            trim_date(t.get("date_start"))
            or trim_date(t.get("date_added"))
            or date_end
        )
        if date_start > date_end:
            date_start = date_end
        project = t.get("project") or {}
        tasks.append(
            {
                "id": f"WS-{t['id']}",
                "name": t.get("name") or t.get("title") or "(без назви)",
                "project": project.get("name", "Без проєкту"),
                "status": map_status(t.get("status")),
                "priority": map_priority(t.get("priority")),
                "assignee": "Ви",
                "dateStart": date_start,
                "dateEnd": date_end,
                "url": t.get("page") and f"https://{t['_subdomain']}.worksection.com{t['page']}",
            }
        )
    tasks.sort(key=lambda x: x["dateEnd"])
    return tasks


def main():
    env = {**load_env(ENV_FILE), **os.environ}
    subdomain = env.get("WS_SUBDOMAIN")
    apikey = env.get("WS_APIKEY")
    user_email = env.get("WS_USER_EMAIL")

    missing = [k for k, v in {
        "WS_SUBDOMAIN": subdomain, "WS_APIKEY": apikey, "WS_USER_EMAIL": user_email,
    }.items() if not v]
    if missing:
        print(f"Немає значень у .env: {', '.join(missing)}. Скопіюйте .env.example -> .env і заповніть.", file=sys.stderr)
        sys.exit(1)

    data = ws_request(subdomain, apikey, {
        "action": "get_all_tasks",
        "email_user_to": user_email,
    })

    if data.get("status") != "ok":
        print(f"Worksection API повернув помилку: {data}", file=sys.stderr)
        sys.exit(1)

    raw_tasks = data.get("data", [])
    for t in raw_tasks:
        t["_subdomain"] = subdomain

    tasks = transform(raw_tasks)
    OUT_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Записано {len(tasks)} задач у {OUT_FILE}")


if __name__ == "__main__":
    main()
