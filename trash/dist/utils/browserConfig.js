"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getBrowserConfig = void 0;
const getBrowserConfig = () => {
    return {
        headless: false, // Run in headful mode for realistic browsing
        args: [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ],
    };
};
exports.getBrowserConfig = getBrowserConfig;
