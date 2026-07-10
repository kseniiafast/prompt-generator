# Календар задач Worksection (локально, без хмари)

Все працює і зберігається лише на вашому комп'ютері. Єдина мережева взаємодія —
прямий запит до `*.worksection.com`, коли `collect_tasks.py` оновлює `tasks.json`.
Ніяких Google Calendar чи інших сторонніх сервісів.

## Файли

- `ws-calendar.html` — інтерфейс календаря (місяць / список, фільтри, деталі задачі).
- `tasks.json` — дані задач, які читає календар. Генерується скриптом, у git не потрапляє.
- `collect_tasks.py` — скрипт-збирач: тягне ваші задачі з Worksection REST API і пише `tasks.json`.
- `.env` — ваші облікові дані (субдомен, ключ, email). У git не потрапляє.

## Крок 1. Налаштування

```bash
cd worksection-calendar
cp .env.example .env
```

Відкрийте `.env` і впишіть:

- `WS_SUBDOMAIN` — субдомен акаунту (для вас це вже `eco9830`, з `https://eco9830.worksection.com`).
- `WS_APIKEY` — адміністративний API-ключ. Знайти: Worksection → аватар/налаштування акаунту → **API**.
  Ключ бачить лише власник акаунту.
- `WS_USER_EMAIL` — ваш email у Worksection (вже підставлено: `kseniia.fast@ecofactortech.com`).

## Крок 2. Перше збирання задач

```bash
python3 collect_tasks.py
```

Має з'явитися `tasks.json` і повідомлення `Записано N задач`.

## Крок 3. Запустити календар

Відкриття файлу напряму (`file://...`) не завжди дозволяє `fetch()` читати `tasks.json`
(блокується браузером). Тому запустіть маленький локальний сервер:

```bash
python3 -m http.server 8000
```

і відкрийте у браузері **http://localhost:8000/ws-calendar.html**.

Щоб зупинити сервер — `Ctrl+C` у тому ж терміналі.

## Крок 4. Автооновлення за розкладом

Скрипт треба перезапускати періодично, щоб `tasks.json` не застарів. Команда для
запуску завжди одна:

```bash
cd /повний/шлях/до/worksection-calendar && python3 collect_tasks.py
```

Спосіб додати це у розклад залежить від вашої ОС — інструкції для macOS/Linux (cron)
і Windows (Task Scheduler) дивіться нижче в основному чаті, підлаштовані під ваш шлях.

## Формат задачі в tasks.json

```json
{
  "id": "WS-17734319",
  "name": "Назва задачі",
  "project": "Назва проєкту",
  "status": "active",
  "priority": "normal",
  "assignee": "Ви",
  "dateStart": "2026-07-08",
  "dateEnd": "2026-07-10",
  "url": "https://eco9830.worksection.com/project/.../..."
}
```

`status`: `active` / `done` / `paused`. `priority`: `high` / `normal` / `low`
(у Worksection числове значення 1 вважається типовим і мапиться на `normal`,
вище — на `high`; за потреби відкоригуйте `map_priority()` у `collect_tasks.py`).
