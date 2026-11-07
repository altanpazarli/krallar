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
    assert (rows["A"]["rank"], rows["Late"]["rank"]) == (1, 2)  # tie: last GW 70 > 60


def test_ties_broken_by_last_gameweek_points():
    current = [
        {"teamId": 1, "teamName": "beta", "gameweekPoints": 30},
        {"teamId": 2, "teamName": "Alfa", "gameweekPoints": 30},
        {"teamId": 3, "teamName": "Gama", "gameweekPoints": 10},
        {"teamId": 4, "teamName": "Delta", "gameweekPoints": 20},
        {"teamId": 5, "teamName": "Epsilon", "gameweekPoints": 99},
    ]
    cache = {"1": {"3": {"totalPoints": 50}}, "2": {"3": {"totalPoints": 50}},
             "3": {"3": {"totalPoints": 60}}, "4": {"3": {"totalPoints": 50}},
             "5": {"3": {"totalPoints": 40}}}
    rows = adjusted_standings(current, cache)
    # 50-point tie broken by last gameweek points; equal on both -> shared rank
    assert [(r["teamName"], r["rank"]) for r in rows] == [
        ("Gama", 1), ("Alfa", 2), ("beta", 2), ("Delta", 4), ("Epsilon", 5)]


def test_all_teams_from_fixture_present():
    rows = adjusted_standings(standings_fixture(), {})
    assert len(rows) == 18


def test_collect_chips_from_history_fixture_and_unknown_codes():
    takim = json.loads((FIXTURES / "takim.json").read_text(encoding="utf-8"))["data"]
    cache = {
        "101": {
            "1": {"totalPoints": 40, "chipCode": "chip.mystery"},
            "2": None,
            "9": {"totalPoints": 50, "chipCode": None},
            "10": {"totalPoints": takim["totalPoints"], "chipCode": takim["teamBreakdown"]["chipCode"]},
        }
    }
    chips, unknown = collect_chips(cache)
    assert chips[101]["3K"] == [10]
    assert collect_chips({"1": {"5": {"chipCode": "chip.benchboost"}}})[0][1] == {"TTS": [5]}
    assert chips[101]["chip.mystery"] == [1]
    assert unknown == {"chip.mystery"}


def test_render_marks_early_chip_and_escapes_names():
    rows = [{"teamId": 1, "teamName": "<b>X</b>", "points": 10, "gameweekPoints": 5, "rank": 1}]
    chips = {1: {"3K": [10], "LB": [2]}}
    html = render(rows, chips, 10, datetime(2026, 11, 3, 10, 0))
    assert "&lt;b&gt;X&lt;/b&gt;" in html
    # mobile card badges
    assert '<span class="b early" title="Limitsiz Bütçe: MH2 (sayılmaz, joker geçersiz)">LB · 2</span>' in html
    assert '<span class="b used" title="Tripleks Kaptan: MH10">3K · 10</span>' in html
    assert '<span class="b free" title="Hücum!: kullanılmadı">HÜ</span>' in html
    # desktop table cells
    assert '<td><span class="b used" title="Tripleks Kaptan: MH10">10</span></td>' in html
    assert "Güncelleme: 03.11.2026 10:00" in html
    assert "MH3 – MH10" in html


class FakeClient:
    def __init__(self, points):
        self.points = points  # {(team, gw): totalPoints or None}
        self.calls = []

    def get_history(self, team_id, gw):
        self.calls.append((team_id, gw))
        p = self.points.get((team_id, gw))
        return None if p is None else {"totalPoints": p, "live": False, "teamBreakdown": {"chipCode": None}}


def test_final_gameweeks_needs_finished_points_and_bonuses():
    from krallar.__main__ import final_gameweeks
    day = lambda pts, bon: {"allPointsAdded": pts, "allBonusesAdded": bon}
    fx = {"gameweeks": [
        {"id": 10, "finished": True, "matchDays": [day(True, True)]},
        {"id": 11, "finished": True, "matchDays": [day(True, False)]},
        {"id": 12, "finished": False, "matchDays": [day(False, False)]},
    ]}
    assert final_gameweeks(fx) == {10}


