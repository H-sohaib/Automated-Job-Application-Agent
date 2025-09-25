import { GoogleJobsScraper } from "./scrapers/googleJobsScraper";
import { ScraperConfig } from "./types/scraperConfig";

const config: ScraperConfig = {
  headless: false,
  timeout: 30000,
  maxJobs: 50,
  userAgent:
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  scrollDelay: 1000,
  captchaWait: 5000,
};

const scraper = new GoogleJobsScraper(config);

async function main() {
  const query = "Software Engineer";
  const location = "Remote";

  try {
    const jobs = await scraper.scrapeJobs(query, location);
    console.log(`Found ${jobs.length} jobs:`);
    console.table(jobs);
  } catch (error) {
    console.error("Error during scraping:", error);
  }
}

main();
