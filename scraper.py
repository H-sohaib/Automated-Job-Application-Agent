import asyncio
import json
from datetime import datetime
import logging
import os
import pdb 
import random 
from job_hash_store import JobHashStore

# Set up logging for the scraper module
logger = logging.getLogger(__name__)

# CSS Selectors - all defined at the top for easy maintenance
JOB_CONTAINER_SELECTOR = '.EimVGf'
JOB_TITLE_SELECTOR = '.tNxQIb.PUpOsf'
COMPANY_SELECTOR = '.wHYlTd.MKCbgd.a3jPc'
LOCATION_PLATFORM_SELECTOR = '.wHYlTd.FqK3wc.MKCbgd'
JOB_TYPE_SELECTOR = 'span.Yf9oye[aria-label*="Employment type"], span.Yf9oye[aria-label*="Job Type"], .nYym1e span.RcZtZb'
AGE_SELECTOR = 'span.Yf9oye[aria-label*="Posted"]'
SALARY_SELECTOR = 'span.Yf9oye[aria-label*="Salary"]'
DESCRIPTION_CONTAINER_SELECTOR = '.NgUYpe div span.hkXmid, .NgUYpe div span.us2QZb'
SHOW_MORE_BUTTON_SELECTOR = 'div[jsname="G7vtgf"] div[role="button"]'
ACTIVE_JOB_PANEL_SELECTOR = 'div.BIB1wf[style*="display: block"]'
PLATFORM_LINKS_SELECTOR = '.nNzjpf-cS4Vcb-PvZLI-wxkYzf .yVRmze-s2gQvd a'

# Configuration
MAX_JOBS_TO_SCRAPE = 10
MAX_SCROLL_ATTEMPTS = 10
SCROLL_DELAY = 2  # seconds

# Human-like timing configurations
SLEEP_SHORT = (1.0, 2.5)      # Quick actions (clicks)
SLEEP_MEDIUM = (2.0, 4.0)     # Reading content, waiting for panels
SLEEP_LONG = (3.5, 6.0)       # Waiting for page loads, scrolling
SLEEP_SCROLL = (1.5, 3.0)     # Scrolling delay

def random_sleep(range_tuple):
    """Get a random sleep duration within the specified range"""
    return random.uniform(range_tuple[0], range_tuple[1])

async def human_sleep(range_tuple):
    """Sleep for a random duration within the specified range"""
    duration = random_sleep(range_tuple)
    logger.debug(f"Sleeping for {duration:.2f} seconds")
    await asyncio.sleep(duration)

