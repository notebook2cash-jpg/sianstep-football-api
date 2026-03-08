const fs = require("node:fs/promises");
const path = require("node:path");
const axios = require("axios");
const cheerio = require("cheerio");

const SOURCE_URL = "https://sianstep.com/program_football/";
const OUTPUT_DATA_PATH = path.join(process.cwd(), "data", "latest.json");
const OUTPUT_DOCS_PATH = path.join(process.cwd(), "docs", "api", "latest.json");

function cleanText(value) {
  if (!value) return "";
  return value.replace(/\s+/g, " ").trim();
}

function parseTeam(rawTeam) {
  const raw = cleanText(rawTeam);
  const startRank = raw.match(/^\[(.*?)\]/)?.[1] ?? null;
  const endRank = raw.match(/\[(.*?)\]$/)?.[1] ?? null;
  const rank = startRank || endRank || null;

  const name = cleanText(raw.replace(/^\[(.*?)\]\s*/, "").replace(/\s*\[(.*?)\]$/, ""));

  return {
    raw,
    name,
    rank,
  };
}

function parseScore(scoreText) {
  const text = cleanText(scoreText);
  const scoreMatch = text.match(/^(\d+)\s*-\s*(\d+)$/);
  if (scoreMatch) {
    return {
      text,
      home: Number(scoreMatch[1]),
      away: Number(scoreMatch[2]),
      is_known: true,
    };
  }

  return {
    text,
    home: null,
    away: null,
    is_known: false,
  };
}

function parseOddsCell($cell) {
  const raw = cleanText($cell.text());
  const lines = $cell
    .text()
    .split("\n")
    .map((line) => cleanText(line))
    .filter((line) => line && line !== "▼" && line !== "▲");

  return {
    raw,
    lines,
  };
}

function parseMatchRow($, row) {
  const cells = $(row).find("td");
  if (cells.length < 8) return null;

  const time = cleanText($(cells[0]).text()) || null;
  const status = cleanText($(cells[1]).text()) || null;
  const homeTeam = parseTeam($(cells[2]).text());
  const score = parseScore($(cells[3]).text());
  const awayTeam = parseTeam($(cells[4]).text());
  const odds = parseOddsCell($(cells[5]));
  const tipText = cleanText($(cells[6]).text());
  const tipLink = $(cells[6]).find("a").attr("href") || null;
  const liveChannel = cleanText($(cells[7]).text()) || null;

  return {
    time,
    status,
    home_team: homeTeam,
    away_team: awayTeam,
    score,
    odds,
    tip: {
      text: tipText,
      url: tipLink,
    },
    live_channel: liveChannel,
  };
}

function parseDocument(html) {
  const $ = cheerio.load(html);
  const root = $(".td-post-text-content.td-post-content").first();

  if (!root.length) {
    throw new Error("ไม่พบโครงสร้างบทความหลัก (.td-post-text-content.td-post-content)");
  }

  const payload = {
    source: SOURCE_URL,
    scraped_at: new Date().toISOString(),
    timezone: "Asia/Bangkok",
    dates: [],
  };

  let currentDate = null;

  root.children().each((_, el) => {
    const $el = $(el);

    if ($el.hasClass("title-header")) {
      const dateLabel = cleanText($el.text());
      currentDate = {
        date_label: dateLabel,
        leagues: [],
      };
      payload.dates.push(currentDate);
      return;
    }

    if ($el.hasClass("league-header")) {
      if (!currentDate) return;

      const leagueName = cleanText($el.text());
      const tableWrap = $el.next(".responsive-table-wrap");

      const matches = [];
      tableWrap.find("tbody tr").each((__, row) => {
        const parsed = parseMatchRow($, row);
        if (parsed) matches.push(parsed);
      });

      currentDate.leagues.push({
        league_name: leagueName,
        matches,
      });
    }
  });

  payload.total_dates = payload.dates.length;
  payload.total_leagues = payload.dates.reduce((sum, date) => sum + date.leagues.length, 0);
  payload.total_matches = payload.dates.reduce(
    (sum, date) => sum + date.leagues.reduce((acc, league) => acc + league.matches.length, 0),
    0
  );

  return payload;
}

async function saveJson(outputPath, data) {
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, JSON.stringify(data, null, 2), "utf8");
}

async function main() {
  const response = await axios.get(SOURCE_URL, {
    timeout: 20000,
    headers: {
      "User-Agent":
        "Mozilla/5.0 (compatible; SianstepFootballApiBot/1.0; +https://github.com/your-org/your-repo)",
    },
  });

  const parsed = parseDocument(response.data);
  await saveJson(OUTPUT_DATA_PATH, parsed);
  await saveJson(OUTPUT_DOCS_PATH, parsed);

  console.log(`Saved ${parsed.total_matches} matches from ${parsed.total_leagues} leagues.`);
}

main().catch((error) => {
  console.error("Scrape failed:", error.message);
  process.exit(1);
});