def test_week_in_progress_is_not_cached_and_is_refetched():
    from krallar.__main__ import merge_weeks, update_cache
    # week 3 is in progress but an older run cached a partial score for it
    cache = {"1": {"1": {"totalPoints": 40, "chipCode": None}, "3": {"totalPoints": 2, "chipCode": None}}}
    client = FakeClient({(1, 1): 40, (1, 2): 50, (1, 3): 8})
    pending = update_cache(client, cache, [1], 3, final={1, 2})
    assert client.calls == [(1, 2), (1, 3)]               # final + cached week 1 is not refetched
    assert cache["1"]["2"]["totalPoints"] == 50           # newly final week is cached
    assert "3" not in cache["1"]                          # in-progress week is never cached (stale entry dropped)
    merged = merge_weeks(cache, pending)
    assert merged["1"]["3"]["totalPoints"] == 8           # but its current points are used


def test_legend_says_early_chips_are_not_spent():
    html = render([], {}, 10, datetime(2026, 11, 3, 10, 0))
    assert "joker de harcanmış sayılmaz" in html
    assert "Eşit puanda son maç haftası puanı yüksek olan önde" in html


def _weeks(table):
    """{teamId: [gw3, gw4, ...]} -> history cache shape."""
    return {str(t): {str(gw): {"totalPoints": p} for gw, p in enumerate(pts, start=3)} for t, pts in table.items()}


def test_rank_changes_against_previous_week():
    from krallar.compute import add_rank_changes
    weeks = _weeks({1: [50, 10], 2: [40, 30], 3: [30, 10], 4: [45, 5]})
    # after MH3: 1(50) 2. 4(45) 3. 2(40) 4. 3(30)  ->  after MH4: 2(70) 1(60) 4(50) 3(40)
    current = [{"teamId": t, "teamName": n, "gameweekPoints": weeks[str(t)]["4"]["totalPoints"]}
               for t, n in [(1, "A"), (2, "B"), (3, "C"), (4, "D")]]
    rows = adjusted_standings(current, weeks)
    assert add_rank_changes(rows, weeks, 4) == 3
    got = {r["teamName"]: (r["rank"], r["previousRank"], r["rankChange"]) for r in rows}
    assert got == {"B": (1, 3, 2), "A": (2, 1, -1), "D": (3, 2, -1), "C": (4, 4, 0)}


def test_previous_ranks_break_ties_by_that_weeks_points():
    from krallar.compute import ranks_after
    weeks = _weeks({1: [30, 20, 99], 2: [10, 40, 0]})
    rows = [{"teamId": 1, "teamName": "A"}, {"teamId": 2, "teamName": "B"}]
    # after MH4 both have 50; B scored more in MH4 (40 > 20). MH5 is ignored.
    assert ranks_after(rows, weeks, 4) == {2: 1, 1: 2}


def test_no_rank_change_when_previous_week_is_not_counted():
    from krallar.compute import add_rank_changes
    weeks = _weeks({1: [50]})
    rows = adjusted_standings([{"teamId": 1, "teamName": "A", "gameweekPoints": 50}], weeks)
    assert add_rank_changes(rows, weeks, 3) is None  # MH2 doesn't count, nothing to compare
    assert rows[0]["rankChange"] is None and rows[0]["previousRank"] is None
    html = render(rows, {}, 3, datetime(2026, 11, 3, 10, 0))
    assert 'class="mv' not in html and "Sıra değişimi" not in html


def test_render_rank_change_badges_movers_and_column():
    rows = [
        {"teamId": 1, "teamName": "Casino", "points": 600, "gameweekPoints": 93, "rank": 1, "previousRank": 4, "rankChange": 3},
        {"teamId": 2, "teamName": "Alz", "points": 590, "gameweekPoints": 60, "rank": 2, "previousRank": 2, "rankChange": 0},
        {"teamId": 3, "teamName": "Amsterdam", "points": 580, "gameweekPoints": 56, "rank": 3, "previousRank": 1, "rankChange": -2},
        {"teamId": 4, "teamName": "Mimi", "points": 570, "gameweekPoints": 30, "rank": 4, "previousRank": 3, "rankChange": -1},
    ]
    html = render(rows, {}, 10, datetime(2026, 11, 3, 10, 0), previous_gw=9)
    assert '<span class="mv up" title="Önceki hafta 4. sıradaydı">' in html
    assert '<span class="sr">3 sıra yükseldi</span>' in html
    assert '<span class="mv down" title="Önceki hafta 1. sıradaydı">' in html
    assert '<span class="sr">2 sıra düştü</span>' in html
    assert html.count('<span class="mv same" title="Sırası değişmedi">') == 2 + 1  # card + table + legend
    assert '<th class="cond" title="Önceki haftaya göre sıra değişimi">±</th>' in html
    assert "değişim: MH9 sırasına göre" in html
    movers = html.split('<section class="movers"')[1].split("</section>")[0]
    assert "En çok yükselen</div><div class=\"name\">Casino</div>" in movers
    assert "En çok düşen</div><div class=\"name\">Amsterdam</div>" in movers
    assert "1. → 3." in movers and "4. → 1." in movers


