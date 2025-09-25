import { Browser, Page } from "playwright";

export abstract class BaseScraper {
  protected browser: Browser | null;
  protected page: Page | null;

  constructor() {
    this.browser = null;
    this.page = null;
  }

  async initBrowser(headless: boolean = true): Promise<void> {
    const { chromium } = require("playwright");

    // More stealth browser configuration
    this.browser = await chromium.launch({
      headless: headless,
      args: [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
        "--disable-background-networking",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
        "--disable-backgrounding-occluded-windows",
        "--disable-client-side-phishing-detection",
        "--disable-crash-reporter",
        "--disable-oopr-debug-crash-dump",
        "--no-crash-upload",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-low-res-tiling",
        "--log-level=3",
        "--silent",
      ],
    });

    if (!this.browser) {
      throw new Error("Failed to launch browser");
    }

    this.page = await this.browser.newPage();

    // Set realistic viewport
    await this.page.setViewportSize({
      width: 1366 + Math.floor(Math.random() * 100),
      height: 768 + Math.floor(Math.random() * 100),
    });

    // Override user agent and other properties
    await this.page.setUserAgent(
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    );

    // Remove webdriver property and other automation indicators
    await this.page.addInitScript(() => {
      // Remove webdriver property
      delete (window as any).webdriver;

      // Override the plugins property to use a custom getter
      Object.defineProperty(navigator, "plugins", {
        get: function () {
          return [1, 2, 3, 4, 5];
        },
      });

      // Override the languages property to use a custom getter
      Object.defineProperty(navigator, "languages", {
        get: function () {
          return ["en-US", "en"];
        },
      });

      // Override the webdriver property to use a custom getter
      Object.defineProperty(navigator, "webdriver", {
        get: function () {
          return false;
        },
      });

      // Mock chrome object
      (window as any).chrome = {
        runtime: {},
        loadTimes: function () {},
        csi: function () {},
        app: {},
      };

      // Override permissions
      const originalQuery = window.navigator.permissions.query;
      window.navigator.permissions.query = (parameters) =>
        parameters.name === "notifications"
          ? Promise.resolve({ state: Cypress ? "denied" : "granted" })
          : originalQuery(parameters);
    });

    // Set extra headers
    await this.page.setExtraHTTPHeaders({
      "Accept-Language": "en-US,en;q=0.9",
      "Accept-Encoding": "gzip, deflate, br",
      Accept:
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
      "Upgrade-Insecure-Requests": "1",
      "Cache-Control": "max-age=0",
    });
  }

  async navigate(url: string): Promise<void> {
    if (!this.page) {
      throw new Error("Browser not initialized. Call initBrowser() first.");
    }

    try {
      // Add random delay before navigation
      await this.randomDelay(1000, 3000);

      await this.page.goto(url, {
        waitUntil: "domcontentloaded",
        timeout: 30000,
      });

      // Wait for page to fully load and add human-like behavior
      await this.randomDelay(2000, 4000);

      // Simulate human-like mouse movement
      await this.simulateHumanBehavior();
    } catch (error) {
      console.error(`Error navigating to ${url}:`, error);
      throw error;
    }
  }

  private async simulateHumanBehavior(): Promise<void> {
    if (!this.page) return;

    try {
      // Random mouse movements
      for (let i = 0; i < 3; i++) {
        await this.page.mouse.move(Math.random() * 1000, Math.random() * 600);
        await this.randomDelay(100, 500);
      }

      // Random scroll
      await this.page.evaluate(() => {
        window.scrollTo(0, Math.random() * 200);
      });

      await this.randomDelay(500, 1500);

      // Scroll back to top
      await this.page.evaluate(() => {
        window.scrollTo(0, 0);
      });
    } catch (error) {
      console.log("Error in human behavior simulation:", error);
    }
  }

  private async randomDelay(min: number, max: number): Promise<void> {
    const delay = Math.floor(Math.random() * (max - min + 1)) + min;
    await new Promise((resolve) => setTimeout(resolve, delay));
  }

  async closeBrowser(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
    }
  }

  protected async handleError(error: any): Promise<void> {
    console.error("An error occurred:", error);
    await this.closeBrowser();
  }
}
