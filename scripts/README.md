# Football data cache service

A tiny, zero-dependency backend that fetches football data **once** on a
schedule and publishes static JSON, so the mobile app reads cached files from a
CDN instead of every device hitting the rate-limited third-party APIs directly.

```
GitHub Actions (cron)  ->  build JSON  ->  commit  ->  GitHub Pages (CDN)
   token in Secrets                                        ^
                                                           |
                            thousands of app installs read here (no rate limit)
```

Third-party APIs are called **~15 times per run from one job**, no matter how
many users the app has.

## What it produces

```
api/v2/
├── index.json                      # manifest + per-file timestamps
├── fixtures.json                   # all leagues' matches (current season)
├── standings/
│   ├── premier-league.json  laliga.json  serie-a.json
│   ├── ligue-1.json  bundesliga.json
│   └── bundesliga-2.json           # from OpenLigaDB
└── scorers/
    └── premier-league.json ... (5 leagues)
```

- **Fixtures** & **scorers** are emitted in the exact shape the app already
  parses (`FixtureMatch.fromJson`, `PlayerStatsLeague.fromJson`).
- **Standings** use a clean canonical schema mapping 1:1 to `StandingRow`.
- Season is computed automatically (Aug–May) — no yearly edits.

## Data sources

| Data | Source | Notes |
|------|--------|-------|
| Fixtures, standings, scorers (5 big leagues) | football-data.org (free) | 10 req/min — paced & retried |
| Bundesliga 2 standings | OpenLigaDB | no token needed |

## One-time setup

1. **Create the repo** (public recommended → unlimited Actions minutes) and
   push these files to the root.
2. **Add the secret:** repo → *Settings → Secrets and variables → Actions →
   New repository secret*
   - Name: `FOOTBALL_DATA_TOKEN`
   - Value: your football-data.org token
3. **Enable Pages:** *Settings → Pages → Build and deployment → Source:*
   "Deploy from a branch", branch `main`, folder `/ (root)`.
4. **First run:** *Actions → refresh → Run workflow* (manual). After it commits,
   files are live at:
   ```
   https://<user>.github.io/<repo>/api/v2/index.json
   https://<user>.github.io/<repo>/api/v2/fixtures.json
   https://<user>.github.io/<repo>/api/v2/standings/premier-league.json
   https://<user>.github.io/<repo>/api/v2/scorers/premier-league.json
   ```

After that it refreshes itself every 15 minutes. Nothing else to do.

## Run locally

```bash
export FOOTBALL_DATA_TOKEN=xxxxxxxx
cd scripts
python build_all.py                 # everything
# or individually:
python build_standings.py
python build_scorers.py
python build_fixtures.py
```

Output goes to `./api/v2` (override with `OUT_DIR`).

## How the app consumes it

Point the app at the Pages base URL and drop the hardcoded football-data token:

- `fetchFixtures`  → `GET .../api/v2/fixtures.json`  (read `leagues[CODE].matches`)
- `fetchLeaguePlayerStats` → `GET .../api/v2/scorers/<key>.json`
- `fetchStandings` → `GET .../api/v2/standings/<key>.json`

Refresh cadence can later be split per data type (separate workflow files with
different crons) if you want fixtures to update more often than scorers.

## Design notes

- **Idempotent writes:** a file is rewritten only when its meaningful data
  changes (timestamps are ignored in the diff), so git history and Pages
  rebuilds aren't spammed when nothing changed.
- **Fail-safe:** if an upstream API errors or returns empty, the previous JSON
  is kept rather than overwritten with garbage.
- **Rate limit:** one shared client paces football-data calls ~7s apart and
  backs off on HTTP 429 / 5xx.
