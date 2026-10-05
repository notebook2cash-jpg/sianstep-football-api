#!/usr/bin/env python3
"""Build api/v2/fixtures.json — every league's matches for the current season,
kept in the SAME shape the app's FixtureMatch.fromJson already understands
(homeTeam/awayTeam/score.fullTime/score.winner), so the app only swaps URLs.
"""

from common import FootballData, current_season, now_iso, write_if_data_changed
from config import LEAGUES


def _match(m):
    ht, at = m.get("homeTeam") or {}, m.get("awayTeam") or {}
    ft = (m.get("score") or {}).get("fullTime") or {}
    return {
        "id": m.get("id"),
        "utcDate": m.get("utcDate"),
        "status": m.get("status"),
        "matchday": m.get("matchday"),
        "homeTeam": {"shortName": ht.get("shortName") or ht.get("name"), "crest": ht.get("crest")},
        "awayTeam": {"shortName": at.get("shortName") or at.get("name"), "crest": at.get("crest")},
        "score": {
            "fullTime": {"home": ft.get("home"), "away": ft.get("away")},
            "winner": (m.get("score") or {}).get("winner"),
        },
    }


def build(fd=None):
    fd = fd or FootballData()
    out = {"generated_at": now_iso(), "season": current_season(True), "leagues": {}}
    for lg in LEAGUES:
        print(f"[fixtures] {lg['code']}")
        data = fd.get(f"/competitions/{lg['code']}/matches")
        matches = [_match(m) for m in data.get("matches", [])]
        if matches:
            out["leagues"][lg["code"]] = {"matches": matches}
    if not out["leagues"]:
        print("[fixtures] no data; skip write")
        return False
    return write_if_data_changed("fixtures.json", out)


if __name__ == "__main__":
    build()
