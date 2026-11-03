"""Render the standings as a single static HTML page."""

from __future__ import annotations

from datetime import datetime
from html import escape

from .compute import CHIPS, EXCLUDED_UNTIL_GW

CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:16px;background:#f6f7f9;color:#1d2330}
h1{font-size:1.4rem;margin:0 0 4px}
.meta{color:#5b6475;font-size:.9rem;margin-bottom:12px}
.wrap{overflow-x:auto;background:#fff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
table{border-collapse:collapse;width:100%;min-width:560px}
th,td{padding:8px 10px;text-align:center;border-bottom:1px solid #eceef2;white-space:nowrap}
th{background:#1d2330;color:#fff;font-weight:600;font-size:.85rem}
td.team,th.team{text-align:left}
td.pts{font-weight:700}
tr:nth-child(even) td{background:#fafbfc}
.early{color:#a3a9b5}
.none{color:#c7ccd4}
.legend{color:#5b6475;font-size:.85rem;margin-top:12px;line-height:1.6}
"""


def _chip_cell(weeks: list[int] | None) -> str:
    if not weeks:
        return '<td class="none">-</td>'
    parts = []
    for gw in weeks:
        if gw <= EXCLUDED_UNTIL_GW:
            parts.append(f'<span class="early" title="Sayılmayan hafta: puan ve joker geçersiz">{gw}</span>')
        else:
            parts.append(str(gw))
    return f"<td>{', '.join(parts)}</td>"


def render(rows: list[dict], chips: dict, gameweek: int, updated_at: datetime) -> str:
    known_keys = [key for key, _n, _c in CHIPS]
    extra_keys = sorted({k for team in chips.values() for k in team if k not in known_keys})
    keys = known_keys + extra_keys

    head = "".join(f'<th title="{escape(name)}">{escape(key)}</th>' for key, name, _c in CHIPS)
    head += "".join(f"<th>{escape(k)}</th>" for k in extra_keys)

    body = []
    for row in rows:
        team_chips = chips.get(row["teamId"], {})
        cells = "".join(_chip_cell(team_chips.get(k)) for k in keys)
        body.append(
            f"<tr><td>{row['rank']}</td>"
            f'<td class="team">{escape(row["teamName"])}</td>'
            f'<td class="pts">{row["points"]}</td>'
            f"<td>{row['gameweekPoints']}</td>{cells}</tr>"
        )

    legend = " &middot; ".join(f"<b>{escape(k)}</b> = {escape(n)}" for k, n, _c in CHIPS)
    stamp = updated_at.strftime("%d.%m.%Y %H:%M")
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Krallar Ligi Sıralaması</title>
<style>{CSS}</style>
</head>
<body>
<h1>Krallar Ligi</h1>
<div class="meta">{EXCLUDED_UNTIL_GW + 1}. maç haftasından itibaren &middot; Güncelleme: {stamp} (MH{gameweek})</div>
<div class="wrap"><table>
<thead><tr><th>#</th><th class="team">Takım</th><th>Puan</th><th>MH{gameweek}</th>{head}</tr></thead>
<tbody>
{chr(10).join(body)}
</tbody>
</table></div>
<div class="legend">{legend}<br>
Joker sütunlarındaki sayı, jokerin kullanıldığı maç haftasıdır. <span class="early">Gri</span> haftalar (MH1-{EXCLUDED_UNTIL_GW}) puana sayılmaz; bu haftalarda kullanılan joker de harcanmış sayılmaz.</div>
</body>
</html>
"""
