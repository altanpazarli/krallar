"""Minimal read-only client for tfffantezilig.com."""

from __future__ import annotations

import time

import requests

BASE_URL = "https://tfffantezilig.com"
LEAGUE_ID = 47061
REQUEST_DELAY = 0.3


class ApiError(RuntimeError):
    pass


class Client:
    def __init__(self, base_url: str = BASE_URL, delay: float = REQUEST_DELAY):
        self.base_url = base_url
        self.delay = delay
        self.requests_made = 0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "krallar-standings/1.0", "Accept": "application/json"})

    def login(self, email: str, password: str) -> None:
        resp = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"email": email.strip(), "password": password},
            timeout=30,
        )
        self.requests_made += 1
        if resp.status_code == 401:
            raise ApiError("Giriş başarısız: e-posta veya şifre hatalı (401).")
        if resp.status_code == 403:
            raise ApiError("Giriş başarısız: e-posta doğrulanmamış (403).")
        if not resp.ok:
            raise ApiError(f"Giriş başarısız: HTTP {resp.status_code}.")
        body = resp.json()
        if body.get("ok") is not True:
            raise ApiError("Giriş başarısız: beklenmeyen yanıt.")

    def _get(self, path: str, params: dict | None = None):
        """GET a backend path; returns `data`, or None on 404."""
        time.sleep(self.delay)
        resp = self.session.get(f"{self.base_url}/api/backend/{path}", params=params, timeout=30)
        self.requests_made += 1
        if resp.status_code == 404:
            return None
        if not resp.ok:
            raise ApiError(f"GET {path} başarısız: HTTP {resp.status_code}.")
        body = resp.json()
        if body.get("status") is False:
            return None
        return body.get("data")

    def get_standings(self, gameweek: int | None = None) -> dict | None:
        params = {"offset": 0, "limit": 50}
        if gameweek is not None:
            params["gameweek-id"] = gameweek
        return self._get(f"fantasy-team/leagues/{LEAGUE_ID}/standings", params)

    def get_history(self, team_id: int, gameweek: int) -> dict | None:
        return self._get(f"fantasy-team/teams/{team_id}/history/{gameweek}")
