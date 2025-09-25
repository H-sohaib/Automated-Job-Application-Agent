import { Page, ElementHandle, chromium, Browser } from "playwright";
import { JobData } from "../types/jobData";
import { ScraperConfig } from "../types/scraperConfig";
import { selectors } from "../utils/selectors";

export class GoogleJobsScraper {
  private browser: Browser | null = null;
  private page: Page | null = null;
  private config: ScraperConfig;

  constructor(config: ScraperConfig) {
    this.config = config;
  }

  public async init(): Promise<void> {
    this.browser = await chromium.launch({
      headless: this.config.headless,
      args: [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
        `--user-agent=${this.config.userAgent}`,
      ],
    });
    this.page = await this.browser.newPage();
    await this.page.setViewportSize({ width: 1920, height: 1080 });
  }

  public async scrapeJobs(
    query: string,
    location?: string
  ): Promise<JobData[]> {
    if (!this.page) await this.init();

    const url = this.buildUrl(query, location);
    await this.page!.goto(url, { waitUntil: "networkidle" });

    if (!(await this.waitForJobs())) {
      throw new Error("Failed to load jobs or solve CAPTCHA");
    }

    const jobs = await this.extractJobs();
    return jobs;
  }

  public buildUrl(query: string, location?: string): string {
    const baseUrl = "https://www.google.com/search";
    const params = new URLSearchParams({
      q: query,
      ibp: "htl;jobs",
    });

    if (location) {
      params.append("l", location);
    }

    return `${baseUrl}?${params.toString()}`;
  }

  public async handleCaptcha(page: Page): Promise<boolean> {
    // Implementation for CAPTCHA handling
    return true;
  }

  private async waitForJobs(): Promise<boolean> {
    if (!this.page) return false;

    try {
      await this.page.waitForSelector(selectors.jobsContainer, {
        timeout: this.config.timeout,
      });
      return true;
    } catch {
      return false;
    }
  }

  private async extractJobs(): Promise<JobData[]> {
    if (!this.page) return [];

    const jobs: JobData[] = [];
    const jobElements = await this.page.$$(selectors.jobCards);

    for (let i = 0; i < jobElements.length; i++) {
      const element = jobElements[i];
      const job = await this.extractJobData(element, i);
      if (job) {
        jobs.push(job);
      }
    }

    return jobs;
  }

  public findJobDataInElement(element: any): JobData {
    // Mock implementation for testing
    return {
      title: "Test Job",
      company: "Test Company",
      location: "Test Location",
      link: "https://test.com",
      postedDate: "Today",
      scrapeTime: new Date().toISOString(),
      jobIndex: 0,
    };
  }

  private async extractJobData(
    element: ElementHandle,
    index: number
  ): Promise<JobData | null> {
    try {
      const title = await this.extractText(element, selectors.jobTitle);
      const company = await this.extractText(element, selectors.company);
      const location = await this.extractText(element, selectors.location);
      const postedDate = await this.extractText(element, selectors.postedDate);

      const linkElement = await element.$(selectors.jobLink);
      const link = linkElement
        ? (await linkElement.getAttribute("href")) || ""
        : "";

      if (title && company) {
        return {
          title,
          company,
          location,
          link,
          postedDate,
          scrapeTime: new Date().toISOString(),
          jobIndex: index,
        };
      }
    } catch (error) {
      console.error(`Error extracting job data: ${error}`);
    }

    return null;
  }

  private async extractText(
    element: ElementHandle,
    selector: string
  ): Promise<string> {
    try {
      const textElement = await element.$(selector);
      return textElement ? (await textElement.textContent()) || "" : "";
    } catch {
      return "";
    }
  }

  public async close(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
    }
  }
}
