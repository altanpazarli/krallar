"""Render the standings as a single static, mobile-friendly HTML page.

Phones get one card per team (joker badges inline); wider screens get a table.
The phone/desktop switch is a CSS media query. The only script turns the update time
into the visitor's local time; without it the page shows Turkish time (TSİ).
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape

from .compute import CHIPS, EXCLUDED_UNTIL_GW

ACCENT = "#0B6E4F"

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#F3F4F1;color:#12161C;font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-text-size-adjust:100%}
.cond{font-family:"Barlow Condensed","Arial Narrow",sans-serif}
header{background:#12161C;color:#fff;padding:28px 20px 22px}
.head{max-width:1080px;margin:0 auto;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:14px}
.kicker{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:#B9C0CA}
h1{margin:4px 0 0;font-weight:700;font-size:40px;line-height:1}
.pills{display:flex;flex-wrap:wrap;gap:8px}
.pill{font-size:12px;font-weight:500;padding:5px 10px;border-radius:999px;background:#262C35;color:#DDE2E8}
.pill.accent{background:ACCENT;color:#fff;font-weight:600}
main{max-width:1080px;margin:0 auto;padding:18px 12px 32px;display:flex;flex-direction:column;gap:16px}
.bar{display:flex;justify-content:space-between;align-items:baseline;padding:0 8px}
h2{margin:0;font-size:22px;font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.muted{color:#5A6270;font-size:12px}
.b{display:inline-block;font-size:11px;font-weight:600;line-height:1;padding:5px 7px;border-radius:6px;white-space:nowrap}
.b.used{background:ACCENT;color:#fff}
.b.early{background:#E4E6EA;color:#4A515C;font-weight:500;text-decoration:line-through}
.b.free{border:1px solid #D5D8DD;color:#5A6270;font-weight:500;padding:4px 6px}
.r{font-weight:700}
.r.top{color:ACCENT}
.mv{display:inline-flex;align-items:center;gap:2px;font-size:11px;font-weight:700;line-height:1;padding:3px 5px;border-radius:5px;white-space:nowrap}
.mv svg{width:7px;height:6px;fill:currentColor}
.mv.up{background:#E2F1E9;color:#0B5C42}
.mv.down{background:#FCE9DB;color:#9A3B06}
.mv.same{color:#5A6270;font-weight:600}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.movers{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.mover{background:#fff;border-radius:12px;padding:12px 14px;display:flex;flex-direction:column;gap:6px;box-shadow:0 1px 2px rgba(18,22,28,.06);min-width:0}
.mover .label{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4A515C}
.mover .teams{display:flex;flex-direction:column;gap:4px;min-width:0}
.mover .tm{display:flex;flex-direction:column;min-width:0}
.mover .name{font-weight:600;font-size:15px}
.mover .mv{align-self:flex-start;font-size:13px;padding:3px 8px;border-radius:6px}
.mover .mv svg{width:9px;height:8px}
/* mobile cards */
.cards{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px}
.card{background:#fff;border-radius:12px;padding:12px 14px;display:flex;gap:12px;align-items:center;box-shadow:0 1px 2px rgba(18,22,28,.06)}
.card .rk{width:36px;flex:none;display:flex;flex-direction:column;align-items:center;gap:4px}
.card .r{font-size:26px;line-height:1}
.card .mid{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:8px}
.card .name{font-weight:600;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card .chips{display:flex;flex-wrap:wrap;gap:4px}
.card .score{flex:none;text-align:right}
.card .pts{font-weight:700;font-size:28px;line-height:1}
/* desktop table */
.tablewrap{display:none;overflow-x:auto;background:#fff;border-radius:14px;box-shadow:0 1px 2px rgba(18,22,28,.06)}
table{width:100%;min-width:760px;border-collapse:collapse;font-size:14px}
th{padding:14px 8px;font-size:14px;text-transform:uppercase;letter-spacing:.06em;color:#4A515C;text-align:center;font-weight:700}
td{padding:10px 8px;text-align:center;border-top:1px solid #ECEEF1}
th.team,td.team{text-align:left}
td.team{font-weight:600}
th.num,td.num{text-align:right}
td .r{font-size:22px}
td.pts{font-weight:700;font-size:24px}
td.gw{color:#4A515C}
td .mv{font-size:12px;padding:3px 7px;border-radius:6px}
td .mv svg{width:8px;height:7px}
td .b{font-size:12px;min-width:28px;padding:5px 6px;margin:1px}
td .none{color:#5A6270}
.legend{background:#fff;border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:12px;font-size:13px}
.legend h2{font-size:18px}
.legend dl{margin:0;display:grid;grid-template-columns:40px 1fr;row-gap:6px}
.legend dt{font-weight:600}.legend dd{margin:0}
.keys{display:flex;flex-direction:column;gap:8px;font-size:12px;color:#4A515C}
.keys div{display:flex;gap:8px;align-items:center}
.legend p{margin:0}
@media (min-width:760px){
  header{padding:40px 24px 32px}
  h1{font-size:56px}
  main{padding:28px 24px 48px}
  .cards{display:none}
  .movers{order:-1}
  .mover{flex-direction:row;align-items:center;gap:12px;padding:12px 16px}
  .mover .label{flex:none;width:118px}
  .mover .mv{flex:none;align-self:center}
  .mover .teams{flex-direction:row;flex-wrap:wrap;gap:2px 16px}
  .mover .tm{display:block;white-space:nowrap}
  .tablewrap{display:block}
  .legend dl{grid-template-columns:repeat(5,auto 1fr);column-gap:8px}
  .keys{flex-direction:row;flex-wrap:wrap;gap:8px 20px}
}
""".replace("ACCENT", ACCENT)

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700'
    '&amp;family=Inter:wght@400;500;600&amp;display=swap" rel="stylesheet">'
)


