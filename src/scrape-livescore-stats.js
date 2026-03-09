const fs = require("node:fs/promises");
const path = require("node:path");
const axios = require("axios");
const cheerio = require("cheerio");

const REQUEST_TIMEOUT_MS = 20000;
const OUTPUT_DATA_PATH = path.join(process.cwd(), "data", "livescore-player-stats.json");
const OUTPUT_DOCS_PATH = path.join(process.cwd(), "docs", "api", "livescore-player-stats.json");

const LEAGUES = [
  {
    key: "premier-league",
    name: "Premier League",
    country: "England",
    url: "https://www.livescore.com/en/football/england/premier-league/stats/",
  },
  {
    key: "laliga",
    name: "LaLiga",
    country: "Spain",
    url: "https://www.livescore.com/en/football/spain/laliga/stats/",
  },
  {
    key: "serie-a",
    name: "Serie A",
    country: "Italy",
    url: "https://www.livescore.com/en/football/italy/serie-a/stats/",
  },
  {
    key: "bundesliga",
    name: "Bundesliga",
    country: "Germany",
    url: "https://www.livescore.com/en/football/germany/bundesliga/stats/",
  },
  {
    key: "ligue-1",
    name: "Ligue 1",
    country: "France",
    url: "https://www.livescore.com/en/football/france/ligue-1/stats/",
  },
];

function cleanText(value) {
  if (!value) return "";
  return value.replace(/\s+/g, " ").trim();
}

function parseNumber(value) {
  const text = cleanText(value).replace("+", "");
  if (!text) return null;
  const number = Number(text);
  return Number.isNaN(number) ? null : number;
}

function parsePlayerRow($, row, columns) {
  const $row = $(row);
  const rank = parseNumber($row.find("p").first().text());
  const name = cleanText($row.find("div.ij").first().text()) || null;
  const team = cleanText($row.find("div.jj").first().text()) || null;
  const teamLogo = $row.find("img").first().attr("src") || null;
  const values = $row
    .find("div.Cj p")
    .map((_, p) => cleanText($(p).text()))
    .get()
    .filter(Boolean);

  const metrics = {};
  columns.forEach((column, index) => {
    metrics[column] = values[index] ?? null;
  });

  return {
    rank,
    player_name: name,
    team_name: team,
    team_logo: teamLogo,
    metrics,
  };
}

function parseSection($, sectionTitle) {
  const heading = $("p")
    .filter((_, el) => cleanText($(el).text()) === sectionTitle)
    .first();

  if (!heading.length) {
    return {
      section: sectionTitle.toLowerCase(),
      columns: [],
      players: [],
    };
  }

  const sectionCard = heading.closest("div.Jj");
  const columnTexts = sectionCard
    .find("p.Wb")
    .map((_, el) => cleanText($(el).text()))
    .get()
    .filter(Boolean);

  const rows = sectionCard.find('a[href^="/en/season-stats/"]');
  const players = rows.map((_, row) => parsePlayerRow($, row, columnTexts)).get();

  return {
    section: sectionTitle.toLowerCase(),
    columns: columnTexts,
    players,
  };
}

async function scrapeLeague(league) {
  const response = await axios.get(league.url, {
    timeout: REQUEST_TIMEOUT_MS,
    headers: {
      "User-Agent":
        "Mozilla/5.0 (compatible; LivescoreStatsBot/1.0; +https://github.com/notebook2cash-jpg/sianstep-football-api)",
    },
  });

  const $ = cheerio.load(response.data);
  const goals = parseSection($, "Goals");
  const assists = parseSection($, "Assists");

  return {
    key: league.key,
    league_name: league.name,
    country: league.country,
    source_url: league.url,
    goals,
    assists,
  };
}

async function saveJson(outputPath, data) {
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, JSON.stringify(data, null, 2), "utf8");
}

async function main() {
  const leagues = [];

  for (const league of LEAGUES) {
    const parsed = await scrapeLeague(league);
    leagues.push(parsed);
  }

  const payload = {
    source: "https://www.livescore.com/",
    scraped_at: new Date().toISOString(),
    total_leagues: leagues.length,
    leagues,
  };

  await saveJson(OUTPUT_DATA_PATH, payload);
  await saveJson(OUTPUT_DOCS_PATH, payload);

  console.log(`Saved LiveScore stats for ${payload.total_leagues} leagues.`);
}

main().catch((error) => {
  console.error("LiveScore scrape failed:", error.message);
  process.exit(1);
});
