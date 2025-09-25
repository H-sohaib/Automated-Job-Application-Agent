import { LaunchOptions } from 'playwright';

export const getBrowserConfig = (): LaunchOptions => {
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