def test_movers_list_all_teams_sharing_the_biggest_move_and_skip_empty_side():
    rows = [
        {"teamId": 1, "teamName": "A", "points": 9, "gameweekPoints": 0, "rank": 1, "previousRank": 2, "rankChange": 1},
        {"teamId": 2, "teamName": "B", "points": 8, "gameweekPoints": 0, "rank": 2, "previousRank": 3, "rankChange": 1},
        {"teamId": 3, "teamName": "C", "points": 7, "gameweekPoints": 0, "rank": 3, "previousRank": 1, "rankChange": -2},
    ]
    movers = render(rows, {}, 10, datetime(2026, 11, 3), previous_gw=9).split('<section class="movers"')[1]
    assert '<div class="name">A, B</div>' in movers
    assert "2. → 1." not in movers and "3. → 2." not in movers  # no single path for a shared move
    assert "1. → 3." in movers
    still = [dict(r, rankChange=0) for r in rows]
    assert '<section class="movers"' not in render(still, {}, 10, datetime(2026, 11, 3), previous_gw=9)


def test_weekly_movers_newest_first_with_ties_and_quiet_sides():
    from krallar.compute import weekly_movers
    # MH3: A50 D45 B40 C30 | MH4: B70 A60 D50 C40 | MH5: nobody changes order
    weeks = _weeks({1: [50, 10, 1], 2: [40, 30, 1], 3: [30, 10, 1], 4: [45, 5, 1]})
    rows = [{"teamId": t, "teamName": n} for t, n in [(1, "A"), (2, "B"), (3, "C"), (4, "D")]]
    got = weekly_movers(rows, weeks, 5)
    assert [m["gameweek"] for m in got] == [5, 4]
    assert got[0] == {"gameweek": 5, "up": [], "upBy": 0, "down": [], "downBy": 0}
    assert got[1]["up"] == [("B", 3, 1)] and got[1]["upBy"] == 2
    assert got[1]["down"] == [("A", 1, 2), ("D", 2, 3)] and got[1]["downBy"] == 1  # tie, by new rank
    assert weekly_movers(rows, weeks, 3) == []  # first counted week has nothing to compare with


def _mover(gw, up=(), up_by=0, down=(), down_by=0):
    return {"gameweek": gw, "up": list(up), "upBy": up_by, "down": list(down), "downBy": down_by}


def test_render_history_section_cards_table_and_collapsed_weeks():
    movers = [_mover(gw, [("Up<&>", 5, 2)], 3, [("X", 1, 4), ("Y", 2, 5)], 3) for gw in range(11, 3, -1)]
    html = render([], {}, 11, datetime(2026, 11, 3), in_progress=True, movers=movers)
    section = html.split('<section class="history"')[1].split("</section>")[0]
    assert "Haftanın hareketleri" in section
    assert "<b>Up&lt;&amp;&gt;</b>" in section and "5. → 2." in section
    assert "<b>X</b>" in section and "<b>Y</b>" in section and "2. → 5." in section
    assert section.count("sürüyor · geçici") == 2  # only MH11: card + table row
    phone = section.split('<div class="histwrap">')[0]
    open_part, hidden = phone.split("<details>")
    assert open_part.count('<li class="wk">') == 5 and hidden.count('<li class="wk">') == 3
    assert "Tüm haftalar (MH4'ten itibaren)" in hidden
    assert section.split('<div class="histwrap">')[1].count("<tr><td>") == 8  # wide screens: every week
    # the history comes before the jokers legend
    assert html.index('<section class="history"') < html.index("<h2 class=\"cond\">Jokerler</h2>")


def test_render_history_quiet_week_and_no_history():
    html = render([], {}, 4, datetime(2026, 11, 3), movers=[_mover(4)])
    assert "Kimse yükselmedi" in html and "Kimse düşmedi" in html
    assert "<details>" not in html and "sürüyor" not in html
    assert '<section class="history"' not in render([], {}, 3, datetime(2026, 11, 3), movers=[])
