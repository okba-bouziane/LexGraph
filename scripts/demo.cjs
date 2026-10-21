// Records the demo video with puppeteer-core page.screencast(). Needs the stack up with the graph ingested.
const puppeteer = require("/Users/okba/Documents/portflio/job-search/outreach/node_modules/puppeteer-core");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const OUT = __dirname + "/../docs/";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function ask(page, q, retriever) {
  await page.$eval("#q", (e) => (e.value = ""));
  await page.type("#q", q, { delay: 25 });
  await page.select("#retriever", retriever);
  await sleep(500);
  await page.click("button.primary");
  await page.waitForFunction(() => !document.querySelector("#out").hidden && document.querySelector("button.primary").textContent === "Ask", { timeout: 180000 });
  await sleep(7000);
}

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new", args: ["--no-sandbox"] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });
  await page.goto("http://localhost:8090/", { waitUntil: "networkidle0" });
  const rec = await page.screencast({ path: OUT + "demo.mp4" });
  await sleep(4000);
  await ask(page, "Which parent company guarantees the supplier's obligations under the Master Supply Agreement?", "vector");
  await ask(page, "Which parent company guarantees the supplier's obligations under the Master Supply Agreement?", "graph");
  await page.evaluate(() => window.scrollTo(0, 400));
  await sleep(3000);
  await page.evaluate(() => window.scrollTo(0, 0));
  await ask(page, "Which company owns the carrier under the Transport Services Agreement?", "hybrid");
  await sleep(5000);
  await rec.stop();
  await browser.close();
})();
