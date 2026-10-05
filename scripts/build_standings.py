#!/usr/bin/env python3
"""Build api/v2/standings/<key>.json for all leagues.

- PL/PD/SA/FL1/BL1 -> football-data.org (/competitions/{code}/standings, TOTAL)
- Bundesliga 2      -> OpenLigaDB (/getbltable/bl2/{year})

Output is a clean canonical schema that maps 1:1 to the app's StandingRow:
  position, team, crest, played, win, draw, loss, goalsFor, goalsAgainst,
  goalDiff, points.
"""

from common import (FootballData, current_season, now_iso, openliga_get,
                    write_if_data_changed)
from config import LEAGUES, OPENLIGA_STANDINGS


def _to_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _row_fd(r):
    t = r.get("team") or {}
    gf = _to_int(r.get("goalsFor"))
    ga = _to_int(r.get("goalsAgainst"))
    return {
        "position": _to_int(r.get("position")),
        "team": t.get("shortName") or t.get("name") or "-",
        "crest": t.get("crest"),
        "played": _to_int(r.get("playedGames")),
        "win": _to_int(r.get("won")),
        "draw": _to_int(r.get("draw")),
        "loss": _to_int(r.get("lost")),
        "goalsFor": gf,
        "goalsAgainst": ga,
        "goalDiff": _to_int(r.get("goalDifference"), gf - ga),
        "points": _to_int(r.get("points")),
    }


def _build_fd(fd, lg):
    data = fd.get(f"/competitions/{lg['code']}/standings")
    total = next((s for s in data.get("standings", []) if s.get("type") == "TOTAL"), None)
    table = [_row_fd(r) for r in (total or {}).get("table", [])]
    if not table:
        print(f"[standings] {lg['code']} empty; skip")
        return False
    out = {
        "generated_at": now_iso(),
        "season": current_season(True),
        "key": lg["key"],
        "league_name": lg["name"],
        "table": table,
    }
    return write_if_data_changed(f"standings/{lg['key']}.json", out)


def _build_openliga(lg):
    year = current_season(hyphenated=False)
    rows = openliga_get(f"/getbltable/{lg['shortcut']}/{year}")
    table = []
    for i, r in enumerate(rows or []):
        gf = _to_int(r.get("goals"))
        ga = _to_int(r.get("goalsAgainst")) or _to_int(r.get("opponentGoals"))
        table.append({
            "position": _to_int(r.get("rank")) or i + 1,
            "team": r.get("teamName") or r.get("shortName") or "-",
            "crest": r.get("teamIconUrl"),
            "played": _to_int(r.get("matches")),
            "win": _to_int(r.get("won")),
            "draw": _to_int(r.get("draw")),
            "loss": _to_int(r.get("lost")),
            "goalsFor": gf,
            "goalsAgainst": ga,
            "goalDiff": _to_int(r.get("goalDiff"), gf - ga),
            "points": _to_int(r.get("points")),
        })
    if not table:
        print(f"[standings] {lg['shortcut']} empty; skip")
        return False
    out = {
        "generated_at": now_iso(),
        "season": current_season(True),
        "key": lg["key"],
        "league_name": lg["name"],
        "table": table,
    }
    return write_if_data_changed(f"standings/{lg['key']}.json", out)


def build(fd=None):
    fd = fd or FootballData()
    changed = False
    for lg in LEAGUES:
        print(f"[standings] {lg['code']}")
        changed |= bool(_build_fd(fd, lg))
    for lg in OPENLIGA_STANDINGS:
        print(f"[standings] {lg['shortcut']} (OpenLigaDB)")
        changed |= bool(_build_openliga(lg))
    return changed


if __name__ == "__main__":
    build()
