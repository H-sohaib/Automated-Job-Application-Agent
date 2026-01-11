import asyncio
import json
from datetime import datetime, timedelta
import re
import logging
import os
import random 
import signal
from typing import Dict, Optional, Tuple
# from job_hash_store import JobHashStore
from utility.job_hash_store import JobHashStore
from config import *

# Set up logging for the scraper module
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_flag
    logger.warning(f"Received signal {signum}. Initiating graceful shutdown...")
    shutdown_flag = True

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def random_sleep(range_tuple: Tuple[float, float]) -> float:
    """
    Get a random sleep duration within the specified range.
    
    Args:
        range_tuple: Tuple containing (min_duration, max_duration) in seconds
        
    Returns:
        float: Random duration between min and max values
    """
    return random.uniform(range_tuple[0], range_tuple[1])

def estimate_posted_date(posted_str: str, scraped_date: str) -> str:
    """
    Convert relative time to approximate date.
    ALWAYS returns a valid date - uses scraped_date as fallback.
    
    Args:
        posted_str: Relative time string (e.g., "3 days ago", "2 weeks ago")
        scraped_date: Current scraped timestamp (format: "YYYY-MM-DD HH:MM:SS")
        
    Returns:
        str: Estimated date in YYYY-MM-DD format (ALWAYS a valid date)
    """
    try:
        # Parse scraped date first (this is our fallback)
        scraped = datetime.strptime(scraped_date, "%Y-%m-%d %H:%M:%S")
        scraped_date_only = scraped.strftime("%Y-%m-%d")
        
        # If posted_str is empty, None, or not a string, return scraped date
        if not posted_str or not isinstance(posted_str, str) or posted_str.strip() == "":
            logger.debug(f"No valid posted_str, using scraped date: {scraped_date_only}")
            return scraped_date_only
        
        # If posted_str is "N/A" or similar, return scraped date
        if posted_str.lower() in ['n/a', 'na', 'none', 'unknown', 'failed to extract']:
            logger.debug(f"Posted_str is '{posted_str}', using scraped date: {scraped_date_only}")
            return scraped_date_only
        
        # Extract number and unit (e.g., "3 days ago" → 3, "days")
        # Handles: "3 days ago", "2 weeks ago", "5h", "2d", etc.
        match = re.search(r'(\d+)\s*(hour|day|week|month|h|d|w|m)s?', posted_str.lower())
        if not match:
            # Can't parse - return scraped date as fallback
            logger.debug(f"Cannot parse '{posted_str}', using scraped date: {scraped_date_only}")
            return scraped_date_only
        
        amount = int(match.group(1))
        unit = match.group(2)
        
        # Calculate offset based on unit
        if 'h' in unit:  # hour or h
            offset = timedelta(hours=amount)
        elif 'd' in unit:  # day or d
            offset = timedelta(days=amount)
        elif 'w' in unit:  # week or w
            offset = timedelta(weeks=amount)
        elif 'm' in unit:  # month or m
            offset = timedelta(days=amount * 30)  # Approximate
        else:
            # Unknown unit - return scraped date
            logger.debug(f"Unknown unit '{unit}' in '{posted_str}', using scraped date: {scraped_date_only}")
            return scraped_date_only
        
        # Calculate estimated date
        estimated = scraped - offset
        estimated_str = estimated.strftime("%Y-%m-%d")
        logger.debug(f"Estimated posted date: '{posted_str}' → {estimated_str}")
        return estimated_str
        
    except Exception as e:
        # ANY error: return scraped date as safe fallback
        logger.warning(f"Error estimating posted date from '{posted_str}': {e}. Using scraped date.")
        try:
            scraped = datetime.strptime(scraped_date, "%Y-%m-%d %H:%M:%S")
            return scraped.strftime("%Y-%m-%d")
        except:
            # Last resort: return today's date
            return datetime.now().strftime("%Y-%m-%d")

async def human_sleep(range_tuple: Tuple[float, float]) -> None:
    """
    Sleep for a random duration within the specified range to mimic human behavior.
    
    Args:
        range_tuple: Tuple containing (min_duration, max_duration) in seconds
    """
    duration = random_sleep(range_tuple)
    logger.debug(f"Human-like sleep for {duration:.2f} seconds")
    await asyncio.sleep(duration)

