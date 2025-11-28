import asyncio
import logging
import json
import os
from playwright_stealth import Stealth  # Changed import
from playwright.async_api import async_playwright
import random
import traceback

# Import the scraping function from scraper.py
from google_scraper.scraper import perform_scraping
# Import LinkedIn scraper (you'll need to create this)
from linkedin_scraper.scraper import perform_linkedin_scraping
from config import JOB_SEARCH_KEYWORDS , MAX_JOBS_TO_SCRAPE


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

def display_menu():
    """Display the main menu for scraper selection"""
    print("\n" + "=" * 60)
    print("           JOB SCRAPER TOOLKIT")
    print("=" * 60)
    print("Please select a scraper to run:")
    print()
    print("1. Google Jobs Scraper")
    print("2. LinkedIn Saved Jobs Scraper")
    print("3. Exit")
    print()
    print("=" * 60)

def get_user_choice():
    """Get and validate user choice"""
    while True:
        display_menu()
        try:
            choice = input("Enter your choice (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("\nInvalid choice! Please enter 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\nExiting...")
            return 3
        except Exception as e:
            print(f"\nError reading input: {e}")

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

async def run_google_scraper():
    """Run the Google Jobs scraper"""
    browser = None
    context = None 
    
    try:
        logger.info("Starting Google Jobs scraper with enhanced stealth")
        
        async with Stealth().use_async(async_playwright()) as p:
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
            
            context = await browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent=get_random_user_agent(),
                locale='en-US',
                timezone_id='Africa/Casablanca',
                permissions=['geolocation'],
                geolocation={'latitude': 33.5731, 'longitude': -7.5898},
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8,ar;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0'
                }
            )
            
            page = await context.new_page()
            
            await load_cookies(context)
            
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
            
            logger.info("Navigating to Google Jobs search")
            await page.goto("https://www.google.com/search?q=software+engineer+jobs&ibp=htl;jobs&hl=en", timeout=0)
                        
            logger.info("Browser is ready. Solve CAPTCHA if needed, then press Enter to start scraping...")
            await asyncio.get_event_loop().run_in_executor(None, input)
            
            await save_cookies(context)
            
            # Create single output file for all keywords
            from google_scraper.scraper import get_json_filename
            output_file = get_json_filename()
            logger.info(f"All jobs will be saved to: {output_file}")
            
            total_jobs = 0
            # REMOVE THIS LINE:
            # total_limit = MAX_JOBS_TO_SCRAPE if MAX_JOBS_TO_SCRAPE > 0 else None
            
            # Loop through keywords
            for idx, keyword in enumerate(JOB_SEARCH_KEYWORDS, 1):
                # REMOVE THIS CHECK:
                # if total_limit is not None and total_jobs >= total_limit:
                #     logger.info(f"Reached global job limit ({total_limit}). Stopping.")
                #     break
                
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing keyword {idx}/{len(JOB_SEARCH_KEYWORDS)}: '{keyword}'")
                logger.info(f"Progress: {total_jobs} total jobs scraped so far")  # CHANGED THIS LINE
                logger.info(f"{'='*60}")
                
                # Navigate to search URL for this keyword
                search_url = f"https://www.google.com/search?q={keyword.replace(' ', '+')}+jobs&ibp=htl;jobs&hl=en"
                await page.goto(search_url, timeout=0)
                await asyncio.sleep(2)  # Wait for page load
                
                # REMOVE THESE LINES:
                # remaining_jobs = None
                # if total_limit is not None:
                #     remaining_jobs = total_limit - total_jobs
                #     if remaining_jobs <= 0:
                #         break
                
                # CHANGE THIS LINE - remove remaining_jobs parameter (let it use config):
                results = await perform_scraping(page, output_file)
                
                if results:
                    total_jobs += results
                    logger.info(f"Completed '{keyword}': {results} jobs scraped (total: {total_jobs})")
                else:
                    logger.warning(f"No results for keyword: '{keyword}'")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"All keywords processed! Total jobs scraped: {total_jobs}")
            logger.info(f"Results saved to: {output_file}")
            logger.info(f"{'='*60}")

            # Upload after all keywords are done:
            if total_jobs > 0 and os.path.exists(output_file):
                try:
                    from utility.google_drive_uploader import GoogleDriveUploader
                    
                    logger.info("Uploading all results to Google Drive...")
                    uploader = GoogleDriveUploader(scraper_type="google_jobs")
                    
                    # Note: We don't have per-keyword stats, so use total counts
                    upload_result = uploader.upload_scraper_results(
                        output_file, 
                        total_jobs, 
                        0,  # We don't track total skipped across keywords
                        0   # We don't track total failed across keywords
                    )
                    
                    if upload_result:
                        logger.info("Upload successful!")
                        logger.info(f"View file: {upload_result['main_file']['view_link']}")
                    else:
                        logger.error("Upload failed")
                except Exception as e:
                    logger.error(f"Google Drive upload error: {e}")
            
            
            logger.info("Press Enter to close the browser and exit...")
            await asyncio.get_event_loop().run_in_executor(None, input)
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.info("Press Enter to close the browser and exit...")
        await asyncio.get_event_loop().run_in_executor(None, input)
    finally:
        if browser:
            try:
                logger.info("Closing browser")
                await browser.close()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

