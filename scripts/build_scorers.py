#!/usr/bin/env python3
"""Build api/v2/scorers/<key>.json — top scorers & assist leaders per league.

Output matches the app's PlayerStatsLeague.fromJson schema (key, league_name,
country, goals{section,columns,players[...]}, assists{...}), so the app's
existing parser works unchanged.

Note: football-data's /scorers is sorted by goals and returns limited rows, so
the assist board is derived from that same set (good-enough top-N). Assists are
sometimes null on the free tier -> those players simply drop out of the assist
section.
"""

from common import FootballData, now_iso, write_if_data_changed
from config import LEAGUES


def _section(title, column, entries, metric, limit=10):
    ranked = sorted(entries, key=lambda e: e[metric], reverse=True)
    players = []
    for i, e in enumerate(ranked):
        if i >= limit or e[metric] <= 0:
            break
        players.append({
            "rank": i + 1,
            "player_name": e["name"],
            "team_name": e["team"],
            "team_logo": e["crest"],
            "metrics": {column: str(e[metric])},
        })
    if not players:
        return None
    return {"section": title, "columns": [column], "players": players}


def _build_one(fd, lg):
    data = fd.get(f"/competitions/{lg['code']}/scorers?limit=30")
    entries = []
    for s in data.get("scorers", []):
        p, t = s.get("player") or {}, s.get("team") or {}
        entries.append({
            "name": p.get("name") or "-",
            "team": t.get("shortName") or t.get("name") or "-",
            "crest": t.get("crest"),
            "goals": s.get("goals") or 0,
            "assists": s.get("assists") or 0,
        })
    goals = _section("ดาวซัลโว", "G", entries, "goals")
    assists = _section("จ่ายบอลยอดเยี่ยม", "A", entries, "assists")
    if not goals and not assists:
        print(f"[scorers] {lg['code']} empty; skip")
        return False
    out = {
        "generated_at": now_iso(),
        "key": lg["key"],
        "league_name": lg["name"],
        "country": lg.get("country", ""),
        "goals": goals,
        "assists": assists,
    }
    return write_if_data_changed(f"scorers/{lg['key']}.json", out)


def build(fd=None):
    fd = fd or FootballData()
    changed = False
    for lg in LEAGUES:
        print(f"[scorers] {lg['code']}")
        changed |= bool(_build_one(fd, lg))
    return changed


if __name__ == "__main__":
    build()
