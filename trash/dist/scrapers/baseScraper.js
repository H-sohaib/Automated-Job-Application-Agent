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
exports.BaseScraper = void 0;
class BaseScraper {
    constructor() {
        this.browser = null;
        this.page = null;
    }
    initBrowser() {
        return __awaiter(this, arguments, void 0, function* (headless = true) {
            const { chromium } = require("playwright");
            this.browser = yield chromium.launch({
                headless: headless,
                args: [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ],
            });
            if (!this.browser) {
                throw new Error("Failed to launch browser");
            }
            this.page = yield this.browser.newPage();
            yield this.page.setViewportSize({ width: 1920, height: 1080 });
        });
    }
    navigate(url) {
        return __awaiter(this, void 0, void 0, function* () {
            if (!this.page) {
                throw new Error("Browser not initialized. Call initBrowser() first.");
            }
            try {
                yield this.page.goto(url, { waitUntil: "networkidle" });
            }
            catch (error) {
                console.error(`Error navigating to ${url}:`, error);
                throw error;
            }
        });
    }
    closeBrowser() {
        return __awaiter(this, void 0, void 0, function* () {
            if (this.browser) {
                yield this.browser.close();
            }
        });
    }
    handleError(error) {
        return __awaiter(this, void 0, void 0, function* () {
            console.error("An error occurred:", error);
            yield this.closeBrowser();
        });
    }
}
exports.BaseScraper = BaseScraper;
