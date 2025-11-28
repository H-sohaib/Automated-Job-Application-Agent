import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Testing Configuration
TESTING_MODE = True     # Set to True to enable testing mode (disables hash storage)
MAX_JOBS_TO_SCRAPE = 3 if TESTING_MODE else 0  # 0 means unlimited
MAX_POSTS_TO_SCRAPE = MAX_JOBS_TO_SCRAPE  # 0 means unlimited

JOB_SEARCH_KEYWORDS = [
    "software engineer intern",
    # "backend developer intern", 
    # "full stack developer intern",
    # "stage web developeur",
    "stage en informatique",
    # "python developer intern",
    # Add more keywords here
]

# LinkedIn Configuration
STOP_AFTER_EXISTING_POSTS = 5  # Stop after finding this many consecutive existing posts
# General Scraper Configuration
MAX_SCROLL_ATTEMPTS = 3
SCROLL_DELAY = 2  # seconds
BATCH_SIZE = 5  # Initial batch size (will be adjusted dynamically)

# LinkedIn-specific CSS selectors - CORRECTED based on HTML structure
LINKEDIN_POST_CONTAINER_SELECTOR = 'li.csImSlkPixlwooCPrzjuMicprhYXhJsJAF'  # Each post item
LINKEDIN_PERSON_NAME_SELECTOR = '.ZtBUfPYEDJpgsPBTEsevFDcMIPKruvsuYY.t-16 a'  # Person/Company name link
LINKEDIN_PERSON_LINK_SELECTOR = '.entity-result__content-image a'  # Profile/Company link (simplified)
LINKEDIN_HEADING_SELECTOR = '.eXEuNfjOurYHSiCLZwEVjqbaNvuRuBzwnNI.t-14.t-black.t-normal'  # Person's title/company or follower count
LINKEDIN_POST_TIME_SELECTOR = 'p.t-black--light.t-12 span[aria-hidden="true"]'  # Posted time (e.g., "2d •")
LINKEDIN_POST_CONTENT_SELECTOR = 'p.relative.entity-result__content-summary'  # Post text content (simplified to match both classes)
LINKEDIN_SEE_MORE_BUTTON_SELECTOR = 'button.reusable-search-show-more-link'  # "see more" button
LINKEDIN_POST_LINK_SELECTOR = '.TanvNKAVOapYdcCLlDucVvwxoFygLerZBSUM a[href*="/feed/update/"]'  # Direct post link
LINKEDIN_POST_URN_SELECTOR = 'div[data-chameleon-result-urn]'  # URN attribute container
LINKEDIN_THREE_DOT_MENU_SELECTOR = 'button.entity-result__overflow-actions-trigger'  # Three-dot menu button (simplified)
LINKEDIN_COPY_LINK_SELECTOR = 'div[data-control-name="copy_link"]'  # Not visible in saved posts view

# CSS Selectors
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


# n8n Configuration (from environment variables with testing mode support)
# Google Jobs Scraper URLs
GOOGLE_JOBS_WEBHOOK_URL_PROD = 'https://n8n.sohaib-engineer.tech/webhook/n8n-webhook'
GOOGLE_JOBS_WEBHOOK_URL_TEST = 'https://n8n.sohaib-engineer.tech/webhook-test/n8n-webhook'

# LinkedIn Scraper URLs  
LINKEDIN_WEBHOOK_URL_PROD = GOOGLE_JOBS_WEBHOOK_URL_PROD
LINKEDIN_WEBHOOK_URL_TEST = GOOGLE_JOBS_WEBHOOK_URL_TEST

# Use test or prod URLs based on TESTING_MODE
GOOGLE_JOBS_WEBHOOK_URL =  GOOGLE_JOBS_WEBHOOK_URL_PROD
LINKEDIN_WEBHOOK_URL = LINKEDIN_WEBHOOK_URL_PROD

# Keep the old N8N_WEBHOOK_URL for backward compatibility (defaults to Google Jobs)
N8N_WEBHOOK_URL = GOOGLE_JOBS_WEBHOOK_URL
N8N_AUTH_TOKEN = os.getenv('N8N_AUTH_TOKEN', 'Goblin123/@')


# Webhook retry configuration
MAX_RETRIES = 5

# Google Drive Configuration (from environment variables)
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '1zE5YJNxzvjSIB_BdbLH556g6Tqeuj6Eq')  # Your Drive folder ID
GOOGLE_DRIVE_CREDENTIALS_PATH = 'data/client_secret_729303119270-0mifattvl0sdr1ks4pmp0oqj6erb13ob.apps.googleusercontent.com.json'  # Downloaded from Google Cloud Console
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Human-like timing configurations
SLEEP_SHORT = (1.0, 2.5)      # Quick actions (clicks)
SLEEP_MEDIUM = (2.0, 4.0)     # Reading content, waiting for panels
SLEEP_LONG = (3.5, 6.0)       # Waiting for page loads, scrolling
SLEEP_SCROLL = (1.5, 3.0)     # Scrolling delay



# Client_secret= "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"
# CLIENT_ID = "729303119270-0mifattvl0sdr1ks4pmp0oqj6erb13ob.apps.googleusercontent.com"