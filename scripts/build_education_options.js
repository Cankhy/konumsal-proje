const fs = require("fs");
const https = require("https");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const OUT_FILE = path.join(ROOT, "static", "js", "education-options.generated.js");

const YOK_ENDPOINT = "https://yokatlas.yok.gov.tr/api/tercih-kilavuz/search";
const MEB_CSV_URL = "https://raw.githubusercontent.com/ensarkovankaya/meb-okullar/master/meb-okullar.csv";

const liseBranches = [
  "Sayısal",
  "Eşit Ağırlık",
  "Sözel",
  "Yabancı Dil",
  "Bilişim Teknolojileri",
  "Elektrik-Elektronik Teknolojisi",
  "Harita-Tapu-Kadastro",
  "Muhasebe ve Finansman",
  "Web Programcılığı",
];

function trCompare(a, b) {
  return a.localeCompare(b, "tr");
}

function cleanText(value) {
  return String(value || "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function requestText(url, options = {}) {
  return new Promise((resolve, reject) => {
    const req = https.request(url, options, (res) => {
      let body = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => {
        body += chunk;
      });
      res.on("end", () => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error(`${url} returned ${res.statusCode}: ${body.slice(0, 200)}`));
          return;
        }
        resolve(body);
      });
    });
    req.on("error", reject);
    if (options.body) req.write(options.body);
    req.end();
  });
}

async function fetchYokAtlasPage(page, size) {
  const body = JSON.stringify({
    filters: {
      puanTuru: null,
      universiteId: [],
      birimGrupId: [],
      ilKodu: [],
      birimTuruId: null,
      universiteTuru: null,
      bursOraniId: null,
      ogrenimTuruId: null,
      kilavuzKodu: null,
      minBasariSirasi: null,
      maxBasariSirasi: null,
    },
    page,
    size,
    sortBy: "universiteAdi",
    direction: "ASC",
  });
  const response = await requestText(YOK_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Content-Length": Buffer.byteLength(body),
      "Accept": "application/json",
      "User-Agent": "Mozilla/5.0",
    },
    body,
  });
  return JSON.parse(response);
}

async function buildUniversities() {
  const schools = {};
  const size = 1000;
  const first = await fetchYokAtlasPage(0, size);
  const pages = Math.max(1, Number(first.totalPages || 1));
  const allRows = [...(first.content || [])];

  for (let page = 1; page < pages; page += 1) {
    const payload = await fetchYokAtlasPage(page, size);
    allRows.push(...(payload.content || []));
  }

  allRows.forEach((row) => {
    const school = cleanText(row.universiteAdi);
    const department = cleanText(row.birimGrupAdi || row.birimAdi);
    if (!school || !department) return;
    if (!schools[school]) schools[school] = new Set();
    schools[school].add(department);
  });
  return schools;
}

function parseCsvLine(line) {
  const result = [];
  let current = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      if (quoted && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        quoted = !quoted;
      }
    } else if (ch === "," && !quoted) {
      result.push(current);
      current = "";
    } else {
      current += ch;
    }
  }
  result.push(current);
  return result;
}

async function buildHighSchools() {
  const schools = {};
  const csv = await requestText(MEB_CSV_URL, { headers: { "User-Agent": "Mozilla/5.0" } });
  csv.split(/\r?\n/).slice(1).forEach((line) => {
    if (!line.trim()) return;
    const cols = parseCsvLine(line).map(cleanText);
    const name = cols.find((col) => /lisesi|mesleki eğitim merkezi|çok programlı/i.test(col));
    if (!name || !/lisesi|mesleki eğitim merkezi|çok programlı/i.test(name)) return;
    schools[name] = new Set(liseBranches);
  });
  return schools;
}

function serializeSchools(schoolMap) {
  const result = {};
  Object.keys(schoolMap).sort(trCompare).forEach((school) => {
    result[school] = Array.from(schoolMap[school]).sort(trCompare);
  });
  return result;
}

async function main() {
  const [universities, highSchools] = await Promise.all([
    buildUniversities(),
    buildHighSchools(),
  ]);
  const merged = { ...highSchools };
  Object.entries(universities).forEach(([school, departments]) => {
    if (!merged[school]) merged[school] = new Set();
    departments.forEach((department) => merged[school].add(department));
  });

  const data = serializeSchools(merged);
  const source = `window.KONUMSAL_EDUCATION_OPTIONS = ${JSON.stringify(data, null, 2)};\n`;
  fs.writeFileSync(OUT_FILE, source, "utf8");
  console.log(`Wrote ${Object.keys(data).length} schools to ${OUT_FILE}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
