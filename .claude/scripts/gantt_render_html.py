#!/usr/bin/env python3
"""Render a Worksection task list as a clickable HTML Gantt page (for the Artifact tool).

Usage:
    python3 gantt_render_html.py input.json output.html

Input JSON: same schema as gantt_render.py, plus a required "url" field per
task (and per no_deadline entry) pointing at the Worksection task page.
Every row is a real <a href> to that URL, so the rendered artifact is
clickable straight from the session.
"""
import base64
import json
import os
import sys
import datetime as dt

LABEL_W = 300
DATE_W = 150
ROW_H = 44
TOP_PAD = 100
CHART_PAD_BOTTOM = 34
DAY_W = 30
MIN_TRACK_W = 820

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _svg(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def esc(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def urgency_class(days_left):
    if days_left <= 3:
        return "critical"
    if days_left <= 10:
        return "warning"
    return "good"


def main():
    in_path, out_html = sys.argv[1], sys.argv[2]
    with open(in_path, encoding="utf-8") as f:
        data = json.load(f)

    today = dt.date.fromisoformat(data["today"])
    period_label = data.get("period_label", "")
    tasks_in = data.get("tasks", [])
    no_deadline = data.get("no_deadline", [])

    tasks = []
    for t in tasks_in:
        deadline = dt.date.fromisoformat(t["deadline"])
        days_left = (deadline - today).days
        tasks.append(
            {
                "id": t["id"],
                "title": t["title"],
                "url": t["url"],
                "deadline": deadline,
                "days_left": days_left,
                "shadow": t.get("shadow", False),
                "from_comment": t.get("deadline_from_comment", False),
                "overdue": days_left < 0,
            }
        )
    tasks.sort(key=lambda t: t["deadline"])

    max_deadline = max((t["deadline"] for t in tasks), default=today)
    span_days = max((max_deadline - today).days, 1)
    TRACK_W = max(MIN_TRACK_W, (span_days + 1) * DAY_W)

    def px_for(days_from_today):
        return (days_from_today / span_days) * TRACK_W

    chart_h = TOP_PAD + len(tasks) * ROW_H + CHART_PAD_BOTTOM
    total_w = LABEL_W + TRACK_W + DATE_W + 40

    # --- gridlines / today line / date ticks — every single day ---
    ticks_html = []
    d = 0
    while d <= span_days:
        x = LABEL_W + px_for(d)
        tick_date = today + dt.timedelta(days=d)
        ticks_html.append(
            f'<div class="gridline" style="left:{x:.1f}px;top:{TOP_PAD - 8}px;'
            f'height:{len(tasks) * ROW_H + 8}px;"></div>'
            f'<div class="tick-label" style="left:{x:.1f}px;top:{TOP_PAD - 20}px;">'
            f"{tick_date.strftime('%d.%m')}</div>"
        )
        d += 1
    today_x = LABEL_W
    ticks_html.append(
        f'<div class="today-line" style="left:{today_x:.1f}px;top:{TOP_PAD - 8}px;'
        f'height:{len(tasks) * ROW_H + 20}px;"></div>'
        f'<div class="today-label" style="left:{today_x:.1f}px;top:{TOP_PAD + len(tasks) * ROW_H + 4}px;">'
        f"Сьогодні</div>"
    )

    # --- rows ---
    rows_html = []
    for i, t in enumerate(tasks):
        y = TOP_PAD + i * ROW_H
        bar_x = 0 if t["overdue"] else px_for(0)
        bar_w = max(px_for(max(t["days_left"], 0)), 5) if not t["overdue"] else 6
        cls = urgency_class(t["days_left"])
        overdue_cls = " overdue" if t["overdue"] else ""
        shadow_cls = " shadow" if t["shadow"] else ""

        dl_label = t["deadline"].strftime("%d.%m")
        if t["overdue"]:
            dl_label += f" · протерміновано на {abs(t['days_left'])} дн."
        elif t["from_comment"]:
            dl_label += " · з коментаря"

        label = ("@ " if t["shadow"] else "") + t["title"]

        rows_html.append(
            f'<a class="row{shadow_cls}" style="top:{y}px;height:{ROW_H}px;" '
            f'href="{esc(t["url"])}" target="_blank" rel="noopener" '
            f'title="Відкрити задачу #{t["id"]} у Worksection">'
            f'<span class="row-label" style="width:{LABEL_W}px">{esc(label)}</span>'
            f'<span class="track" style="width:{TRACK_W}px">'
            f'<span class="bar {cls}{overdue_cls}" style="left:{bar_x:.1f}px;width:{bar_w:.1f}px"></span>'
            f"</span>"
            f'<span class="row-date">{dl_label}</span>'
            f'<span class="ext-icon" aria-hidden="true">&#8599;</span>'
            f"</a>"
        )

    # --- no-deadline list ---
    nodl_html = ""
    if no_deadline:
        items = "".join(
            f'<li><a href="{esc(t["url"])}" target="_blank" rel="noopener">'
            f'{"@ " if t.get("shadow") else ""}{esc(t["title"])}'
            f'<span class="ext-icon" aria-hidden="true">&#8599;</span></a></li>'
            for t in no_deadline
        )
        nodl_html = f'<section class="no-deadline"><h2>Без дедлайну</h2><ul>{items}</ul></section>'

    font_regular_b64 = _b64(os.path.join(ASSETS_DIR, "fonts", "Ruberoid-Regular.woff2"))
    font_bold_b64 = _b64(os.path.join(ASSETS_DIR, "fonts", "Ruberoid-Bold.woff2"))
    logo_green = _svg(os.path.join(ASSETS_DIR, "logos", "ecofactor-green-horizontal.svg"))
    logo_white = _svg(os.path.join(ASSETS_DIR, "logos", "ecofactor-white-horizontal.svg"))

    html = f"""<title>Гант — задачі Worksection</title>
<style>
  @font-face {{
    font-family: 'Ruberoid';
    src: url('data:font/woff2;base64,{font_regular_b64}') format('woff2');
    font-weight: 400;
    font-style: normal;
    font-display: swap;
  }}
  @font-face {{
    font-family: 'Ruberoid';
    src: url('data:font/woff2;base64,{font_bold_b64}') format('woff2');
    font-weight: 700;
    font-style: normal;
    font-display: swap;
  }}
  :root {{
    --surface-page: #F1F3F5;
    --surface-card: #ffffff;
    --text-primary: #3A3A3A;
    --text-secondary: #525252;
    --text-muted: #7B7F84;
    --border: #D9DBDE;
    --accent: #23A859;
    --accent-soft: rgba(35,168,89,0.08);
    --critical: #d03b3b;
    --warning-fill: #f7ae1f;
    --warning-text: #9c6600;
    --good: #0ca30c;
    --shadow-text: #3577D8;
    --row-hover: rgba(35,168,89,0.06);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --surface-page: #1F1F1F;
      --surface-card: #262626;
      --text-primary: #ffffff;
      --text-secondary: rgba(255,255,255,0.72);
      --text-muted: rgba(255,255,255,0.5);
      --border: rgba(255,255,255,0.14);
      --accent: #3AF185;
      --accent-soft: rgba(58,241,133,0.14);
      --critical: #e2645f;
      --warning-fill: #d99a1c;
      --warning-text: #f0c674;
      --good: #3fc463;
      --shadow-text: #6ea3ea;
      --row-hover: rgba(58,241,133,0.10);
    }}
  }}
  :root[data-theme="dark"] {{
    --surface-page: #1F1F1F;
    --surface-card: #262626;
    --text-primary: #ffffff;
    --text-secondary: rgba(255,255,255,0.72);
    --text-muted: rgba(255,255,255,0.5);
    --border: rgba(255,255,255,0.14);
    --accent: #3AF185;
    --accent-soft: rgba(58,241,133,0.14);
    --critical: #e2645f;
    --warning-fill: #d99a1c;
    --warning-text: #f0c674;
    --good: #3fc463;
    --shadow-text: #6ea3ea;
    --row-hover: rgba(58,241,133,0.10);
  }}
  :root[data-theme="light"] {{
    --surface-page: #F1F3F5;
    --surface-card: #ffffff;
    --text-primary: #3A3A3A;
    --text-secondary: #525252;
    --text-muted: #7B7F84;
    --border: #D9DBDE;
    --accent: #23A859;
    --accent-soft: rgba(35,168,89,0.08);
    --critical: #d03b3b;
    --warning-fill: #f7ae1f;
    --warning-text: #9c6600;
    --good: #0ca30c;
    --shadow-text: #3577D8;
    --row-hover: rgba(35,168,89,0.06);
  }}
  * {{ box-sizing: border-box; }}
  body {{ background: var(--surface-page); }}
  .page {{
    font-family: 'Ruberoid', 'Open Sans', -apple-system, "Segoe UI", sans-serif;
    color: var(--text-primary);
    max-width: 1400px;
    margin: 0 auto;
    padding: 28px 20px 40px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }}
  .logo {{ margin-bottom: 12px; }}
  .logo svg {{ height: 28px; width: auto; display: block; }}
  .logo-dark {{ display: none; }}
  @media (prefers-color-scheme: dark) {{
    .logo-light {{ display: none; }}
    .logo-dark {{ display: block; }}
  }}
  :root[data-theme="dark"] .logo-light {{ display: none; }}
  :root[data-theme="dark"] .logo-dark {{ display: block; }}
  :root[data-theme="light"] .logo-light {{ display: block; }}
  :root[data-theme="light"] .logo-dark {{ display: none; }}
  .head h1 {{
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin: 0 0 4px;
    text-wrap: balance;
  }}
  .head .meta {{
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin: 0;
  }}
  .scroll-wrap {{
    overflow-x: auto;
    background: var(--surface-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 4px 8px;
  }}
  .chart {{ position: relative; }}
  .gridline {{
    position: absolute;
    width: 1px;
    background: var(--border);
  }}
  .tick-label {{
    position: absolute;
    font-size: 10px;
    color: var(--text-muted);
    transform: rotate(-60deg);
    transform-origin: left center;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }}
  .today-line {{
    position: absolute;
    width: 2px;
    background: var(--accent);
  }}
  .today-label {{
    position: absolute;
    font-size: 11px;
    font-weight: 600;
    color: var(--accent);
    transform: translateX(-50%);
    white-space: nowrap;
  }}
  .row {{
    position: absolute;
    left: 0;
    right: 0;
    display: flex;
    align-items: center;
    text-decoration: none;
    color: inherit;
    border-radius: 8px;
    padding: 0 8px;
    gap: 10px;
  }}
  .row:hover, .row:focus-visible {{
    background: var(--row-hover);
    outline: none;
  }}
  .row:focus-visible {{
    box-shadow: 0 0 0 2px var(--accent);
  }}
  .row-label {{
    font-size: 13px;
    flex: 0 0 auto;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  .row.shadow .row-label {{ color: var(--shadow-text); }}
  .track {{ position: relative; height: 100%; flex: 0 0 auto; }}
  .bar {{
    position: absolute;
    top: 9px;
    height: 26px;
    border-radius: 6px;
  }}
  .bar.critical {{ background: var(--critical); }}
  .bar.warning {{ background: var(--warning-fill); }}
  .bar.good {{ background: var(--good); }}
  .bar.overdue {{ box-shadow: 0 0 0 3px var(--critical) inset; }}
  .row-date {{
    font-size: 12px;
    color: var(--text-secondary);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }}
  .ext-icon {{
    font-size: 13px;
    color: var(--text-muted);
    flex: 0 0 auto;
  }}
  .legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 18px;
    align-items: center;
    font-size: 12.5px;
    color: var(--text-secondary);
    padding: 4px 4px 0;
  }}
  .legend .item {{ display: flex; align-items: center; gap: 7px; }}
  .swatch {{ width: 14px; height: 14px; border-radius: 4px; display: inline-block; }}
  .swatch.critical {{ background: var(--critical); }}
  .swatch.warning {{ background: var(--warning-fill); }}
  .swatch.good {{ background: var(--good); }}
  .swatch.overdue {{ background: var(--critical); box-shadow: 0 0 0 3px var(--critical) inset; }}
  .legend .today-dot {{
    width: 2px; height: 14px; background: var(--accent); display: inline-block;
  }}
  .legend .at {{ color: var(--shadow-text); font-weight: 700; }}
  .no-deadline h2 {{
    font-size: 1rem;
    margin: 0 0 8px;
  }}
  .no-deadline ul {{
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  .no-deadline a {{
    color: var(--text-primary);
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 13.5px;
    padding: 4px 8px;
    margin: 0 -8px;
    border-radius: 6px;
  }}
  .no-deadline a:hover {{ background: var(--row-hover); }}
</style>
<div class="page">
  <header class="head">
    <div class="logo logo-light">{logo_green}</div>
    <div class="logo logo-dark">{logo_white}</div>
    <h1>Гант — задачі Ксенії Фаст (Worksection)</h1>
    <p class="meta">Сьогодні: {today.isoformat()} · Період: {esc(period_label)} · клікни на задачу, щоб відкрити її у Worksection</p>
  </header>

  <div class="scroll-wrap">
    <div class="chart" style="width:{total_w}px;height:{chart_h}px;">
      {''.join(ticks_html)}
      {''.join(rows_html)}
    </div>
  </div>

  <div class="legend">
    <span class="item"><span class="swatch critical"></span>≤ 3 днів — терміново</span>
    <span class="item"><span class="swatch warning"></span>4–10 днів — скоро</span>
    <span class="item"><span class="swatch good"></span>&gt; 10 днів — є час</span>
    <span class="item"><span class="swatch overdue"></span>протерміновано (рамка)</span>
    <span class="item"><span class="today-dot"></span>сьогодні</span>
    <span class="item"><span class="at">@</span> тебе тегнули в коментарях (тіньова задача)</span>
  </div>

  {nodl_html}
</div>
"""

    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Rows: {len(tasks)}, no-deadline: {len(no_deadline)}, span: {span_days}d -> {out_html}")


if __name__ == "__main__":
    main()
