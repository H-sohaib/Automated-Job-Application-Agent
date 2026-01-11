import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Testing Configuration
TESTING_MODE = False     # Set to True to enable testing mode (disables hash storage)
MAX_JOBS_TO_SCRAPE = 3 if TESTING_MODE else 0  # 0 means unlimited
MAX_POSTS_TO_SCRAPE = MAX_JOBS_TO_SCRAPE  # 0 means unlimited

JOB_SEARCH_KEYWORDS = [
    # IT / Informatique générale
    "stage PFE",
    "internship PFE",
    "internship Pre hired",
    "stage pré embauche",
    "stage PFE en informatique",
    "stage pré embauche en informatique",
    # "internship PFE in IT",
    # "internship Pre hired in IT",
    # "stage IT",
    # "IT internship",

    # Réseau
    "stage réseau",
    "network intern",
    "stage ingénieur réseau",
    "network engineering internship",

    # Cybersecurity / sécurité
    "stage cybersécurité",
    "cybersecurity intern",
    "stage sécurité informatique",
    "information security internship",
    "ethical hacking internship",
    "stage pentesting",
    "stage soc",
    "SOC intern",

    # Développement web
    "stage developpeur web",
    "web developer intern",
    # "stage web",
    "internship web development",
    "back-end developer intern",
    "stage back-end",
    "full stack developer intern",
    "stage full stack",
    "full stack web development internship",

    # Développement logiciel
    "software engineer intern",
    "stage ingénieur logiciel",
    "python developer intern",
    "stage python",
    "java developer intern",
    "Spring developer intern",
    "stage java spring",
    "stage java",
]

# LinkedIn Configuration
STOP_AFTER_EXISTING_POSTS = 5  # Stop after finding this many consecutive existing posts
# General Scraper Configuration
MAX_SCROLL_ATTEMPTS = 3
SCROLL_DELAY = 2  # seconds
BATCH_SIZE = 5  # Initial batch size (will be adjusted dynamically)

# LinkedIn-specific CSS selectors - UPDATED based on actual HTML structure
LINKEDIN_POST_CONTAINER_SELECTOR = 'li.WdkfqDOUJZCWthfjyTNzddOIbUbRvfCG'  # Each post item
LINKEDIN_PERSON_NAME_SELECTOR = 'span.ClwkWtshSslMPZIFyoYLNeAGiibyUUUwGNzhCxZI a span[aria-hidden="true"]'  # Person/Company name
LINKEDIN_PERSON_LINK_SELECTOR = 'span.ClwkWtshSslMPZIFyoYLNeAGiibyUUUwGNzhCxZI a.qZeTGqFRxixYywXeiJBKyqEkwEmzWYtTPNuLg'  # Profile/Company link
LINKEDIN_HEADING_SELECTOR = 'div.OulMkMIIgxfHHNTPcFnQMiohVdfmCyVAYsGqKE'  # Job title or follower count
LINKEDIN_POST_TIME_SELECTOR = 'div.entity-result__content-actor p.t-black--light.t-12 span[aria-hidden="true"]'  # Posted time (1d, 7h, 21h, etc.)
LINKEDIN_POST_CONTENT_SELECTOR = 'p.entity-result__content-summary'  # Post content paragraph
LINKEDIN_POST_LINK_SELECTOR = 'div.linked-area.flex-1.cursor-pointer'  # Clickable area to open post
LINKEDIN_SEE_MORE_BUTTON_SELECTOR = 'button.reusable-search-show-more-link'  # See more button
LINKEDIN_POST_URN_SELECTOR = 'div.bnSSTYNVfGjvkaHMrUGLVhMzPgsNuQrTA[data-chameleon-result-urn]'  # URN container
LINKEDIN_THREE_DOT_MENU_SELECTOR = 'button.artdeco-dropdown__trigger'  # Three-dot overflow menu
LINKEDIN_POST_IMAGE_SELECTOR = 'img.ivm-view-attr__img--centered.entity-result__embedded-object-image'  # Post image (if exists)

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
N8N_AUTH_TOKEN = os.getenv('N8N_AUTH_TOKEN', '')  # Your n8n authentication token


# Webhook retry configuration
MAX_RETRIES = 5

# Google Drive Configuration (from environment variables)
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')  # Your Drive folder ID
GOOGLE_DRIVE_CREDENTIALS_PATH = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH', '')  # Downloaded from Google Cloud Console
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Human-like timing configurations
SLEEP_SHORT = (1.0, 2.5)      # Quick actions (clicks)
SLEEP_MEDIUM = (2.0, 4.0)     # Reading content, waiting for panels
SLEEP_LONG = (3.5, 6.0)       # Waiting for page loads, scrolling
SLEEP_SCROLL = (1.5, 3.0)     # Scrolling delay