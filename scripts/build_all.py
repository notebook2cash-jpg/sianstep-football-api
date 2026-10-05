#!/usr/bin/env python3
"""Full refresh: fixtures + standings + scorers + index, all sharing ONE
rate-limited football-data client so the 10 req/min cap is respected across
the whole run (~15 calls paced ~7s apart => ~2 min)."""

import build_fixtures
import build_index
import build_scorers
import build_standings
from common import FootballData


def main():
    fd = FootballData()
    changed = False
    changed |= bool(build_fixtures.build(fd))
    changed |= bool(build_standings.build(fd))
    changed |= bool(build_scorers.build(fd))
    build_index.build()
    print(f"DONE. data_changed={changed}")


if __name__ == "__main__":
    main()
