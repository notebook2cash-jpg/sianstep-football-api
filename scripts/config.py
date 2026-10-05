"""League catalogue. `code` = football-data.org competition code."""

LEAGUES = [
    {"key": "premier-league", "code": "PL",  "name": "Premier League", "name_th": "พรีเมียร์ลีก", "country": "England"},
    {"key": "laliga",         "code": "PD",  "name": "La Liga",        "name_th": "ลาลีกา",      "country": "Spain"},
    {"key": "serie-a",        "code": "SA",  "name": "Serie A",        "name_th": "เซเรีย อา",   "country": "Italy"},
    {"key": "ligue-1",        "code": "FL1", "name": "Ligue 1",        "name_th": "ลีก เอิง",    "country": "France"},
    {"key": "bundesliga",     "code": "BL1", "name": "Bundesliga",     "name_th": "บุนเดสลีกา",  "country": "Germany"},
]

# football-data free tier does NOT cover Bundesliga 2 — standings come from
# OpenLigaDB instead (no scorers available for this league).
OPENLIGA_STANDINGS = [
    {"key": "bundesliga-2", "shortcut": "bl2", "name": "Bundesliga 2", "name_th": "บุนเดสลีกา 2", "country": "Germany"},
]
