import json
from datetime import datetime
from pathlib import Path

from krallar.compute import adjusted_standings, collect_chips
from krallar.render import render

FIXTURES = Path(__file__).parent / "fixtures"


def standings_fixture():
    return json.loads((FIXTURES / "siralama.json").read_text(encoding="utf-8"))["data"]["standings"]


def test_score_is_sum_of_weeks_after_two_and_handles_late_joiners():
    current = [
        {"teamId": 1, "teamName": "A", "points": 300, "gameweekPoints": 70},
        {"teamId": 2, "teamName": "Late", "points": 200, "gameweekPoints": 60},
    ]
    cache = {
        "1": {"1": {"totalPoints": 47}, "2": {"totalPoints": 76}, "3": {"totalPoints": 80}, "4": {"totalPoints": 70}},
        "2": {"1": None, "2": None, "3": {"totalPoints": 90}, "4": {"totalPoints": 60}},
    }
    rows = {r["teamName"]: r for r in adjusted_standings(current, cache)}
    assert rows["A"]["points"] == 150
    assert rows["A"]["excludedPoints"] == 123
    assert rows["Late"]["points"] == 150 and rows["Late"]["excludedPoints"] == 0
    assert rows["A"]["rank"] == rows["Late"]["rank"] == 1


def test_ties_share_rank_and_sort_by_name():
    current = [
        {"teamId": 1, "teamName": "beta"},
        {"teamId": 2, "teamName": "Alfa"},
        {"teamId": 3, "teamName": "Gama"},
        {"teamId": 4, "teamName": "Delta"},
    ]
    cache = {"1": {"3": {"totalPoints": 50}}, "2": {"3": {"totalPoints": 50}},
             "3": {"3": {"totalPoints": 60}}, "4": {"3": {"totalPoints": 40}}}
    rows = adjusted_standings(current, cache)
    assert [(r["teamName"], r["rank"]) for r in rows] == [("Gama", 1), ("Alfa", 2), ("beta", 2), ("Delta", 4)]


def test_all_teams_from_fixture_present():
    rows = adjusted_standings(standings_fixture(), {})
    assert len(rows) == 18


def test_collect_chips_from_history_fixture_and_unknown_codes():
    takim = json.loads((FIXTURES / "takim.json").read_text(encoding="utf-8"))["data"]
    cache = {
        "477821": {
            "1": {"totalPoints": 40, "chipCode": "chip.mystery"},
            "2": None,
            "9": {"totalPoints": 50, "chipCode": None},
            "10": {"totalPoints": takim["totalPoints"], "chipCode": takim["teamBreakdown"]["chipCode"]},
        }
    }
    chips, unknown = collect_chips(cache)
    assert chips[477821]["3K"] == [10]
    assert collect_chips({"1": {"5": {"chipCode": "chip.benchboost"}}})[0][1] == {"TTS": [5]}
    assert chips[477821]["chip.mystery"] == [1]
    assert unknown == {"chip.mystery"}


def test_render_marks_early_chip_and_escapes_names():
    rows = [{"teamId": 1, "teamName": "<b>X</b>", "points": 10, "gameweekPoints": 5, "rank": 1}]
    chips = {1: {"3K": [10], "LB": [2]}}
    html = render(rows, chips, 10, datetime(2026, 11, 3, 10, 0))
    assert "&lt;b&gt;X&lt;/b&gt;" in html
    assert '<span class="early" title="Puanı sayılmayan hafta">2</span>' in html
    assert "<td>10</td>" in html
    assert "03.11.2026 10:00 (MH10)" in html