def get_json_filename():
    """Generate a timestamp-based filename for the JSON output"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"data/jobs/jobs_{timestamp}.json"

def save_job_incrementally(job_data, filename):
    """
    Save a job to a JSON file incrementally.
    If the file exists, read it, append the job, and write it back.
    If not, create a new file with this job as the first element.
    """
    try:
        # Check if file exists and has content
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            # Read existing jobs
            with open(filename, 'r', encoding='utf-8') as f:
                try:
                    jobs = json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"Error parsing JSON in {filename}, starting fresh")
                    jobs = []
        else:
            # Create new file with empty array
            jobs = []
        
        # Append new job
        jobs.append(job_data)
        
        # Write back to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Added job '{job_data['title']}' to {filename} (total: {len(jobs)})")
        return True
    except Exception as e:
        logger.error(f"Error saving job '{job_data['title']}' to {filename}: {e}")
        return False

async def perform_scraping(page):
    """
    Scrape job listings from Google Jobs search results with scrolling support.
    
    Args:
        page: The Playwright page object to use for scraping
    """
    logger.info("Starting scraping process...")
    
    # Initialize the job hash store
    hash_store = JobHashStore()
    # Clean up expired job hashes at the start of each scraping session
    hash_store.cleanup_expired()
    
    # Get hash store stats for logging
    stats = hash_store.get_stats()
    logger.info(f"Job hash store stats: {stats['total_jobs_tracked']} jobs tracked, oldest from {stats['oldest_job_date']}")
    
    # Create output filename at start (so all jobs go to the same file)
    output_filename = get_json_filename()
    logger.info(f"Jobs will be saved to: {output_filename}")
    
    # Wait for the job listings to load
    try:
        await page.wait_for_selector(JOB_CONTAINER_SELECTOR, timeout=10000)
    except Exception as e:
        logger.error(f"Could not find job listings: {e}")
        return []
    
    # Track processed jobs to avoid duplicates
    processed_job_titles = set()
    jobs_count = 0 
    skipped_duplicates = 0
    # Scroll and load more jobs
    scroll_attempts = 0
    
    
    while scroll_attempts < MAX_SCROLL_ATTEMPTS:
        # Get current job elements
        job_elements = await page.query_selector_all(JOB_CONTAINER_SELECTOR)
        current_job_count = len(job_elements)
        
        logger.info(f"Found {current_job_count} jobs so far...")
        
        # breakpoint() 
        # Process visible job   s
        for job_element in job_elements:
            try:
                # Extract job title for tracking
                title_el = await job_element.query_selector(JOB_TITLE_SELECTOR)
                if not title_el:
                    continue
                    
                title = await title_el.text_content()
                company_el = await job_element.query_selector(COMPANY_SELECTOR)
                company = await company_el.text_content() if company_el else "N/A"
                
                # Skip if we've already processed this job in this session
                job_key = f"{title}_{company}"
                if job_key in processed_job_titles:
                    continue
                    
                processed_job_titles.add(job_key)
                
                # Process location and platform
                loc_platform_el = await job_element.query_selector(LOCATION_PLATFORM_SELECTOR)
                loc_platform = await loc_platform_el.text_content() if loc_platform_el else ""
                location = loc_platform.split('•')[0].strip() if '•' in loc_platform else loc_platform
                platform = loc_platform.split('•')[1].strip() if '•' in loc_platform and len(loc_platform.split('•')) > 1 else "N/A"
                
                # Get other job details
                job_type_el = await job_element.query_selector(JOB_TYPE_SELECTOR)
                age_el = await job_element.query_selector(AGE_SELECTOR)
                salary_el = await job_element.query_selector(SALARY_SELECTOR)
                
                job_type = await job_type_el.text_content() if job_type_el else "N/A"
                age = await age_el.text_content() if age_el else "N/A"
                salary = await salary_el.text_content() if salary_el else "N/A"
                
                # Create a preliminary job data for BASIC duplicate checking
                preliminary_job_data = {
                    'title': title,
                    'company': company,
                    'location': location
                }
                
                # FIRST CHECK: Use basic hash to quickly check if job might be a duplicate
                # This avoids clicking on obvious duplicates
                if hash_store.is_basic_duplicate(preliminary_job_data):
                    logger.debug(f"Skipping likely duplicate job: {title} at {company}")
                    skipped_duplicates += 1
                    continue

                # Get description by clicking on the job
                await job_element.click()
                logger.info(f"Clicked on job: {title}")

                # Initialize platform_links before try block
                platform_links = []
                description = ""

                # Wait for the job details panel to load fully
                try:
                    # First wait for the job details panel itself to be visible
                    # await page.wait_for_selector('.NgUYpe', timeout=10000)
                    await human_sleep(SLEEP_MEDIUM)  # Give it more time to fully render
                    
                    active_panel = await page.query_selector(ACTIVE_JOB_PANEL_SELECTOR)
                    
                    # Extract description with more targeted selectors
                    if active_panel:
                        # Description extraction (as before)
                        desc_elements = await active_panel.query_selector_all(DESCRIPTION_CONTAINER_SELECTOR)
                        if desc_elements:
                            for desc_el in desc_elements:
                                content = await desc_el.text_content()
                                if content:
                                    description += content + " "
                            description = description.strip()
                        if not description:
                            description = "No description available"

                        # ----------- PLATFORM LINKS EXTRACTION -----------
                        link_elements = await active_panel.query_selector_all(PLATFORM_LINKS_SELECTOR)
                        for link in link_elements:
                            href = await link.get_attribute('href')
                            text = await link.text_content()
                            if href:
                                platform_links.append({'text': text.strip() if text else '', 'href': href})

                    else:
                        logger.warning(f"Could not find active job panel for {title}")
                        description = "Failed to locate job details panel"
                        platform_links = []
                except Exception as e:
                    logger.error(f"Error while loading job details panel for {title}: {e}")
                    description = "Failed to load job details panel"
                
                # Create job data dictionary
                job_data = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'platform': platform,
                    'job_type': job_type,
                    'posted': age,
                    'salary': salary,
                    'description': description,
                    'platform_links': platform_links,
                    'scraped_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # SECOND CHECK: Now do a full hash check with the complete data including description
                if hash_store.is_duplicate(job_data):
                    logger.debug(f"Skipping confirmed duplicate job after checking description: {title} at {company}")
                    skipped_duplicates += 1
                    continue
                
                # Save this job incrementally to our single file
                if save_job_incrementally(job_data, output_filename):
                    jobs_count += 1  # Increment counter only on successful save
                # Check if we've reached the maximum number of jobs
                if jobs_count >= MAX_JOBS_TO_SCRAPE:
                    logger.info(f"Reached maximum job count ({jobs_count}), skipped {skipped_duplicates} duplicates")
                    return
                    
                    
            except Exception as e:
                logger.error(f"Error scraping job: {e}")
        
        # Scroll down to load more jobs
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await human_sleep(SLEEP_SCROLL)  # Wait for new jobs to load
        
        # Check if we loaded new jobs after scrolling
        new_job_elements = await page.query_selector_all(JOB_CONTAINER_SELECTOR)
        if len(new_job_elements) <= current_job_count:
            scroll_attempts += 1
            logger.info(f"No new jobs loaded, attempt {scroll_attempts}/{MAX_SCROLL_ATTEMPTS}")
        else:
            # Reset counter if we found new jobs
            scroll_attempts = 0
        
    
    logger.info(f"Scraping completed! Found {jobs_count} jobs")
    # return jobs