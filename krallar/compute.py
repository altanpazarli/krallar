"""Pure calculation helpers (no network access)."""

from __future__ import annotations

# Gameweeks up to and including this one are excluded from the standings.
EXCLUDED_UNTIL_GW = 2

# Column key, Turkish name, chip code from the API (all five confirmed in real data).
CHIPS: list[tuple[str, str, str]] = [
    ("3K", "Tripleks Kaptan", "chip.triplecaptain"),
    ("4K", "Dört Dörtlük Kaptan", "chip.quadruplecaptain"),
    ("TTS", "Tüm Takım Sahaya", "chip.benchboost"),
    ("HÜ", "Hücum!", "chip.attack"),
    ("LB", "Limitsiz Bütçe", "chip.unlimitedbudget"),
]
CODE_TO_KEY = {code: key for key, _name, code in CHIPS}


def _week_points(weeks: dict, include) -> int:
    return sum((entry or {}).get("totalPoints") or 0 for gw, entry in weeks.items() if include(int(gw)))


def adjusted_standings(current: list[dict], cache: dict) -> list[dict]:
    """Score = sum of the team's own weekly totalPoints for gw > EXCLUDED_UNTIL_GW.

    `current` is the league standings of the latest gameweek (team list, league points,
    last gameweek points). Equal scores share a rank; ties are ordered by team name.
    """
    rows = []
    for row in current:
        weeks = cache.get(str(row["teamId"]), {})
        points = _week_points(weeks, lambda gw: gw > EXCLUDED_UNTIL_GW)
        rows.append(
            {
                "teamId": row["teamId"],
                "teamName": row["teamName"],
                "points": points,
                "gameweekPoints": row.get("gameweekPoints") or 0,
                "leaguePoints": row.get("points") or 0,
                "excludedPoints": _week_points(weeks, lambda gw: gw <= EXCLUDED_UNTIL_GW),
            }
        )
    rows.sort(key=lambda r: (-r["points"], r["teamName"].casefold()))
    prev_points = None
    rank = 0
    for i, row in enumerate(rows, start=1):
        if row["points"] != prev_points:
            rank = i
            prev_points = row["points"]
        row["rank"] = rank
    return rows


def collect_chips(cache: dict) -> tuple[dict, set]:
    """From the history cache build {teamId: {columnKey: [gw, ...]}}.

    Unknown chip codes are kept under their raw code. Returns (chips, unknown_codes).
    """
    chips: dict[int, dict[str, list[int]]] = {}
    unknown: set[str] = set()
    for team_id, weeks in cache.items():
        team: dict[str, list[int]] = {}
        for gw, entry in weeks.items():
            code = (entry or {}).get("chipCode")
            if not code:
                continue
            key = CODE_TO_KEY.get(code)
            if key is None:
                unknown.add(code)
                key = code
            team.setdefault(key, []).append(int(gw))
        for weeks_used in team.values():
            weeks_used.sort()
        chips[int(team_id)] = team
    return chips, unknown
