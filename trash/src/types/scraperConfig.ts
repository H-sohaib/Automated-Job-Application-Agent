export interface ScraperConfig {
    headless: boolean;
    timeout: number;
    maxJobs: number;
    userAgent: string;
    scrollDelay: number;
    captchaWait: number;
}