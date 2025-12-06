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
    "stage PFE en informatique",
    "stage pré embauche en informatique",
    "internship PFE in IT",
    "internship Pre hired in IT",
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

    # Développement web
    "stage développeur web",
    "web developer intern",
    "stage web",
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
    "stage java",
]

# LinkedIn Configuration
STOP_AFTER_EXISTING_POSTS = 5  # Stop after finding this many consecutive existing posts
# General Scraper Configuration
MAX_SCROLL_ATTEMPTS = 3
SCROLL_DELAY = 2  # seconds
BATCH_SIZE = 5  # Initial batch size (will be adjusted dynamically)

# LinkedIn-specific CSS selectors - UPDATED based on HTML structure
LINKEDIN_POST_CONTAINER_SELECTOR = 'li.wMRiBRCvyAuKYKJAJQBPBewvOUTZLAyc'  # Each post item
LINKEDIN_PERSON_NAME_SELECTOR = '.entity-result__content-actor .AHnruhvJOLcieYAdDEXLwXpwxPshmxsPkCs.t-16 a span[aria-hidden="true"]'  # Person/Company name
LINKEDIN_PERSON_LINK_SELECTOR = '.entity-result__content-actor .AHnruhvJOLcieYAdDEXLwXpwxPshmxsPkCs.t-16 a.QJGrFqtGqHGdfvGNjGKbMnXKKgXQAqEbI'  # Profile/Company link
LINKEDIN_HEADING_SELECTOR = '.entity-result__content-actor .FPdNKwviUxbzXoewHkEjWfHOezasHFIMKbJox.t-14.t-black.t-normal'  # Job title or follower count
LINKEDIN_POST_TIME_SELECTOR = '.entity-result__content-actor p.t-black--light.t-12 span[aria-hidden="true"]'  # Posted time
LINKEDIN_POST_CONTENT_SELECTOR = '.entity-result__content-inner-container--right-padding p.entity-result__content-summary'  # Post content
LINKEDIN_SEE_MORE_BUTTON_SELECTOR = '.entity-result__content-inner-container--right-padding button.reusable-search-show-more-link'  # See more button
LINKEDIN_POST_LINK_SELECTOR = '.entity-result__content-inner-container--right-padding a.QJGrFqtGqHGdfvGNjGKbMnXKKgXQAqEbI[href*="/feed/update/"]'  # Post link
LINKEDIN_POST_URN_SELECTOR = 'div.jzdaHAHkcwgvghZOledAWhWddzlUnvHIQ[data-chameleon-result-urn]'  # URN container
LINKEDIN_THREE_DOT_MENU_SELECTOR = '.entity-result__actions-overflow-menu-dropdown button.artdeco-dropdown__trigger'  # Three-dot menu
LINKEDIN_COPY_LINK_SELECTOR = 'div[data-control-name="copy_link"]'  # Copy link option (in dropdown)
LINKEDIN_POST_IMAGE_SELECTOR = '.entity-result__content-inner-container--right-padding .ivm-image-view-model img'  # Post image (if any)

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