def _badge_class(gw: int) -> str:
    return "early" if gw <= EXCLUDED_UNTIL_GW else "used"


def _badge_title(name: str, gw: int) -> str:
    if gw <= EXCLUDED_UNTIL_GW:
        return f"{name}: MH{gw} (sayılmaz, joker geçersiz)"
    return f"{name}: MH{gw}"


def _columns(chips: dict) -> list[tuple[str, str]]:
    known = [(key, name) for key, name, _c in CHIPS]
    known_keys = {k for k, _n in known}
    extra = sorted({k for team in chips.values() for k in team if k not in known_keys})
    return known + [(k, k) for k in extra]


def _card_chips(team_chips: dict, columns: list[tuple[str, str]]) -> str:
    out = []
    for key, name in columns:
        weeks = team_chips.get(key) or []
        if not weeks:
            if key in {k for k, _n, _c in CHIPS}:
                out.append(f'<span class="b free" title="{escape(name)}: kullanılmadı">{escape(key)}</span>')
            continue
        for gw in weeks:
            out.append(
                f'<span class="b {_badge_class(gw)}" title="{escape(_badge_title(name, gw))}">'
                f"{escape(key)} · {gw}</span>"
            )
    return "".join(out)


def _table_cell(weeks: list[int] | None, name: str) -> str:
    if not weeks:
        return f'<td><span class="none" title="{escape(name)}: kullanılmadı">–</span></td>'
    badges = "".join(
        f'<span class="b {_badge_class(gw)}" title="{escape(_badge_title(name, gw))}">{gw}</span>' for gw in weeks
    )
    return f"<td>{badges}</td>"


UP_ICON = '<svg aria-hidden="true" viewBox="0 0 9 8"><path d="M4.5 0 9 8H0z"/></svg>'
DOWN_ICON = '<svg aria-hidden="true" viewBox="0 0 9 8"><path d="M0 0h9L4.5 8z"/></svg>'


