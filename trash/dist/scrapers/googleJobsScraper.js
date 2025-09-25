"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.GoogleJobsScraper = void 0;
const playwright_1 = require("playwright");
const selectors_1 = require("../utils/selectors");
class GoogleJobsScraper {
    constructor(config) {
        this.browser = null;
        this.page = null;
        this.config = config;
    }
    init() {
        return __awaiter(this, void 0, void 0, function* () {
            this.browser = yield playwright_1.chromium.launch({
                headless: this.config.headless,
                args: [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    `--user-agent=${this.config.userAgent}`,
                ],
            });
            this.page = yield this.browser.newPage();
            yield this.page.setViewportSize({ width: 1920, height: 1080 });
        });
    }
    scrapeJobs(query, location) {
        return __awaiter(this, void 0, void 0, function* () {
            if (!this.page)
                yield this.init();
            const url = this.buildUrl(query, location);
            yield this.page.goto(url, { waitUntil: "networkidle" });
            if (!(yield this.waitForJobs())) {
                throw new Error("Failed to load jobs or solve CAPTCHA");
            }
            const jobs = yield this.extractJobs();
            return jobs;
        });
    }
    buildUrl(query, location) {
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
    handleCaptcha(page) {
        return __awaiter(this, void 0, void 0, function* () {
            // Implementation for CAPTCHA handling
            return true;
        });
    }
    waitForJobs() {
        return __awaiter(this, void 0, void 0, function* () {
            if (!this.page)
                return false;
            try {
                yield this.page.waitForSelector(selectors_1.selectors.jobsContainer, {
                    timeout: this.config.timeout,
                });
                return true;
            }
            catch (_a) {
                return false;
            }
        });
    }
    extractJobs() {
        return __awaiter(this, void 0, void 0, function* () {
            if (!this.page)
                return [];
            const jobs = [];
            const jobElements = yield this.page.$$(selectors_1.selectors.jobCards);
            for (let i = 0; i < jobElements.length; i++) {
                const element = jobElements[i];
                const job = yield this.extractJobData(element, i);
                if (job) {
                    jobs.push(job);
                }
            }
            return jobs;
        });
    }
    findJobDataInElement(element) {
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
    extractJobData(element, index) {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const title = yield this.extractText(element, selectors_1.selectors.jobTitle);
                const company = yield this.extractText(element, selectors_1.selectors.company);
                const location = yield this.extractText(element, selectors_1.selectors.location);
                const postedDate = yield this.extractText(element, selectors_1.selectors.postedDate);
                const linkElement = yield element.$(selectors_1.selectors.jobLink);
                const link = linkElement
                    ? (yield linkElement.getAttribute("href")) || ""
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
            }
            catch (error) {
                console.error(`Error extracting job data: ${error}`);
            }
            return null;
        });
    }
    extractText(element, selector) {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const textElement = yield element.$(selector);
                return textElement ? (yield textElement.textContent()) || "" : "";
            }
            catch (_a) {
                return "";
            }
        });
    }
    close() {
        return __awaiter(this, void 0, void 0, function* () {
            if (this.browser) {
                yield this.browser.close();
            }
        });
    }
}
exports.GoogleJobsScraper = GoogleJobsScraper;
