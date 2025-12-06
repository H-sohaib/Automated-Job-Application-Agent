import random
import logging
import os
from typing import List, Dict, Optional, Tuple
import re
import asyncio
import json
from datetime import datetime, timedelta

# Import from main config
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

# Set up logging for the LinkedIn scraper module
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = False

def load_scraped_ids(filename='data/scraped_post_ids.json'):
    """Load scraped post IDs from a file."""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return set(json.load(f))
    except Exception as e:
        logger.error(f"Error loading scraped IDs: {e}")
    return set()

def save_scraped_id(post_id, filename='data/scraped_post_ids.json'):
    """Save a new scraped post ID to the file."""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        scraped_ids = load_scraped_ids(filename)
        scraped_ids.add(post_id)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(list(scraped_ids), f, indent=2)
    except Exception as e:
        logger.error(f"Error saving scraped ID: {e}")

def random_sleep(range_tuple: Tuple[float, float]) -> float:
    """Get a random sleep duration within the specified range."""
    return random.uniform(range_tuple[0], range_tuple[1])

async def human_sleep(range_tuple: Tuple[float, float]) -> None:
    """Sleep for a random duration within the specified range to mimic human behavior."""
    duration = random_sleep(range_tuple)
    logger.debug(f"Human-like sleep for {duration:.2f} seconds")
    await asyncio.sleep(duration)

def get_json_filename() -> str:
    """Generate a timestamp-based filename for the JSON output."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"data/linkedin_jobs/linkedin_jobs_{timestamp}.json"

def estimate_posted_date(posted_str: str, scraped_date: str) -> str:
    """
    Convert relative time to approximate date for LinkedIn posts.
    ALWAYS returns a valid date - uses scraped_date as fallback.
    
    Args:
        posted_str: Relative time string (e.g., "2h", "3d", "1w")
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
        
        # LinkedIn format: "2h", "3d", "1w", "2mo"
        match = re.search(r'(\d+)\s*(h|d|w|mo|min)', posted_str.lower())
        if not match:
            logger.debug(f"Cannot parse '{posted_str}', using scraped date: {scraped_date_only}")
            return scraped_date_only
        
        amount = int(match.group(1))
        unit = match.group(2)
        
        # Calculate offset
        if 'h' in unit:
            offset = timedelta(hours=amount)
        elif 'min' in unit:
            offset = timedelta(minutes=amount)
        elif 'd' in unit:
            offset = timedelta(days=amount)
        elif 'w' in unit:
            offset = timedelta(weeks=amount)
        elif 'mo' in unit:
            offset = timedelta(days=amount * 30)
        else:
            logger.debug(f"Unknown unit '{unit}', using scraped date: {scraped_date_only}")
            return scraped_date_only
        
        estimated = scraped - offset
        estimated_str = estimated.strftime("%Y-%m-%d")
        logger.debug(f"Estimated posted date: '{posted_str}' → {estimated_str}")
        return estimated_str
        
    except Exception as e:
        logger.warning(f"Error estimating posted date from '{posted_str}': {e}")
        try:
            scraped = datetime.strptime(scraped_date, "%Y-%m-%d %H:%M:%S")
            return scraped.strftime("%Y-%m-%d")
        except:
            return datetime.now().strftime("%Y-%m-%d")

def extract_post_id_from_link(post_link: str) -> Optional[str]:
    """Extract post ID from LinkedIn post link."""
    try:
        if post_link and post_link != 'Failed to extract':
            # Extract from URLs like: https://www.linkedin.com/feed/update/urn:li:activity:7380917238549340160
            if 'urn:li:activity:' in post_link:
                return post_link.split('urn:li:activity:')[-1].split('/')[0]
        return None
    except Exception as e:
        logger.warning(f"Error extracting post ID from link '{post_link}': {e}")
        return None

def extract_post_id_from_urn(urn: str) -> Optional[str]:
    """Extract post ID from URN attribute."""
    try:
        if urn and 'urn:li:activity:' in urn:
            return urn.split(':')[-1]
        return None
    except Exception as e:
        logger.warning(f"Error extracting post ID from URN '{urn}': {e}")
        return None

