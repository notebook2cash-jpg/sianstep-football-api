#!/usr/bin/env python3
"""Regenerate api/v2/index.json — a lightweight manifest of every data file
with the generated_at read from each. Only rewrites when the *set* of files
changes (timestamps are ignored in the diff), so it doesn't commit every run.
The app can read per-file generated_at for "updated X min ago".
"""

import json
import os

from common import OUT_DIR, current_season, now_iso, write_if_data_changed
from config import LEAGUES, OPENLIGA_STANDINGS


def _entry(rel):
    full = os.path.join(OUT_DIR, rel)
    if not os.path.exists(full):
        return None
    try:
        with open(full, encoding="utf-8") as f:
            return {"path": rel, "updated_at": json.load(f).get("generated_at")}
    except Exception:  # noqa: BLE001
        return {"path": rel, "updated_at": None}


def build():
    standings = {}
    for lg in LEAGUES + OPENLIGA_STANDINGS:
        e = _entry(f"standings/{lg['key']}.json")
        if e:
            standings[lg["key"]] = e
    scorers = {}
    for lg in LEAGUES:
        e = _entry(f"scorers/{lg['key']}.json")
        if e:
            scorers[lg["key"]] = e

    index = {
        "schema_version": 2,
        "generated_at": now_iso(),
        "season": current_season(True),
        "files": {
            "fixtures": _entry("fixtures.json"),
            "standings": standings,
            "scorers": scorers,
        },
    }
    # Ignore volatile timestamp keys so the manifest commits only when the file
    # set changes (e.g. a league added/removed), not on every refresh.
    return write_if_data_changed("index.json", index,
                                 ignore=("generated_at", "updated_at"))


if __name__ == "__main__":
    build()
