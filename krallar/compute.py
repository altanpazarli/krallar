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
    last gameweek points). Ties on score are broken by the last gameweek's points;
    only teams equal on both share a rank (ordered by team name).
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
    _assign_ranks(rows)
    return rows


def _assign_ranks(rows: list[dict]) -> None:
    """Sort by points, then last gameweek points, then name; teams equal on both share a rank."""
    rows.sort(key=lambda r: (-r["points"], -r["gameweekPoints"], r["teamName"].casefold()))
    prev_key = None
    rank = 0
    for i, row in enumerate(rows, start=1):
        key = (row["points"], row["gameweekPoints"])
        if key != prev_key:
            rank = i
            prev_key = key
        row["rank"] = rank


def ranks_after(rows: list[dict], weeks: dict, gameweek: int) -> dict[int, int]:
    """Each team's rank at the end of `gameweek`, by the same rules as adjusted_standings.

    Uses only weeks EXCLUDED_UNTIL_GW < gw <= gameweek; ties are broken by that week's points.
    """
    past = []
    for row in rows:
        team_weeks = weeks.get(str(row["teamId"]), {})
        last = team_weeks.get(str(gameweek)) or {}
        past.append(
            {
                "teamId": row["teamId"],
                "teamName": row["teamName"],
                "points": _week_points(team_weeks, lambda gw: EXCLUDED_UNTIL_GW < gw <= gameweek),
                "gameweekPoints": last.get("totalPoints") or 0,
            }
        )
    _assign_ranks(past)
    return {r["teamId"]: r["rank"] for r in past}


def add_rank_changes(rows: list[dict], weeks: dict, latest_gw: int) -> int | None:
    """Set `previousRank` and `rankChange` (positive = moved up) on each row, compared with
    the standings at the end of the previous gameweek. Returns that gameweek, or None when
    there is no counted previous week to compare with (then both fields are None).
    """
    previous_gw = latest_gw - 1
    if previous_gw <= EXCLUDED_UNTIL_GW:
        for row in rows:
            row["previousRank"] = row["rankChange"] = None
        return None
    before = ranks_after(rows, weeks, previous_gw)
    for row in rows:
        row["previousRank"] = before[row["teamId"]]
        row["rankChange"] = before[row["teamId"]] - row["rank"]
    return previous_gw


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

