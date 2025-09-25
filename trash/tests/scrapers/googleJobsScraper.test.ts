import { test, expect } from '@playwright/test';
import { GoogleJobsScraper } from '../../src/scrapers/googleJobsScraper';

test.describe('GoogleJobsScraper', () => {
    let scraper: GoogleJobsScraper;

    test.beforeEach(() => {
        scraper = new GoogleJobsScraper();
    });

    test('should build a valid search URL', () => {
        const query = 'Software Engineer';
        const location = 'New York';
        const url = scraper.buildUrl(query, location);
        expect(url).toContain('https://www.google.com/search?q=Software+Engineer');
        expect(url).toContain('l=New+York');
    });

    test('should handle CAPTCHA correctly', async ({ page }) => {
        await page.goto('https://www.google.com/search?q=Software+Engineer');
        const captchaHandled = await scraper.handleCaptcha(page);
        expect(captchaHandled).toBe(true);
    });

    test('should extract job data from a job element', async () => {
        const mockElement = {
            querySelector: jest.fn().mockImplementation((selector) => {
                if (selector === 'h3') return { innerText: () => 'Software Engineer' };
                if (selector === '.company') return { innerText: () => 'Tech Company' };
                if (selector === '.location') return { innerText: () => 'New York, NY' };
                if (selector === 'a') return { getAttribute: () => 'https://example.com/job' };
                return null;
            }),
        };

        const jobData = scraper.findJobDataInElement(mockElement);
        expect(jobData.title).toBe('Software Engineer');
        expect(jobData.company).toBe('Tech Company');
        expect(jobData.location).toBe('New York, NY');
        expect(jobData.link).toBe('https://example.com/job');
    });

    test('should extract jobs from the page', async ({ page }) => {
        await page.goto('https://www.google.com/search?q=Software+Engineer');
        const jobs = await scraper.extractJobs(page);
        expect(Array.isArray(jobs)).toBe(true);
    });
});