def _move_badge(row: dict) -> str:
    change = row.get("rankChange")
    if change is None:
        return ""
    title = f'Önceki hafta {row["previousRank"]}. sıradaydı'
    if change > 0:
        return (f'<span class="mv up" title="{title}">{UP_ICON}<span aria-hidden="true">{change}</span>'
                f'<span class="sr">{change} sıra yükseldi</span></span>')
    if change < 0:
        return (f'<span class="mv down" title="{title}">{DOWN_ICON}<span aria-hidden="true">{-change}</span>'
                f'<span class="sr">{-change} sıra düştü</span></span>')
    return '<span class="mv same" title="Sırası değişmedi"><span aria-hidden="true">–</span><span class="sr">Sırası değişmedi</span></span>'


def _mover_box(label: str, rows: list[dict]) -> str:
    """Summary card for the team(s) with the largest move in one direction."""
    if not rows:
        return ""
    teams = "".join(
        f'<span class="tm"><span class="name">{escape(r["teamName"])}</span> '
        f'<span class="muted">{r["previousRank"]}. → {r["rank"]}.</span></span>'
        for r in rows
    )
    badge = _move_badge(rows[0]).replace(f' title="Önceki hafta {rows[0]["previousRank"]}. sıradaydı"', "")
    return f'<div class="mover"><div class="label">{label}</div>{badge}<div class="teams">{teams}</div></div>'



def _top_movers(rows: list[dict]) -> str:
    changes = [r for r in rows if r.get("rankChange")]
    if not changes:
        return ""
    best = max(r["rankChange"] for r in changes)
    worst = min(r["rankChange"] for r in changes)
    up = [r for r in changes if r["rankChange"] == best] if best > 0 else []
    down = [r for r in changes if r["rankChange"] == worst] if worst < 0 else []
    return (f'<section class="movers" aria-label="Haftanın hareketleri">'
            f'{_mover_box("En çok yükselen", up)}{_mover_box("En çok düşen", down)}</section>')


TURKEY = ZoneInfo("Europe/Istanbul")

# Rewrites <time data-local> in the visitor's own time zone (same dd.mm.yyyy HH:MM format).
LOCAL_TIME_JS = (
    "<script>(function(){var t=document.querySelector('time[data-local]');if(!t)return;"
    "var d=new Date(t.getAttribute('datetime'));if(isNaN(d))return;"
    "function p(n){return(n<10?'0':'')+n}"
    "t.textContent=p(d.getDate())+'.'+p(d.getMonth()+1)+'.'+d.getFullYear()+' '+p(d.getHours())+':'+p(d.getMinutes());"
    "})();</script>"
)


def _update_time(updated_at: datetime) -> str:
    """Update time in Turkish time, shown in the visitor's local time by LOCAL_TIME_JS."""
    turkey = (updated_at.replace(tzinfo=TURKEY) if updated_at.tzinfo is None else updated_at).astimezone(TURKEY)
    stamp = turkey.strftime("%d.%m.%Y %H:%M")
    return (
        f'<time data-local datetime="{turkey.isoformat(timespec="minutes")}" '
        f'title="Türkiye saati: {stamp}">{stamp} TSİ</time>'
    )


