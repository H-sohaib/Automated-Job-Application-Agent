import json
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError
from urllib.parse import quote_plus
from typing import Dict, List
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class JobData:
    """Simple job data structure"""
    title: str = "Not found"
    company: str = "Not found"
    location: str = "Not found"
    link: str = "No link found"
    posted_date: str = "Not found"
    scrape_time: str = ""
    job_index: int = 0

class SimpleGoogleJobsScraper:
    """
    Simple Google Jobs scraper - easy to configure when selectors break
    """
    
    def __init__(self):
        # Updated selectors based on actual Google Jobs structure
        self.SELECTORS = {
            'jobs_container': '#rso, .dURPMd, .ULSxyf',
            'job_cards': '.MjjYud, .g, div[data-hveid], div[jscontroller]',
            'job_title': 'h3, .LC20lb, .DKV0Md, [role="heading"]',
            'company': '.VuuXrf, .tjvcx, span:has-text("·")',
            'location': '.rllt__details, .tjvcx',
            'job_link': 'a[href*="jobs"], a[data-ved], h3 a',
            'posted_date': '.MUxGbd, .f, .s, span:contains("ago"), span:contains("day")'
        }
        
        # Simple settings
        self.SETTINGS = {
            'wait_timeout': 30,
            'scroll_delay': 3,
            'max_scrolls': 5,
            'headless': True,
            'captcha_wait': 60  # Wait time for manual CAPTCHA solving
        }
    
    def build_url(self, query: str, location: str = None) -> str:
        """Build Google Jobs URL"""
        base_url = "https://www.google.com/search"
        params = [f"q={quote_plus(query)}", "ibp=htl;jobs"]
        
        if location:
            params.append(f"l={quote_plus(location)}")
        
        url = f"{base_url}?{'&'.join(params)}"
        logger.info(f"Built URL: {url}")
        return url
    
    def handle_captcha(self, page):
        """Handle CAPTCHA if it appears"""
        captcha_selectors = [
            '#captcha-form',
            '.g-recaptcha',
            'iframe[src*="recaptcha"]',
            '[id*="captcha"]',
            'form[action*="captcha"]'
        ]
        
        for selector in captcha_selectors:
            try:
                captcha = page.query_selector(selector)
                if captcha and captcha.is_visible():
                    logger.warning("CAPTCHA detected! Please solve it manually...")
                    print("\n🚨 CAPTCHA DETECTED!")
                    print("Please solve the CAPTCHA in the browser window.")
                    print(f"Waiting {self.SETTINGS['captcha_wait']} seconds...")
                    
                    # Wait for CAPTCHA to be solved
                    start_time = time.time()
                    while time.time() - start_time < self.SETTINGS['captcha_wait']:
                        # Check if CAPTCHA is gone
                        if not page.query_selector(selector) or not page.query_selector(selector).is_visible():
                            logger.info("CAPTCHA solved! Continuing...")
                            return True
                        time.sleep(2)
                    
                    logger.error("CAPTCHA timeout - please try again")
                    return False
            except:
                continue
        
        return True  # No CAPTCHA found
    
    def wait_for_jobs(self, page) -> bool:
        """Wait for jobs to load"""
        # First handle any CAPTCHA
        if not self.handle_captcha(page):
            return False
        
        # Look for any jobs container
        for container_selector in self.SELECTORS['jobs_container'].split(', '):
            try:
                page.wait_for_selector(container_selector.strip(), timeout=10000)
                logger.info(f"Found jobs container with: {container_selector}")
                break
            except TimeoutError:
                continue
        
        # Wait a bit for content to load
        time.sleep(3)
        
        # Check if we have any job-like content
        for job_selector in self.SELECTORS['job_cards'].split(', '):
            try:
                elements = page.query_selector_all(job_selector.strip())
                if elements and len(elements) > 0:
                    logger.info(f"Found {len(elements)} potential job elements with: {job_selector}")
                    return True
            except:
                continue
        
        logger.warning("No job elements found")
        return True  # Continue anyway, might find jobs later
    
    def scroll_for_more_jobs(self, page):
        """Scroll to load more jobs"""
        logger.info("Scrolling for more jobs...")
        
        for i in range(self.SETTINGS['max_scrolls']):
            # Scroll down
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(self.SETTINGS['scroll_delay'])
            
            # Try to click "Show more" or "Load more" buttons
            more_buttons = [
                'button:has-text("Show more")',
                'button:has-text("More jobs")',
                'button:has-text("Load more")',
                '[data-ved*="more"]'
            ]
            
            for button_selector in more_buttons:
                try:
                    button = page.query_selector(button_selector)
                    if button and button.is_visible():
                        button.click()
                        time.sleep(2)
                        logger.info(f"Clicked load more button: {button_selector}")
                        break
                except:
                    continue
            
            # Count potential job elements
            total_elements = 0
            for job_selector in self.SELECTORS['job_cards'].split(', '):
                try:
                    elements = page.query_selector_all(job_selector.strip())
                    total_elements = max(total_elements, len(elements))
                except:
                    continue
            
            logger.info(f"Scroll {i+1}: Found {total_elements} total elements")
        
        logger.info("Scrolling complete")
    
    def extract_text(self, element) -> str:
        """Safely extract text from element"""
        if not element:
            return "Not found"
        try:
            text = element.inner_text().strip()
            return text if text else "Not found"
        except:
            return "Error extracting"
    
    def find_job_data_in_element(self, element) -> JobData:
        """Try to extract job data from any element"""
        job = JobData()
        
        # Try to find title in element
        for title_selector in self.SELECTORS['job_title'].split(', '):
            try:
                title_elem = element.query_selector(title_selector.strip())
                if title_elem:
                    title_text = self.extract_text(title_elem)
                    if title_text and title_text != "Not found" and len(title_text) > 3:
                        job.title = title_text
                        break
            except:
                continue
        
        # Try to find company
        for company_selector in self.SELECTORS['company'].split(', '):
            try:
                company_elem = element.query_selector(company_selector.strip())
                if company_elem:
                    company_text = self.extract_text(company_elem)
                    if company_text and company_text != "Not found":
                        job.company = company_text
                        break
            except:
                continue
        
        # Try to find location
        for location_selector in self.SELECTORS['location'].split(', '):
            try:
                location_elem = element.query_selector(location_selector.strip())
                if location_elem:
                    location_text = self.extract_text(location_elem)
                    if location_text and location_text != "Not found":
                        job.location = location_text
                        break
            except:
                continue
        
        # Try to find link
        for link_selector in self.SELECTORS['job_link'].split(', '):
            try:
                link_elem = element.query_selector(link_selector.strip())
                if link_elem:
                    href = link_elem.get_attribute('href')
                    if href:
                        job.link = href
                        break
            except:
                continue
        
        # Try to find date
        for date_selector in self.SELECTORS['posted_date'].split(', '):
            try:
                date_elem = element.query_selector(date_selector.strip())
                if date_elem:
                    date_text = self.extract_text(date_elem)
                    if date_text and date_text != "Not found":
                        job.posted_date = date_text
                        break
            except:
                continue
        
        return job
    
    def extract_jobs(self, page) -> List[JobData]:
        """Extract job data from page"""
        jobs = []
        all_elements = []
        
        # Collect all potential job elements
        for job_selector in self.SELECTORS['job_cards'].split(', '):
            try:
                elements = page.query_selector_all(job_selector.strip())
                all_elements.extend(elements)
            except Exception as e:
                logger.debug(f"Selector {job_selector} failed: {e}")
                continue
        
        logger.info(f"Found {len(all_elements)} total elements to check")
        
        # Remove duplicates (keep unique elements)
        unique_elements = []
        seen_elements = set()
        for elem in all_elements:
            try:
                # Use element's text content as a simple way to identify duplicates
                text_content = elem.inner_text()[:100]  # First 100 chars
                if text_content not in seen_elements:
                    seen_elements.add(text_content)
                    unique_elements.append(elem)
            except:
                unique_elements.append(elem)  # Add anyway if we can't get text
        
        logger.info(f"Processing {len(unique_elements)} unique elements")
        
        for i, element in enumerate(unique_elements):
            try:
                job = self.find_job_data_in_element(element)
                job.scrape_time = datetime.now().isoformat()
                job.job_index = i
                
                # Only add if we found meaningful data
                if (job.title != "Not found" and len(job.title) > 3) or \
                   (job.company != "Not found" and len(job.company) > 2):
                    jobs.append(job)
                    logger.debug(f"Found job {i}: {job.title} at {job.company}")
                
            except Exception as e:
                logger.warning(f"Error extracting job {i}: {e}")
                continue
        
        logger.info(f"Successfully extracted {len(jobs)} jobs")
        return jobs
    
    def scrape_jobs(self, query: str, location: str = None, headless: bool = None, max_jobs: int = 50) -> List[Dict]:
        """Main scraping function"""
        if headless is None:
            headless = self.SETTINGS['headless']
        
        url = self.build_url(query, location)
        
        try:
            with sync_playwright() as p:
                # Launch browser with more realistic settings
                browser = p.chromium.launch(
                    headless=headless,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ]
                )
                
                # Create page with realistic settings
                page = browser.new_page()
                page.set_viewport_size({"width": 1920, "height": 1080})
                
                # Set headers to look more like a real browser
                page.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                })
                
                # Navigate to URL
                logger.info(f"Navigating to: {url}")
                page.goto(url, wait_until='networkidle', timeout=60000)
                
                # Wait for jobs to load (includes CAPTCHA handling)
                if not self.wait_for_jobs(page):
                    logger.error("Failed to load jobs or solve CAPTCHA")
                    browser.close()
                    return []
                
                # Scroll for more jobs
                self.scroll_for_more_jobs(page)
                
                # Extract jobs
                jobs = self.extract_jobs(page)
                
                browser.close()
                
                # Limit results and convert to dict
                jobs = jobs[:max_jobs]
                return [asdict(job) for job in jobs]
                
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return []
    
    def save_jobs(self, jobs: List[Dict], filename: str = "jobs.json"):
        """Save jobs to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(jobs)} jobs to {filename}")
        except Exception as e:
            logger.error(f"Failed to save jobs: {e}")
    
    def update_selectors(self, **new_selectors):
        """Update selectors when they break"""
        for key, value in new_selectors.items():
            if key in self.SELECTORS:
                old_value = self.SELECTORS[key]
                self.SELECTORS[key] = value
                logger.info(f"Updated {key}: '{old_value}' -> '{value}'")
            else:
                logger.warning(f"Unknown selector: {key}")

# Simple usage functions
def scrape_google_jobs(query: str, location: str = None, headless: bool = True, max_jobs: int = 50) -> List[Dict]:
    """Simple function to scrape Google Jobs"""
    scraper = SimpleGoogleJobsScraper()
    return scraper.scrape_jobs(query, location, headless, max_jobs)

def save_jobs_to_file(jobs: List[Dict], filename: str = "jobs.json"):
    """Save jobs to file"""
    scraper = SimpleGoogleJobsScraper()
    scraper.save_jobs(jobs, filename)

if __name__ == "__main__":
    # Example usage
    scraper = SimpleGoogleJobsScraper()
    
    # Search for jobs
    jobs = scraper.scrape_jobs(
        query="IT jobs internship",
        location="Morocco", 
        headless=False,  # Set to True for headless mode
        max_jobs=20
    )
    
    # Display results
    if jobs:
        print(f"\n✅ Found {len(jobs)} jobs:")
        for i, job in enumerate(jobs[:3], 1):  # Show first 3
            print(f"\n{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Posted: {job['posted_date']}")
        
        # Save to file
        scraper.save_jobs(jobs, "it_internships.json")
        print(f"\n💾 All jobs saved to it_internships.json")
    else:
        print("❌ No jobs found")
        print("\n💡 Try updating selectors if this persists:")
        print("scraper.update_selectors(job_cards='your_new_selector')")