"""Entry point: python -m krallar"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .client import ApiError, Client
from .compute import EXCLUDED_UNTIL_GW, adjusted_standings, collect_chips
from .render import render

ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = ROOT / "data" / "history-cache.json"
SITE_PATH = ROOT / "site" / "index.html"
MAX_GW = 34


def find_latest_gameweek(client: Client) -> tuple[int, list[dict]]:
    """Walk forward from MH2; for weeks not played yet the API returns the latest
    week's table (with a different gameweekId), which marks the end."""
    latest: tuple[int, list[dict]] | None = None
    for gw in range(EXCLUDED_UNTIL_GW, MAX_GW + 1):
        try:
            data = client.get_standings(gw)
        except ApiError:
            data = None
        rows = (data or {}).get("standings") or []
        if not rows or rows[0].get("gameweekId") != gw:
            if latest:
                break
            continue
        latest = (gw, rows)
    if latest is None:
        raise ApiError("Lig sıralaması bulunamadı.")
    return latest


def load_env() -> None:
    """Load KEY=VALUE pairs from a local .env (never committed) if present."""
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def update_cache(client: Client, cache: dict, team_ids: list[int], latest_gw: int) -> None:
    for team_id in team_ids:
        weeks = cache.setdefault(str(team_id), {})
        for gw in range(1, latest_gw + 1):
            if str(gw) in weeks:
                continue
            data = client.get_history(team_id, gw)
            if data is None:
                # Team had no entry that week (e.g. joined later); never changes.
                weeks[str(gw)] = None
                continue
            if data.get("live"):
                continue  # not final yet, fetch again next run
            weeks[str(gw)] = {
                "totalPoints": data.get("totalPoints"),
                "chipCode": (data.get("teamBreakdown") or {}).get("chipCode") or None,
            }


def main() -> int:
    load_env()
    email = os.environ.get("TFF_EMAIL")
    password = os.environ.get("TFF_PASSWORD")
    if not email or not password:
        print("TFF_EMAIL ve TFF_PASSWORD ortam değişkenleri gerekli.", file=sys.stderr)
        return 2

    client = Client()
    client.login(email, password)

    latest_gw, current = find_latest_gameweek(client)
    print(f"Son maç haftası: MH{latest_gw}, takım sayısı: {len(current)}")

    cache = load_cache()
    update_cache(client, cache, [row["teamId"] for row in current], latest_gw)
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")

    rows = adjusted_standings(current, cache)
    print(f"\n{'Takım':<26}{'Lig':>6}{'MH3+':>6}{'Fark':>6}{'MH1-2':>7}")
    for r in rows:
        diff = r["leaguePoints"] - r["points"]
        print(f"{r['teamName'][:25]:<26}{r['leaguePoints']:>6}{r['points']:>6}{diff:>6}{r['excludedPoints']:>7}")
    print("(Fark = sitedeki lig puanı - bizim puan; MH1-2 = takımın kendi MH1+MH2 puanı)\n")

    chips, unknown = collect_chips(cache)
    for code in sorted(unknown):
        print(f"UYARI: bilinmeyen joker kodu: {code} (krallar/compute.py CHIPS tablosunu güncelleyin)")

    now = datetime.now(ZoneInfo("Europe/Istanbul"))
    SITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SITE_PATH.write_text(render(rows, chips, latest_gw, now), encoding="utf-8")
    print(f"{SITE_PATH.relative_to(ROOT)} yazıldı. Toplam istek: {client.requests_made}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ApiError as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        sys.exit(1)