def save_post_incrementally(post_data: Dict, filename: str) -> bool:
    """Save a LinkedIn post to a JSON file incrementally, with duplicate checking."""
    person_name = post_data.get('person_name', 'Unknown')
    post_id = post_data.get('post_id')
    
    if not post_id:
        logger.warning(f"Post by '{person_name}' has no post_id, cannot check for duplicates")
        # Still save it but without duplicate protection
    elif not TESTING_MODE:  # Only check duplicates if not in testing mode
        # Load existing scraped IDs
        scraped_ids = load_scraped_ids()
        
        # Check if the post ID has already been scraped
        if post_id in scraped_ids:
            logger.info(f"Post by '{person_name}' with ID '{post_id}' has already been scraped. Skipping.")
            return False  # Skip saving if already scraped
    else:
        logger.debug(f"TESTING_MODE enabled - skipping duplicate check for post ID '{post_id}'")
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Check if file exists and has content
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            # Read existing posts
            with open(filename, 'r', encoding='utf-8') as f:
                try:
                    posts = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error in {filename}: {e}. Starting fresh for post by '{person_name}'")
                    posts = []
        else:
            # Create new file with empty array
            posts = []
        
        # Append new post
        posts.append(post_data)
        
        # Write back to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        
        # Save the new post ID to the scraped IDs file (only if we have an ID and not in testing mode)
        if post_id and not TESTING_MODE:
            save_scraped_id(post_id)
        elif post_id and TESTING_MODE:
            logger.debug(f"TESTING_MODE enabled - not saving post ID '{post_id}' to duplicate tracker")
        
        logger.info(f"Successfully saved post by '{person_name}' to {filename} (total: {len(posts)} posts)")
        return True
        
    except PermissionError as e:
        logger.error(f"Permission denied saving post by '{person_name}' to {filename}: {e}")
        return False
    except IOError as e:
        logger.error(f"IO error saving post by '{person_name}' to {filename}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving post by '{person_name}' to {filename}: {e}")
        return False

async def extract_post_link_from_feed_url(post_element) -> Optional[str]:
    """Extract post link from the feed update URL (Method 1 - Most reliable)."""
    try:
        # Look for the direct feed link
        feed_link_element = await post_element.query_selector(LINKEDIN_POST_LINK_SELECTOR)
        if feed_link_element:
            href = await feed_link_element.get_attribute('href')
            if href and '/feed/update/urn:li:activity:' in href:
                # This is the actual working LinkedIn post URL
                logger.debug(f"Extracted post link from feed URL: {href}")
                return href
        
        logger.debug("Could not find feed URL, trying URN method")
        return None
        
    except Exception as e:
        logger.warning(f"Error extracting post link from feed URL: {e}")
        return None

async def extract_post_link_from_urn(post_element) -> Optional[str]:
    """Extract post link from data-chameleon-result-urn attribute (Method 2 - Fallback)."""
    try:
        # Get the element with data-chameleon-result-urn attribute
        urn_element = await post_element.query_selector(LINKEDIN_POST_URN_SELECTOR)
        if urn_element:
            urn = await urn_element.get_attribute('data-chameleon-result-urn')
            if urn and 'urn:li:activity:' in urn:
                # Extract the activity ID from the URN
                activity_id = urn.split(':')[-1]
                # Construct the LinkedIn feed URL (this is the correct format)
                post_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}"
                logger.debug(f"Extracted post link from URN: {post_url}")
                return post_url
        
        logger.debug("Could not find URN attribute")
        return None
        
    except Exception as e:
        logger.warning(f"Error extracting post link from URN: {e}")
        return None

async def extract_post_link(page, post_element) -> str:
    """Extract post link using multiple methods with fallback."""
    # Method 1: Extract from feed URL (most reliable)
    post_link = await extract_post_link_from_feed_url(post_element)
    if post_link:
        return post_link
    
    # Method 2: Extract from URN (fallback)
    logger.debug("Trying fallback method: URN extraction")
    post_link = await extract_post_link_from_urn(post_element)
    if post_link:
        return post_link
    
    # If both methods fail
    logger.warning("Failed to extract post link using all methods")
    return 'Failed to extract'

async def extract_person_info(post_element) -> Dict:
    """Extract person information from a LinkedIn post element."""
    person_info = {
        'person_name': 'Failed to extract',
        'person_link': 'Failed to extract',
        'heading': 'Failed to extract'
    }
    
    try:
        # Extract person name - try multiple selectors
        name_selectors = [
            LINKEDIN_PERSON_NAME_SELECTOR,
            '.meivKfdaNNAuIPkXHsImjugZzmtQ.t-16 a',
            '.entity-result__content-actor .meivKfdaNNAuIPkXHsImjugZzmtQ span'
        ]
        
        for selector in name_selectors:
            try:
                name_element = await post_element.query_selector(selector)
                if name_element:
                    name_text = await name_element.text_content()
                    if name_text and name_text.strip() and len(name_text.strip()) > 1:
                        person_info['person_name'] = name_text.strip()
                        break
            except:
                continue
        
        # Extract person profile link
        link_element = await post_element.query_selector(LINKEDIN_PERSON_LINK_SELECTOR)
        if link_element:
            href = await link_element.get_attribute('href')
            if href:
                # Clean up the LinkedIn URL
                if '?' in href:
                    href = href.split('?')[0]
                person_info['person_link'] = href
        
        # Extract person heading/title
        heading_element = await post_element.query_selector(LINKEDIN_HEADING_SELECTOR)
        if heading_element:
            heading_text = await heading_element.text_content()
            if heading_text and heading_text.strip():
                person_info['heading'] = heading_text.strip()
    
    except Exception as e:
        logger.warning(f"Error extracting person info: {e}")
    
    return person_info

