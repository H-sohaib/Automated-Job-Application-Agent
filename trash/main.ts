import { chromium, Browser, Page, BrowserContext } from "playwright";

class BrowserManager {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private page: Page | null = null;

  async start(): Promise<void> {
    console.log("🚀 Starting browser...");

    this.browser = await chromium.launch({
      headless: false,
      args: [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--start-maximized",
        "--disable-blink-features=AutomationControlled", // Disable automation detection
      ],
    });

    // Create a new browser context with a custom user agent
    this.context = await this.browser.newContext({
      userAgent:
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
      viewport: { width: 1920, height: 1080 },
    });

    this.page = await this.context.newPage();

    // Set additional headers to mimic a real browser
    await this.page.setExtraHTTPHeaders({
      "Accept-Language": "en-US,en;q=0.9",
    });

    // Add stealth-like behavior
    await this.addStealthFeatures();

    console.log("✅ Browser opened!");

    // Navigate to Google
    console.log("🌐 Navigating to Google...");
    await this.page.goto("https://www.google.com", {
      waitUntil: "domcontentloaded",
    });

    console.log(
      "📝 Navigate to your target page, then press ENTER to start scraping..."
    );

    await this.waitForUserInput();

    console.log("🤖 Starting scraping logic...");
    if (this.page) {
      // await startScraping(this.page);
    }

    await this.close();
  }

  private async addStealthFeatures(): Promise<void> {
    if (!this.context) return;

    // Remove WebDriver property
    await this.context.addInitScript(() => {
      Object.defineProperty(navigator, "webdriver", { get: () => undefined });
    });

    // Mock plugins and languages
    await this.context.addInitScript(() => {
      Object.defineProperty(navigator, "plugins", {
        get: () => [1, 2, 3],
      });
      Object.defineProperty(navigator, "languages", {
        get: () => ["en-US", "en"],
      });
    });

    console.log("🛡️ Stealth features added.");
  }

  private async waitForUserInput(): Promise<void> {
    return new Promise((resolve) => {
      process.stdin.setRawMode(true);
      process.stdin.resume();
      process.stdin.on("data", () => {
        process.stdin.setRawMode(false);
        process.stdin.pause();
        resolve();
      });
    });
  }

  async close(): Promise<void> {
    if (this.browser) {
      console.log("🔒 Closing browser...");
      await this.browser.close();
    }
  }
}

// Main execution
async function main() {
  console.log("🎯 Job Scraper Starting...");

  const manager = new BrowserManager();

  try {
    await manager.start();
  } catch (error) {
    console.error("❌ Error:", error);
    await manager.close();
  }
}

process.on("SIGINT", () => {
  console.log("\n👋 Shutting down...");
  process.exit(0);
});

main();