async def run_linkedin_scraper():
    """Run the LinkedIn Saved Jobs scraper"""
    browser = None
    context = None
    
    try:
        logger.info("Starting LinkedIn Saved Jobs scraper")
        
        # Initialize Stealth with Playwright
        async with Stealth().use_async(async_playwright()) as p:
            logger.info("Launching browser for LinkedIn scraping")
            browser = await p.chromium.launch(
                headless=False,
                # args=[
                #     '--no-first-run',
                #     '--no-default-browser-check',
                #     '--disable-blink-features=AutomationControlled',
                #     '--disable-web-security',
                #     '--disable-features=VizDisplayCompositor',
                #     '--no-sandbox',
                #     '--disable-setuid-sandbox'
                # ]
            )
            
            # Create context with realistic settings
            context = await browser.new_context(
                # viewport={'width': 1366, 'height': 768},
                # user_agent=get_random_user_agent(),
                # locale='en-US',
                # timezone_id='Africa/Casablanca',
                # extra_http_headers={
                #     'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8,ar;q=0.7',
                #     'Accept-Encoding': 'gzip, deflate, br',
                #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
                # }
            )
            
            page = await context.new_page()
            
            # Load LinkedIn cookies (separate from Google cookies)
            await load_cookies(context, 'data/linkedin_cookies.json')
            
            # Navigate to LinkedIn
            logger.info("Navigating to LinkedIn")
            await page.goto("https://www.linkedin.com/my-items/saved-posts/", timeout=0)
            
            logger.info("LinkedIn page loaded. Please log in if needed.")
            logger.info("Press Enter here to start scraping saved jobs...")
            
            # Wait for user to press Enter
            await asyncio.get_event_loop().run_in_executor(None, input)
            
            # Save cookies after user interaction
            logger.info("Saving LinkedIn cookies...")
            # await save_cookies(context, 'data/linkedin_cookies.json')
            
            # Call the LinkedIn scraping function
            logger.info("Starting LinkedIn scraping process")
            results = await perform_linkedin_scraping(page)
            
            if results:
                logger.info(f"LinkedIn scraping completed successfully! Processed {results} jobs")
            else:
                logger.warning("LinkedIn scraping completed but no results returned")
            
            # Keep browser open until user wants to close    
            logger.info("=" * 60)
            logger.info("Press Enter to close the browser and exit...")
            await asyncio.get_event_loop().run_in_executor(None, input)
            
    except Exception as e:
        logger.error(f"An error occurred during LinkedIn scraping: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.info("=" * 60)
        logger.info("Press Enter to close the browser and exit...")
        await asyncio.get_event_loop().run_in_executor(None, input)
    finally:
        if browser:
            try:
                logger.info("Closing browser")
                await browser.close()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

async def main():
    """Main function with menu selection"""
    logger.info("Job Scraper Toolkit Starting...")
    
    while True:
        try:
            choice = get_user_choice()
            
            if choice == 1:
                logger.info("User selected Google Jobs Scraper")
                await run_google_scraper()
                # Don't break here - go back to menu
                print("\nGoogle Jobs Scraper completed. Returning to main menu...")
                
            elif choice == 2:
                logger.info("User selected LinkedIn Saved Jobs Scraper")
                await run_linkedin_scraper()
                # Don't break here - go back to menu
                print("\nLinkedIn Scraper completed. Returning to main menu...")
                
            elif choice == 3:
                logger.info("User chose to exit")
                print("\nGoodbye! 👋")
                break
                
        except KeyboardInterrupt:
            logger.info("Script terminated by user (Ctrl+C)")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main menu: {e}")
            print(f"\nAn error occurred: {e}")
            print("Returning to main menu...")

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