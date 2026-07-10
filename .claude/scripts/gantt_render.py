#!/usr/bin/env python3
"""Render a Worksection task list as a horizontal Gantt/urgency SVG chart.

Usage:
    python3 gantt_render.py input.json output.svg [output.png]

Input JSON schema:
{
  "today": "YYYY-MM-DD",
  "period_label": "human-readable period description (Ukrainian)",
  "tasks": [
    {
      "id": 123,
      "title": "...",
      "deadline": "YYYY-MM-DD",       // required for a bar to be drawn
      "shadow": false,                 // true => "@" prefix, shadow-task styling
      "deadline_from_comment": false   // true => deadline came from a comment, not date_end
    }
  ],
  "no_deadline": [ {"id": 456, "title": "...", "shadow": false} ]
}

Tasks are sorted by deadline ascending (nearest first) regardless of input order.
Color rule: overdue -> critical fill + thick red outline; <=3 days -> critical;
4-10 days -> warning; >10 days -> good. All from the dataviz skill's status palette.
"""
import json
import sys
import datetime as dt

# --- dataviz skill status palette (light surface) ---
COLOR_CRITICAL = "#d03b3b"
COLOR_WARNING = "#fab219"
COLOR_GOOD = "#0ca30c"
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"


def urgency_color(days_left):
    if days_left < 0:
        return COLOR_CRITICAL
    if days_left <= 3:
        return COLOR_CRITICAL
    if days_left <= 10:
        return COLOR_WARNING
    return COLOR_GOOD