def get_json_filename() -> str:
    """
    Generate a timestamp-based filename for the JSON output.
    
    Returns:
        str: Formatted filename with timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"data/google_jobs/google_jobs_{timestamp}.json"

def save_job_incrementally(job_data: Dict, filename: str) -> bool:
    """
    Save a job to a JSON file incrementally.
    If the file exists, read it, append the job, and write it back.
    If not, create a new file with this job as the first element.
    
    Args:
        job_data: Dictionary containing job information
        filename: Path to the JSON file
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    job_title = job_data.get('title', 'Unknown')
    job_company = job_data.get('company', 'Unknown')
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Check if file exists and has content
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            # Read existing jobs
            with open(filename, 'r', encoding='utf-8') as f:
                try:
                    jobs = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error in {filename}: {e}. Starting fresh for job '{job_title}' at '{job_company}'")
                    jobs = []
        else:
            # Create new file with empty array
            jobs = []
        
        # Append new job
        jobs.append(job_data)
        
        # Write back to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully saved job '{job_title}' at '{job_company}' to {filename} (total: {len(jobs)} jobs)")
        return True
        
    except PermissionError as e:
        logger.error(f"Permission denied saving job '{job_title}' at '{job_company}' to {filename}: {e}")
        return False
    except IOError as e:
        logger.error(f"IO error saving job '{job_title}' at '{job_company}' to {filename}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving job '{job_title}' at '{job_company}' to {filename}: {e}")
        return False

async def extract_basic_job_info(job_element) -> Optional[Dict]:
    """
    Extract basic job information from a job element.
    
    Args:
        job_element: Playwright element containing job information
        
    Returns:
        Dict or None: Basic job information or None if extraction fails
    """
    try:
        # Extract job title
        title_el = await job_element.query_selector(JOB_TITLE_SELECTOR)
        if not title_el:
            logger.debug("Job element missing title selector")
            return None
            
        title = await title_el.text_content()
        if not title:
            logger.debug("Job element has empty title")
            return None
        
        # Extract company
        company_el = await job_element.query_selector(COMPANY_SELECTOR)
        company = await company_el.text_content() if company_el else "N/A"
        
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
        
        return {
            'title': title.strip(),
            'company': company.strip(),
            'location': location.strip(),
            'platform': platform.strip(),
            'job_type': job_type.strip(),
            'posted': age.strip(),
            'salary': salary.strip()
        }
        
    except Exception as e:
        logger.warning(f"Error extracting basic job info: {e}")
        return None

async def extract_detailed_job_info(page, job_element, basic_info: Dict) -> Optional[Dict]:
    """
    Extract detailed job information by clicking on the job element.
    """
    job_title = basic_info.get('title', 'Unknown')
    job_company = basic_info.get('company', 'Unknown')
    
    try:
        # Click on the job
        await job_element.click()
        logger.debug(f"Clicked on job: '{job_title}' at '{job_company}'")

        # Initialize variables
        platform_links = []
        description = ""

        # Wait for the job details panel to load
        await human_sleep(SLEEP_MEDIUM)
        
        active_panel = await page.query_selector(ACTIVE_JOB_PANEL_SELECTOR)
        
        if active_panel:
            # Extract description
            desc_elements = await active_panel.query_selector_all(DESCRIPTION_CONTAINER_SELECTOR)
            if desc_elements:
                for desc_el in desc_elements:
                    content = await desc_el.text_content()
                    if content:
                        description += content + " "
                description = description.strip()
            
            if not description:
                description = "No description available"
                logger.debug(f"No description found for job: '{job_title}' at '{job_company}'")

            # Extract platform links
            link_elements = await active_panel.query_selector_all(PLATFORM_LINKS_SELECTOR)
            for link in link_elements:
                href = await link.get_attribute('href')
                text = await link.text_content()
                if href:
                    platform_links.append({
                        'text': text.strip() if text else '', 
                        'href': href
                    })
            
            logger.debug(f"Extracted details for job: '{job_title}' at '{job_company}' - {len(platform_links)} links found")
        else:
            logger.warning(f"Could not find active job panel for '{job_title}' at '{job_company}'")
            description = "Failed to locate job details panel"

        # Get scraped date first
        scraped_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create complete job data with estimated posted date
        job_data = {
            **basic_info,
            'description': description,
            'platform_links': platform_links,
            'scraped_date': scraped_date,
            'estimated_posted_date': estimate_posted_date(basic_info.get('posted', ''), scraped_date)  # ADD THIS LINE
        }
        
        return job_data
        
    except Exception as e:
        logger.error(f"Error extracting detailed job info for '{job_title}' at '{job_company}': {e}")
        return None


