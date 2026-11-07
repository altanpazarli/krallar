"""Render the standings as a single static, mobile-friendly HTML page.

Phones get one card per team (joker badges inline); wider screens get a table.
No JavaScript; the switch is a CSS media query.
"""

from __future__ import annotations

from datetime import datetime
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
/* mobile cards */
.cards{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px}
.card{background:#fff;border-radius:12px;padding:12px 14px;display:flex;gap:12px;align-items:center;box-shadow:0 1px 2px rgba(18,22,28,.06)}
.card .r{width:30px;flex:none;text-align:center;font-size:26px}
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


def render(rows: list[dict], chips: dict, gameweek: int, updated_at: datetime, in_progress: bool = False) -> str:
    columns = _columns(chips)
    first_gw = EXCLUDED_UNTIL_GW + 1
    stamp = updated_at.strftime("%d.%m.%Y %H:%M")
    live_pill = f'<span class="pill">MH{gameweek} devam ediyor</span>' if in_progress else ""

    cards, trs = [], []
    for row in rows:
        team_chips = chips.get(row["teamId"], {})
        rank_cls = "r cond top" if row["rank"] <= 3 else "r cond"
        name = escape(row["teamName"])
        cards.append(
            f'<li class="card"><div class="{rank_cls}">{row["rank"]}</div>'
            f'<div class="mid"><div class="name">{name}</div>'
            f'<div class="chips">{_card_chips(team_chips, columns)}</div></div>'
            f'<div class="score"><div class="pts cond">{row["points"]}</div>'
            f'<div class="muted">MH{gameweek}: {row["gameweekPoints"]}</div></div></li>'
        )
        cells = "".join(_table_cell(team_chips.get(k), n) for k, n in columns)
        trs.append(
            f'<tr><td><span class="{rank_cls}">{row["rank"]}</span></td>'
            f'<td class="team">{name}</td><td class="num pts cond">{row["points"]}</td>'
            f'<td class="num gw">{row["gameweekPoints"]}</td>{cells}</tr>'
        )

    chip_heads = "".join(f'<th class="cond" title="{escape(n)}">{escape(k)}</th>' for k, n in columns)
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
<div class="bar"><h2 class="cond">Sıralama</h2><span class="muted">{len(rows)} takım</span></div>
<ol class="cards">
{chr(10).join(cards)}
</ol>
<div class="tablewrap"><table>
<thead><tr><th class="cond">#</th><th class="cond team">Takım</th><th class="cond num">Puan</th><th class="cond num">MH{gameweek}</th>{chip_heads}</tr></thead>
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
<p class="muted">Puan, MH{first_gw}'ten itibaren toplamdır. Eşit puanda son maç haftası puanı yüksek olan önde yer alır. Gri haftalar (MH1-{EXCLUDED_UNTIL_GW}) puana sayılmaz; bu haftalarda kullanılan joker de harcanmış sayılmaz. Cuma, Cumartesi, Pazar ve Salı 23:59'da güncellenir; maç haftası sürerken son haftanın puanı geçicidir.</p>
</section>
</main>
</body>
</html>
"""
