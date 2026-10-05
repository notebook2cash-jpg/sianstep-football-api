"""Shared helpers for the football-data cache service.

- FootballData: rate-limited client for api.football-data.org (free tier = 10
  req/min, so we pace calls ~7s apart and retry on 429/5xx).
- openliga_get: plain fetch for api.openligadb.de (Bundesliga 2 standings).
- current_season / now_iso: season + timestamp helpers.
- write_if_data_changed: atomic JSON write that only touches the file when the
  *meaningful* data changed (ignoring volatile keys like generated_at), so the
  git repo isn't spammed with no-op commits.
"""

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

# Output root; overridable from CI so it can point at <workspace>/api/v2.
OUT_DIR = os.environ.get("OUT_DIR", "api/v2")


def now_iso():
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def current_season(hyphenated=True):
    """European season: Aug–May. July onward belongs to the new season.
    hyphenated=True  -> "2026-2027" (TheSportsDB / football-data style)
    hyphenated=False -> "2026"       (OpenLigaDB start-year style)
    """
    now = datetime.now(timezone.utc)
    start = now.year if now.month >= 7 else now.year - 1
    return f"{start}-{start + 1}" if hyphenated else str(start)


def _request_json(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


class FootballData:
    BASE = "https://api.football-data.org/v4"

    def __init__(self, token=None, min_interval=7.0):
        self.token = token or os.environ.get("FOOTBALL_DATA_TOKEN", "")
        if not self.token:
            raise SystemExit("ERROR: FOOTBALL_DATA_TOKEN env var is required")
        self.min_interval = min_interval
        self._last = 0.0

    def get(self, path, max_retries=4):
        url = f"{self.BASE}{path}"
        for attempt in range(max_retries):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            try:
                data = _request_json(url, {"X-Auth-Token": self.token})
                self._last = time.monotonic()
                return data
            except urllib.error.HTTPError as e:
                self._last = time.monotonic()
                if e.code == 429:
                    retry = int(e.headers.get("Retry-After", "60"))
                    print(f"  429 rate-limited; sleeping {retry}s "
                          f"(attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry + 1)
                    continue
                if 500 <= e.code < 600:
                    back = 5 * (attempt + 1)
                    print(f"  {e.code} server error; backoff {back}s")
                    time.sleep(back)
                    continue
                raise
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                back = 5 * (attempt + 1)
                print(f"  network error {e}; backoff {back}s")
                time.sleep(back)
                continue
        raise SystemExit(f"ERROR: football-data GET failed after retries: {path}")


def openliga_get(path, max_retries=3):
    url = f"https://api.openligadb.de{path}"
    for attempt in range(max_retries):
        try:
            return _request_json(url)
        except Exception as e:  # noqa: BLE001 - best-effort external API
            print(f"  OpenLigaDB error {e}; retry {attempt + 1}/{max_retries}")
            time.sleep(4 * (attempt + 1))
    raise SystemExit(f"ERROR: OpenLigaDB GET failed: {path}")


def _strip(obj, ignore):
    if isinstance(obj, dict):
        return {k: _strip(v, ignore) for k, v in obj.items() if k not in ignore}
    if isinstance(obj, list):
        return [_strip(v, ignore) for v in obj]
    return obj


def write_if_data_changed(rel_path, obj, ignore=("generated_at",)):
    """Write api/v2/<rel_path> only if data (minus ignored keys) changed.
    Atomic (tmp + os.replace). Returns True if a write happened."""
    full = os.path.join(OUT_DIR, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    ignore = set(ignore)
    new_cmp = _strip(obj, ignore)
    if os.path.exists(full):
        try:
            with open(full, encoding="utf-8") as f:
                if _strip(json.load(f), ignore) == new_cmp:
                    print(f"  unchanged {rel_path}")
                    return False
        except Exception:  # noqa: BLE001 - corrupt/old file -> overwrite
            pass
    tmp = full + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, full)
    print(f"  wrote {rel_path}")
    return True