async def perform_scraping(page, output_filename: str = None, max_jobs_override: Optional[int] = None) -> Optional[int]:
    """
    Scrape job listings from Google Jobs search results with scrolling support.
    
    Args:
        page: The Playwright page object to use for scraping
        output_filename: Optional filename to save results
        max_jobs_override: Optional override for max jobs (used for multi-keyword scraping)
        
    Returns:
        int or None: Number of jobs scraped, or None if scraping failed
    """
    global shutdown_flag
    
    logger.info("Starting job scraping process...")
    
    try:
        # Initialize the job hash store
        read_only_mode = TESTING_MODE
        hash_store = JobHashStore(read_only=read_only_mode)
        # hash_store.cleanup_expired()
        if read_only_mode:
            logger.warning("Hash storage is DISABLED - running in testing mode")
        
        stats = hash_store.get_stats()
        logger.info(f"Job hash store initialized - {stats['total_jobs_tracked']} jobs tracked")
        
        # Use provided filename or create new one
        if not output_filename:
            output_filename = get_json_filename()
        logger.info(f"Jobs will be saved to: {output_filename}")
        
        # Wait for job listings to load
        try:
            await page.wait_for_selector(JOB_CONTAINER_SELECTOR, timeout=10000)
            logger.debug("Job container selector found successfully")
        except Exception as e:
            logger.error(f"Could not find job listings: {e}")
            return None
        
        # Initialize tracking variables
        processed_job_keys = set()
        jobs_count = 0
        skipped_duplicates = 0
        failed_extractions = 0
        jobs_to_send = []
        scroll_attempts = 0
        
        # Use override if provided, otherwise use config
        job_limit = max_jobs_override if max_jobs_override is not None else (MAX_JOBS_TO_SCRAPE if MAX_JOBS_TO_SCRAPE > 0 else None)
        limit_str = job_limit if job_limit is not None else "unlimited"
        logger.info(f"Starting scraping loop - target: {limit_str} jobs, max scrolls: {MAX_SCROLL_ATTEMPTS}")
        
        while scroll_attempts < MAX_SCROLL_ATTEMPTS and not shutdown_flag:
            # Get current job elements
            job_elements = await page.query_selector_all(JOB_CONTAINER_SELECTOR)
            current_job_count = len(job_elements)
            
            logger.info(f"Found {current_job_count} job elements on page (scroll attempt {scroll_attempts})")
            
            # Process visible jobs
            job_limit_reached = False  # Add flag to track if limit was reached
            for job_element in job_elements:
                if shutdown_flag:
                    logger.warning("Shutdown signal received, stopping job processing")
                    break
                
                # Extract basic job information
                basic_info = await extract_basic_job_info(job_element)
                if not basic_info:
                    failed_extractions += 1
                    continue
                
                job_title = basic_info['title']
                job_company = basic_info['company']
                
                # Skip if we've already processed this job in this session
                job_key = f"{job_title}_{job_company}"
                if job_key in processed_job_keys:
                    logger.info(f"Skipping already processed job: '{job_title}' at '{job_company}'")
                    continue
                
                processed_job_keys.add(job_key)
                
                # Check for basic duplicates using hash store
                preliminary_job_data = {
                    'title': job_title,
                    'company': job_company,
                    'location': basic_info['location']
                }
                
                if hash_store.is_basic_duplicate(preliminary_job_data):
                    logger.info(f"Skipping basic duplicate: '{job_title}' at '{job_company}'")
                    skipped_duplicates += 1
                    continue

                # Extract detailed job information
                detailed_info = await extract_detailed_job_info(page, job_element, basic_info)
                if not detailed_info:
                    logger.warning(f"Failed to extract detailed info for: '{job_title}' at '{job_company}'")
                    failed_extractions += 1
                    continue
                
                # Final duplicate check with complete data
                if hash_store.is_duplicate(detailed_info):
                    logger.info(f"Skipping confirmed duplicate after full check: '{job_title}' at '{job_company}'")
                    skipped_duplicates += 1
                    continue
                
                # Save job incrementally
                if save_job_incrementally(detailed_info, output_filename):
                    jobs_count += 1
                    jobs_to_send.append(detailed_info)
                    logger.debug(f"Successfully processed job {jobs_count}: '{job_title}' at '{job_company}'")
                else:
                    logger.error(f"Failed to save job: '{job_title}' at '{job_company}'")
                    continue
                
                # Check if we've reached the maximum number of jobs
                if job_limit is not None and jobs_count >= job_limit:
                    logger.info(f"Reached maximum job count ({jobs_count})")
                    job_limit_reached = True
                    break
            
            # Break out of outer loop if job limit reached or shutdown requested
            if job_limit_reached or shutdown_flag:
                break
            
            # Scroll down to load more jobs
            logger.info("Scrolling to load more jobs...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await human_sleep(SLEEP_SCROLL)
            
            # Check if new jobs were loaded
            new_job_elements = await page.query_selector_all(JOB_CONTAINER_SELECTOR)
            if len(new_job_elements) <= current_job_count:
                scroll_attempts += 1
                logger.info(f"No new jobs loaded, scroll attempt {scroll_attempts}/{MAX_SCROLL_ATTEMPTS}")
            else:
                scroll_attempts = 0  # Reset counter if new jobs found
                logger.info(f"Found {len(new_job_elements) - current_job_count} new jobs after scrolling")
        
        # Log final statistics
        logger.info(f"Scraping completed! Summary:")
        logger.info(f"  - Total jobs processed: {jobs_count}")
        logger.info(f"  - Duplicates skipped: {skipped_duplicates}")
        logger.info(f"  - Failed extractions: {failed_extractions}")
        logger.info(f"  - Shutdown requested: {shutdown_flag}")
        
        return jobs_count
        
    except Exception as e:
        logger.error(f"Critical error in perform_scraping: {e}")
        return None