async def extract_post_time(post_element) -> str:
    """Extract post time from a LinkedIn post element."""
    try:
        # Try multiple selectors for time
        time_selectors = [
            LINKEDIN_POST_TIME_SELECTOR,
            'p.t-black--light.t-12 span[aria-hidden="true"]',
            '.t-black--light.t-12 span[aria-hidden="true"]',
            'p.t-black--light span[aria-hidden="true"]'
        ]
        
        for selector in time_selectors:
            try:
                time_element = await post_element.query_selector(selector)
                if time_element:
                    time_text = await time_element.text_content()
                    if time_text and time_text.strip():
                        # Clean up the time text (remove extra characters and get only time part)
                        cleaned_time = time_text.strip()
                        # Look for time patterns like "2h", "3d", "1w", etc.
                        if '•' in cleaned_time:
                            time_parts = cleaned_time.split('•')
                            for part in time_parts:
                                part = part.strip()
                                # Check if this part looks like a time (contains numbers and time units)
                                if any(char.isdigit() for char in part) and any(unit in part.lower() for unit in ['h', 'd', 'w', 'm', 'min', 'hour', 'day', 'week']):
                                    return part
                        # If no bullet separator, check if the whole text looks like time
                        elif any(char.isdigit() for char in cleaned_time) and any(unit in cleaned_time.lower() for unit in ['h', 'd', 'w', 'm', 'min', 'hour', 'day', 'week']):
                            return cleaned_time
            except:
                continue
                
    except Exception as e:
        logger.warning(f"Error extracting post time: {e}")
    
    return 'Failed to extract'

async def extract_post_content(post_element) -> str:
    """Extract post content from a LinkedIn post element."""
    try:
        # First try to find the "see more" button and click it to expand the content
        see_more_button = await post_element.query_selector(LINKEDIN_SEE_MORE_BUTTON_SELECTOR)
        if see_more_button:
            try:
                await see_more_button.click()
                await human_sleep(SLEEP_SHORT)
                logger.debug("Clicked 'see more' to expand post content")
            except Exception as e:
                logger.debug(f"Could not click 'see more' button: {e}")
        
        # Try multiple selectors for content
        content_selectors = [
            LINKEDIN_POST_CONTENT_SELECTOR,
            'p.relative.entity-result__content-summary--3-lines',
            '.entity-result__content-summary',
            'p.entity-result__content-summary',
            '.rcpNGBRTqHenDVxuthshRGglvWCTyFNRvSvUU p'
        ]
        
        for selector in content_selectors:
            try:
                content_element = await post_element.query_selector(selector)
                if content_element:
                    content_text = await content_element.text_content()
                    if content_text and content_text.strip() and len(content_text.strip()) > 10:
                        # Clean up the content (remove extra whitespace and normalize)
                        cleaned_content = ' '.join(content_text.strip().split())
                        # Remove the "see more" text if present
                        if '…see more' in cleaned_content:
                            cleaned_content = cleaned_content.replace('…see more', '').strip()
                        return cleaned_content
            except:
                continue
    
    except Exception as e:
        logger.warning(f"Error extracting post content: {e}")
    
    return 'Failed to extract'

async def extract_complete_post_info(page, post_element) -> Optional[Dict]:
    """Extract complete information from a LinkedIn post element."""
    try:
        # Extract person information
        person_info = await extract_person_info(post_element)
        
        # Extract post time
        post_time = await extract_post_time(post_element)
        
        # Extract post content
        post_content = await extract_post_content(post_element)
        
        # Extract post link
        post_link = await extract_post_link(page, post_element)
        
        # Extract post ID from multiple sources
        post_id = None
        
        if post_link and post_link != 'Failed to extract':
            post_id = extract_post_id_from_link(post_link)
        
        if not post_id:
            try:
                urn_element = await post_element.query_selector(LINKEDIN_POST_URN_SELECTOR)
                if urn_element:
                    urn = await urn_element.get_attribute('data-chameleon-result-urn')
                    if urn:
                        post_id = extract_post_id_from_urn(urn)
            except:
                pass
        
        # Get scraped date first
        scraped_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create complete post data with estimated posted date
        post_data = {
            **person_info,
            'posted_time': post_time,
            'post_content': post_content,
            'post_link': post_link,
            'post_id': post_id,
            'scraped_date': scraped_date,
            'estimated_posted_date': estimate_posted_date(post_time, scraped_date)  # ADD THIS LINE
        }
        
        # Log extraction results
        person_name = person_info.get('person_name', 'Unknown')
        failed_fields = [key for key, value in post_data.items() 
                        if value == 'Failed to extract' and key != 'scraped_date']
        
        if failed_fields:
            logger.warning(f"Post by '{person_name}': Failed to extract {failed_fields}")
        
        if not post_id:
            logger.warning(f"Post by '{person_name}': Failed to extract post_id")
        else:
            logger.debug(f"Successfully extracted all fields for post by '{person_name}' (ID: {post_id})")
        
        return post_data
        
    except Exception as e:
        logger.error(f"Error extracting complete post info: {e}")
        return None