def render(
    rows: list[dict],
    chips: dict,
    gameweek: int,
    updated_at: datetime,
    in_progress: bool = False,
    previous_gw: int | None = None,
) -> str:
    columns = _columns(chips)
    first_gw = EXCLUDED_UNTIL_GW + 1
    stamp = _update_time(updated_at)
    live_pill = f'<span class="pill">MH{gameweek} devam ediyor</span>' if in_progress else ""

    cards, trs = [], []
    for row in rows:
        team_chips = chips.get(row["teamId"], {})
        rank_cls = "r cond top" if row["rank"] <= 3 else "r cond"
        name = escape(row["teamName"])
        cards.append(
            f'<li class="card"><div class="rk"><div class="{rank_cls}">{row["rank"]}</div>{_move_badge(row)}</div>'
            f'<div class="mid"><div class="name">{name}</div>'
            f'<div class="chips">{_card_chips(team_chips, columns)}</div></div>'
            f'<div class="score"><div class="pts cond">{row["points"]}</div>'
            f'<div class="muted">MH{gameweek}: {row["gameweekPoints"]}</div></div></li>'
        )
        move_cell = f"<td>{_move_badge(row)}</td>" if previous_gw else ""
        cells = "".join(_table_cell(team_chips.get(k), n) for k, n in columns)
        trs.append(
            f'<tr><td><span class="{rank_cls}">{row["rank"]}</span></td>{move_cell}'
            f'<td class="team">{name}</td><td class="num pts cond">{row["points"]}</td>'
            f'<td class="num gw">{row["gameweekPoints"]}</td>{cells}</tr>'
        )

    chip_heads = "".join(f'<th class="cond" title="{escape(n)}">{escape(k)}</th>' for k, n in columns)
    move_head = '<th class="cond" title="Önceki haftaya göre sıra değişimi">±</th>' if previous_gw else ""
    move_note = f" · değişim: MH{previous_gw} sırasına göre" if previous_gw else ""
    move_legend = (
        '<section class="legend"><h2 class="cond">Sıra değişimi</h2><div class="keys">'
        f'<div>{_move_badge({"rankChange": 3, "previousRank": 5})}Önceki haftaya göre 3 sıra yükseldi</div>'
        f'<div>{_move_badge({"rankChange": -5, "previousRank": 3})}Önceki haftaya göre 5 sıra düştü</div>'
        f'<div>{_move_badge({"rankChange": 0, "previousRank": 1})}Sırası değişmedi</div></div>'
        '<p class="muted">Karşılaştırma, bir önceki maç haftasının sonundaki sıralamaya göre yapılır '
        "(aynı kural: MH3'ten itibaren toplam, eşitlikte o haftanın puanı). "
        "Hafta sürerken değişim de geçicidir.</p></section>"
        if previous_gw else ""
    )
    legend_items = "".join(f"<dt>{escape(k)}</dt><dd>{escape(n)}</dd>" for k, n, _c in CHIPS)

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Krallar Ligi Sıralaması</title>
{FONTS}
<style>{CSS}</style>
</head>
<body>
<header><div class="head">
<div><div class="kicker cond">TFF Fantezi Lig</div><h1 class="cond">Krallar Ligi</h1></div>
<div class="pills"><span class="pill accent">MH{first_gw} – MH{gameweek}</span>{live_pill}<span class="pill">Güncelleme: {stamp}</span></div>
</div></header>
<main>
<div class="bar"><h2 class="cond">Sıralama</h2><span class="muted">{len(rows)} takım{move_note}</span></div>
{_top_movers(rows) if previous_gw else ""}
<ol class="cards">
{chr(10).join(cards)}
</ol>
<div class="tablewrap"><table>
<thead><tr><th class="cond">#</th>{move_head}<th class="cond team">Takım</th><th class="cond num">Puan</th><th class="cond num">MH{gameweek}</th>{chip_heads}</tr></thead>
<tbody>
{chr(10).join(trs)}
</tbody>
</table></div>
<section class="legend">
<h2 class="cond">Jokerler</h2>
<dl>{legend_items}</dl>
<div class="keys">
<div><span class="b used">3K · 7</span>Kullanıldı (7. hafta)</div>
<div><span class="b early">3K · 1</span>MH1-{EXCLUDED_UNTIL_GW}: puan ve joker sayılmaz</div>
<div><span class="b free">3K</span>Henüz kullanılmadı</div>
</div>
<p class="muted">Puan, MH{first_gw}'ten itibaren toplamdır. Eşit puanda son maç haftası puanı yüksek olan önde yer alır. Gri haftalar (MH1-{EXCLUDED_UNTIL_GW}) puana sayılmaz; bu haftalarda kullanılan joker de harcanmış sayılmaz. Her gün 23:59'da, Salı günleri ayrıca 10:00'da (Türkiye saati) güncellenir; güncelleme saati tarayıcınızın saatine göre gösterilir; maç haftası sürerken son haftanın puanı geçicidir.</p>
</section>
{move_legend}
</main>
{LOCAL_TIME_JS}
</body>
</html>
"""
