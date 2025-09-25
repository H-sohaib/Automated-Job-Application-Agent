import asyncio
import logging
import json
import os
from playwright_stealth import Stealth
from playwright.async_api import async_playwright
import pdb 
# Import the scraping function from scraper.py
from scraper import perform_scraping

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def save_cookies(context, filename='data/google_cookies.json'):
    """Save browser cookies to a file"""
    try:
        cookies = await context.cookies()
        with open(filename, 'w') as f:
            json.dump(cookies, f)
        logger.info(f"Saved {len(cookies)} cookies to {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to save cookies: {e}")
        return False

async def main():
    browser = None
    context = None 
    
    try:
        logger.info("Starting Google Jobs scraper")
        # Initialize Stealth with Playwright
        async with Stealth().use_async(async_playwright()) as p:
            # Launch visible browser
            logger.info("Launching browser")
            browser = await p.chromium.launch(
                headless=False,
                ignore_default_args=['--enable-automation'],
            )
            
            # Create context with minimal settings
            context = await browser.new_context(
                viewport={'width': 1366, 'height': 768},
            )
            
            page = await context.new_page()
            
            # Load cookies if they exist (key part for captcha avoidance)
            cookie_file = 'data/google_cookies.json'
            if os.path.exists(cookie_file):
                with open(cookie_file, 'r') as f:
                    cookies = json.load(f)
                    logger.info(f"Loading {len(cookies)} cookies from {cookie_file}")
                    await context.add_cookies(cookies)
            else:
                logger.info(f"No cookie file found at {cookie_file}")
            
            # Set up handler for page close
            async def on_page_close(page):
                logger.warning("Browser page was closed by user")
            page.on("close", on_page_close)
            
            # Navigate to Google Jobs search
            logger.info("Navigating to Google Jobs search")
            await page.goto("https://www.google.com/search?q=it+jobs&ibp=htl;jobs")
            
            # breakpoint() 
            logger.info("Browser is open. Press Enter to start scraping...")
            # Wait for user to press Enter
            await asyncio.get_event_loop().run_in_executor(None, input)
            
            # Save cookies immediately after user interaction
            logger.info("Saving cookies before starting scraping...")
            await save_cookies(context)
            
            # Call the scraping function from scraper.py
            logger.info("Starting scraping process")
            results = await perform_scraping(page)
            
            logger.info("Scraping completed")
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")
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