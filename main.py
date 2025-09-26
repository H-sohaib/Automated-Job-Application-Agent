import asyncio
import logging
import json
import os
from playwright_stealth import Stealth  # Changed import
from playwright.async_api import async_playwright
import random
import traceback

# Import the scraping function from scraper.py
from scraper import perform_scraping

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def save_cookies(context, filename='data/google_cookies.json'):
    """Save browser cookies to a file"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        cookies = await context.cookies()
        with open(filename, 'w') as f:
            json.dump(cookies, f)
        logger.info(f"Saved {len(cookies)} cookies to {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to save cookies: {e}")
        return False

async def load_cookies(context, filename='data/google_cookies.json'):
    """Load browser cookies from a file"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
                logger.info(f"Loaded {len(cookies)} cookies from {filename}")
                return True
        else:
            logger.info(f"No cookie file found at {filename}")
            return False
    except Exception as e:
        logger.error(f"Failed to load cookies: {e}")
        return False

def get_random_user_agent():
    """Get a random realistic user agent"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    return random.choice(user_agents)

async def main():
    browser = None
    context = None 
    
    try:
        logger.info("Starting Google Jobs scraper with enhanced stealth")
        
        # Initialize Stealth with Playwright (using the correct syntax)
        async with Stealth().use_async(async_playwright()) as p:
            # Launch browser with enhanced stealth settings
            logger.info("Launching browser with stealth settings")
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions-http-throttling',
                    '--disable-ipc-flooding-protection',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )
            
            # Create context with realistic settings
            context = await browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent=get_random_user_agent(),
                locale='en-US',  # Keep English locale for interface
                timezone_id='Africa/Casablanca',  # Morocco timezone
                permissions=['geolocation'],
                geolocation={'latitude': 33.5731, 'longitude': -7.5898},  # Casablanca coordinates
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8,ar;q=0.7',  # English first, then French/Arabic
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0'
                }
            )
            
            # Create page (stealth is already applied through Stealth().use_async())
            page = await context.new_page()
            
            # Load existing cookies
            await load_cookies(context)
            
            # Add additional stealth JavaScript
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'fr', 'ar'],
                });
                
                window.chrome = {
                    runtime: {},
                };
            """)
            
            # # Navigate to Google first (not directly to jobs)
            # logger.info("Navigating to Google homepage first")
            # await page.goto("https://www.google.com", timeout=0)
            
            # # Wait a bit and then navigate to jobs
            # await asyncio.sleep(random.uniform(2, 4))
            
            logger.info("Navigating to Google Jobs search")
            await page.goto("https://www.google.com/search?q=software+engineer+jobs&ibp=htl;jobs&hl=en", timeout=0)
                        
            logger.info("Browser is ready. You can:")
            logger.info("2. Navigate to your desired job search")
            logger.info("3. Press Enter here to start scraping...")
            
            # Wait for user to press Enter
            await asyncio.get_event_loop().run_in_executor(None, input)
            
            # Save cookies after user interaction
            logger.info("Saving cookies after user interaction...")
            await save_cookies(context)
            
            # Call the scraping function
            logger.info("Starting scraping process")
            results = await perform_scraping(page)
            
            if results:
                logger.info(f"Scraping completed successfully! Processed {results} jobs")
            else:
                logger.warning("Scraping completed but no results returned")
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
    finally:
        # Close browser if it's still open
        if browser:
            try:
                logger.info("Closing browser")
                await browser.close()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

# Run the main function
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Script terminated by user (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
    finally:
        logger.info("Script execution completed")