def esc(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main():
    in_path, out_svg = sys.argv[1], sys.argv[2]
    out_png = sys.argv[3] if len(sys.argv) > 3 else None

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

    # --- layout ---
    row_h = 34
    label_w = 430
    chart_left = label_w + 20
    chart_right_margin = 60
    top_margin = 90
    bottom_legend_h = 90
    n_rows = max(len(tasks), 1)
    chart_w = 900
    width = chart_left + chart_w + chart_right_margin
    height = top_margin + n_rows * row_h + bottom_legend_h + (
        26 * len(no_deadline) + (40 if no_deadline else 0)
    )

    def x_for(days_from_today):
        return chart_left + (days_from_today / span_days) * chart_w

    svg = []
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}">'
    )
    svg.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{SURFACE}"/>')

    # Title
    svg.append(
        f'<text x="24" y="36" font-size="22" font-weight="700" fill="{INK_PRIMARY}">'
        f"Гант — задачі Ксенії Фаст (Worksection)</text>"
    )
    subtitle = f"Сьогодні: {today.isoformat()}"
    if period_label:
        subtitle += f"  ·  Період: {esc(period_label)}"
    svg.append(f'<text x="24" y="58" font-size="13" fill="{INK_SECONDARY}">{subtitle}</text>')

    # Date axis ticks (weekly-ish, at most ~8 ticks)
    tick_step = max(1, span_days // 8)
    d = 0
    while d <= span_days:
        tx = x_for(d)
        tick_date = today + dt.timedelta(days=d)
        svg.append(
            f'<line x1="{tx:.1f}" y1="{top_margin - 10}" x2="{tx:.1f}" '
            f'y2="{top_margin + n_rows * row_h}" stroke="{GRIDLINE}" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="{tx:.1f}" y="{top_margin - 16}" font-size="11" fill="{INK_MUTED}" '
            f'text-anchor="middle">{tick_date.strftime("%d.%m")}</text>'
        )
        d += tick_step

    # Rows
    for i, t in enumerate(tasks):
        y = top_margin + i * row_h
        bar_y = y + 6
        bar_h = row_h - 14

        label = ("@ " if t["shadow"] else "") + t["title"]
        if len(label) > 62:
            cut = label[:56].rsplit(" ", 1)[0]
            label = cut + "..."
        label_color = "#9a3ab0" if t["shadow"] else INK_PRIMARY

        svg.append(
            f'<text x="16" y="{y + row_h / 2 + 4:.1f}" font-size="13" fill="{label_color}">'
            f"{esc(label)}</text>"
        )

        x_start = x_for(0)
        x_end = x_for(max(t["days_left"], 0)) if not t["overdue"] else x_for(0)
        bar_x = min(x_start, x_end)
        bar_w = max(abs(x_end - x_start), 4)
        color = urgency_color(t["days_left"])

        stroke = COLOR_CRITICAL if t["overdue"] else "none"
        stroke_w = 3 if t["overdue"] else 0
        svg.append(
            f'<rect x="{bar_x:.1f}" y="{bar_y}" width="{bar_w:.1f}" height="{bar_h}" rx="4" '
            f'fill="{color}" stroke="{stroke}" stroke-width="{stroke_w}"/>'
        )

        dl_label = t["deadline"].strftime("%d.%m")
        if t["overdue"]:
            dl_label += f" (протерміновано на {abs(t['days_left'])} дн.)"
        elif t["from_comment"]:
            dl_label += " (з коментаря)"
        label_x = bar_x + bar_w + 8
        svg.append(
            f'<text x="{label_x:.1f}" y="{y + row_h / 2 + 4:.1f}" font-size="11" '
            f'fill="{INK_SECONDARY}">{dl_label}</text>'
        )

    # Today line
    today_x = x_for(0)
    svg.append(
        f'<line x1="{today_x:.1f}" y1="{top_margin - 10}" x2="{today_x:.1f}" '
        f'y2="{top_margin + n_rows * row_h + 10}" stroke="{INK_PRIMARY}" '
        f'stroke-width="2" stroke-dasharray="5,3"/>'
    )
    svg.append(
        f'<text x="{today_x:.1f}" y="{top_margin + n_rows * row_h + 26}" font-size="11" '
        f'font-weight="600" fill="{INK_PRIMARY}" text-anchor="middle">Сьогодні</text>'
    )

    # Legend
    legend_y = top_margin + n_rows * row_h + 46
    legend_items = [
        (COLOR_CRITICAL, "≤ 3 днів — терміново"),
        (COLOR_WARNING, "4–10 днів — скоро"),
        (COLOR_GOOD, "> 10 днів — є час"),
    ]
    lx = 24
    for color, text in legend_items:
        svg.append(f'<rect x="{lx}" y="{legend_y}" width="16" height="16" rx="3" fill="{color}"/>')
        svg.append(
            f'<text x="{lx + 22}" y="{legend_y + 13}" font-size="12" fill="{INK_SECONDARY}">{text}</text>'
        )
        lx += 22 + 8 + len(text) * 6.6 + 24

    legend_y2 = legend_y + 26
    svg.append(
        f'<rect x="24" y="{legend_y2}" width="16" height="16" rx="3" fill="{COLOR_CRITICAL}" '
        f'stroke="{COLOR_CRITICAL}" stroke-width="3"/>'
    )
    svg.append(
        f'<text x="46" y="{legend_y2 + 13}" font-size="12" fill="{INK_SECONDARY}">'
        f"протерміновано (червона рамка)</text>"
    )
    svg.append(
        f'<line x1="300" y1="{legend_y2}" x2="300" y2="{legend_y2 + 16}" stroke="{INK_PRIMARY}" '
        f'stroke-width="2" stroke-dasharray="5,3"/>'
    )
    svg.append(
        f'<text x="310" y="{legend_y2 + 13}" font-size="12" fill="{INK_SECONDARY}">сьогодні</text>'
    )
    svg.append(
        f'<text x="400" y="{legend_y2 + 13}" font-size="12" font-weight="700" fill="#9a3ab0">@</text>'
    )
    svg.append(
        f'<text x="414" y="{legend_y2 + 13}" font-size="12" fill="{INK_SECONDARY}">'
        f"— тебе тегнули в коментарях (тіньова задача)</text>"
    )

    # No-deadline list
    if no_deadline:
        ny = legend_y2 + 50
        svg.append(
            f'<text x="24" y="{ny}" font-size="14" font-weight="700" fill="{INK_PRIMARY}">'
            f"Без дедлайну:</text>"
        )
        for j, t in enumerate(no_deadline):
            label = ("@ " if t.get("shadow") else "") + t["title"]
            svg.append(
                f'<text x="24" y="{ny + 22 + j * 22}" font-size="12" fill="{INK_SECONDARY}">'
                f"• {esc(label)}</text>"
            )

    svg.append("</svg>")
    svg_content = "\n".join(svg)

    with open(out_svg, "w", encoding="utf-8") as f:
        f.write(svg_content)

    if out_png:
        import cairosvg

        cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=out_png, scale=2)

    print(f"Rows: {len(tasks)}, no-deadline: {len(no_deadline)}, span: {span_days}d -> {out_svg}")


if __name__ == "__main__":
    main()
