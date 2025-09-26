import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# Configuration
MAX_JOBS_TO_SCRAPE = 4
MAX_SCROLL_ATTEMPTS = 10
SCROLL_DELAY = 2  # seconds
BATCH_SIZE = 5  # Initial batch size (will be adjusted dynamically)

# n8n Configuration (from environment variables)
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL', 'https://n8n.sohaib-engineer.tech/webhook-test/jobs-webhook')
N8N_AUTH_TOKEN = os.getenv('N8N_AUTH_TOKEN', 'Goblin123/@')

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