# Google Jobs & LinkedIn Scraper

A comprehensive Python-based web scraping tool that automatically collects job postings from Google Jobs and LinkedIn posts, uploads results to Google Drive, and sends notifications via webhooks.

## 📋 Table of Contents

- Overview
- Features
- Technology Stack
- Architecture
- Project Structure
- Installation
- Configuration
- Usage
- How It Works
- API & Integrations
- Troubleshooting

## 🎯 Overview

This project automates the process of scraping job listings from Google Jobs and LinkedIn posts, specifically targeting internship and job opportunities. It uses Playwright for browser automation, implements intelligent duplicate detection, stores results in JSON format, uploads them to Google Drive, and triggers webhooks for downstream processing.

## ✨ Features

### Core Functionality

- **Dual Scraper Support**: Scrapes both Google Jobs and LinkedIn saved posts
- **Intelligent Duplicate Detection**: Uses hash-based system to avoid re-scraping existing content
- **Incremental Saving**: Saves data as it's scraped to prevent data loss
- **Cookie Management**: Persists login sessions across runs
- **Human-like Behavior**: Random delays and natural scrolling patterns to avoid detection
- **Graceful Shutdown**: Handles interruption signals properly, saving progress

### LinkedIn Scraper Features

- Extracts post content, author information, company details, and timestamps
- Expands "see more" buttons to get full post content
- Estimates posting dates from relative timestamps (e.g., "2d ago" → actual date)
- Stops after encountering consecutive existing posts (configurable threshold)
- Multiple fallback methods for extracting post links

### Google Jobs Scraper Features

- Extracts job title, company, location, description, and posting date
- Filters jobs by keywords (configurable in config.py)
- Handles "Show more jobs" pagination
- Estimates posting dates from relative timestamps

### Data Management

- **Google Drive Integration**: Automatically uploads results to specified folder
- **Webhook Notifications**: Triggers n8n workflows with scraping statistics
- **SQLite Database**: Stores job hashes for efficient duplicate checking (30-day expiry)
- **JSON Export**: Structured data in timestamp-based files

### Testing Features

- Testing mode for limited scraping runs
- Read-only mode for hash checking without storage
- Webhook tester utility included

## 🛠 Technology Stack

### Core Technologies

- **Python 3.8+**
- **Playwright**: Browser automation framework
- **playwright-stealth**: Anti-detection plugin

### Key Libraries

- `asyncio`: Asynchronous operations
- `sqlite3`: Duplicate detection database
- `google-auth`, `google-api-python-client`: Google Drive integration
- `requests`: HTTP requests for webhooks
- `python-dotenv`: Environment variable management
- `hashlib`: Content hashing for duplicate detection

### External Services

- **Google Drive API**: File storage
- **n8n Webhooks**: Workflow automation
- **LinkedIn**: Content source (requires login)
- **Google Jobs**: Job listings source

## 🏗 Architecture

### Component Interaction Flow

```
┌─────────────┐
│   main.py   │ (Entry Point)
└──────┬──────┘
       │
       ├─────────────────┬──────────────────┐
       │                 │                  │
       ▼                 ▼                  ▼
┌────────────┐   ┌─────────────┐   ┌──────────────┐
│  Google    │   │  LinkedIn   │   │   Config     │
│  Scraper   │   │  Scraper    │   │  (config.py) │
└─────┬──────┘   └──────┬──────┘   └──────────────┘
      │                 │
      │                 │
      ▼                 ▼
┌─────────────────────────────┐
│     Utility Modules         │
├─────────────────────────────┤
│ • JobHashStore              │ ◄── SQLite DB
│ • GoogleDriveUploader       │ ◄── Google Drive API
│ • WebhookNotifier           │ ◄── n8n Webhooks
└─────────────────────────────┘
      │
      ▼
┌─────────────────────────────┐
│     Data Storage            │
├─────────────────────────────┤
│ • JSON files (results)      │
│ • Cookie files              │
│ • scraped_post_ids.json     │
│ • job_hashes.db             │
└─────────────────────────────┘
```

### Module Breakdown

#### 1. **main.py** - Entry Point & Browser Management

- Displays interactive menu for scraper selection
- Initializes Playwright browser with stealth mode
- Manages cookie persistence for authenticated sessions
- Orchestrates scraper execution

#### 2. **scraper.py** - Google Jobs Scraper

- **Key Functions**:
  - `perform_scraping()`: Main scraping loop
  - `extract_basic_job_info()`: Extracts job data from elements
  - `estimate_posted_date()`: Converts relative dates to absolute dates
  - `save_job_incrementally()`: Saves jobs one at a time
- **Flow**:
  1. Searches for jobs using configured keywords
  2. Extracts job details from search results
  3. Checks against hash database for duplicates
  4. Saves new jobs incrementally
  5. Handles pagination ("Show more jobs")
  6. Uploads results to Google Drive

#### 3. **scraper.py** - LinkedIn Posts Scraper

- **Key Functions**:
  - `perform_linkedin_scraping()`: Main scraping loop
  - `extract_post_content()`: Expands and extracts full post text
  - `extract_post_link()`: Multiple methods to get post URLs
  - `estimate_posted_date()`: Converts relative timestamps
- **Flow**:
  1. Loads saved posts page
  2. Extracts post IDs to check for duplicates
  3. Scrolls through feed, extracting post details
  4. Stops after N consecutive existing posts
  5. Saves incrementally to JSON
  6. Uploads to Google Drive

#### 4. **job_hash_store.py** - Duplicate Detection

- **Purpose**: Prevents re-scraping the same jobs
- **Mechanism**:
  - Generates MD5 hash from title + company + location + description snippet
  - Stores hashes in SQLite database with timestamps
  - Auto-expires entries after 30 days
- **Modes**:
  - Normal: Stores new hashes
  - Read-only: Only checks, doesn't store (for testing)

#### 5. **google_drive_uploader.py** - File Upload

- **Authentication**: OAuth2 with token caching
- **Features**:
  - Retry mechanism (up to 5 attempts)
  - Uploads JSON results to configured Drive folder
  - Returns shareable links
  - Triggers webhook after successful upload

#### 6. **webhook_notifier.py** - n8n Integration

- **Purpose**: Triggers downstream workflows
- **Payload Structure**:
  ```json
  {
    "event": "scraper_completed",
    "scraper_type": "google_jobs|linkedin_posts",
    "timestamp": "2024-01-15 14:30:00",
    "file": {
      "name": "google_jobs_20240115_143000.json",
      "drive_file_id": "...",
      "view_link": "https://drive.google.com/..."
    },
    "scraping_stats": {
      "jobs_scraped": 15,
      "duplicates_skipped": 5,
      "failed_extractions": 1
    }
  }
  ```

#### 7. **config.py** - Configuration Management

- **Settings Categories**:
  - Testing configuration (limits, testing mode)
  - Search keywords for Google Jobs
  - LinkedIn scraping parameters (stop threshold, scroll attempts)
  - CSS selectors for both platforms
  - Webhook URLs (prod/test)
  - Google Drive credentials
  - Human-like timing configurations

## 📁 Project Structure

```
google-jobs-scraper/
├── main.py                    # Entry point
├── config.py                  # Configuration
├── requirements.txt           # Python dependencies
├── .gitignore
├── google_scraper/
│   └── scraper.py            # Google Jobs scraping logic
├── linkedin_scraper/
│   └── scraper.py            # LinkedIn posts scraping logic
├── utility/
│   ├── job_hash_store.py     # Duplicate detection
│   ├── google_drive_uploader.py  # Drive integration
│   └── webhook_notifier.py   # Webhook notifications
├── test/
│   └── webhook_tester.py     # Test webhook functionality
└── data/                      # Data storage (gitignored)
    ├── google_cookies.json
    ├── linkedin_cookies.json
    ├── scraped_post_ids.json
    ├── job_hashes.db
    ├── google_drive_token.pickle
    ├── client_secret_*.json
    ├── scraper.log
    ├── google_jobs/          # Google Jobs results
    └── linkedin_jobs/        # LinkedIn posts results
```

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- Google Cloud Project with Drive API enabled
- n8n instance (for webhooks)

### Steps

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd google-jobs-scraper
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**

   ```bash
   playwright install chromium
   ```

4. **Set up Google Drive API**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Google Drive API
   - Create OAuth 2.0 credentials
   - Download credentials and save as `data/client_secret_*.json`

5. **Create `.env` file** (optional)
   ```bash
   N8N_AUTH_TOKEN=your_auth_token
   GOOGLE_DRIVE_FOLDER_ID=your_folder_id
   ```

## ⚙️ Configuration

### Essential Settings in config.py

```python
# Testing Configuration
TESTING_MODE = True              # Set False for production
MAX_JOBS_TO_SCRAPE = 3          # Limit for testing (0 = unlimited)

# Job Search Keywords
JOB_SEARCH_KEYWORDS = [
    "software engineer intern",
    "stage en informatique",
    # Add more keywords...
]

# LinkedIn Configuration
STOP_AFTER_EXISTING_POSTS = 5   # Stop after N consecutive existing posts

# Webhooks
GOOGLE_JOBS_WEBHOOK_URL = 'https://your-n8n-instance/webhook/...'
LINKEDIN_WEBHOOK_URL = 'https://your-n8n-instance/webhook/...'

# Google Drive
GOOGLE_DRIVE_FOLDER_ID = 'your_folder_id'
```

### CSS Selectors

Both scrapers use CSS selectors defined in config.py. If LinkedIn or Google changes their UI, update these selectors:

```python
# LinkedIn Selectors
LINKEDIN_POST_CONTAINER_SELECTOR = 'li.csImSlkPixlwooCPrzjuMicprhYXhJsJAF'
LINKEDIN_PERSON_NAME_SELECTOR = '.ZtBUfPYEDJpgsPBTEsevFDcMIPKruvsuYY.t-16 a'
# ... more selectors

# Google Jobs Selectors
JOB_CONTAINER_SELECTOR = '.EimVGf'
JOB_TITLE_SELECTOR = '.tNxQIb.PUpOsf'
# ... more selectors
```

## 🚀 Usage

### Interactive Mode

1. **Run the main script**

   ```bash
   python main.py
   ```

2. **Select scraper type**

   ```
   ==============================================
          Job Scraper - Choose Your Source
   ==============================================
   1. Google Jobs Scraper
   2. LinkedIn Posts Scraper
   3. Exit
   ==============================================
   Enter your choice (1-3):
   ```

3. **First-time login** (if needed)
   - For Google Jobs: Browser will open, log in to Google
   - For LinkedIn: Browser will open, log in to LinkedIn
   - Cookies are saved for future runs

### Programmatic Usage

```python
from google_scraper.scraper import perform_scraping
from linkedin_scraper.scraper import perform_linkedin_scraping
from playwright.async_api import async_playwright

async def run_google_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        jobs_count = await perform_scraping(page)
        print(f"Scraped {jobs_count} jobs")

        await browser.close()

# Run with asyncio
import asyncio
asyncio.run(run_google_scraper())
```

## 🔄 How It Works

### Google Jobs Scraping Flow

1. **Initialization**

   - Loads cookies from google_cookies.json
   - Initializes `JobHashStore` for duplicate checking

2. **Search Loop**

   - Iterates through keywords in `JOB_SEARCH_KEYWORDS`
   - Navigates to Google Jobs with each keyword
   - Waits for job listings to load

3. **Job Extraction**

   - Finds all job cards using `JOB_CONTAINER_SELECTOR`
   - For each job:
     - Extracts title, company, location
     - Clicks job to open details panel
     - Extracts full description
     - Estimates posting date using `estimate_posted_date()`

4. **Duplicate Detection**

   - Generates hash: `MD5(title|company|location|description[:100])`
   - Checks against `job_hashes.db`
   - Skips if duplicate, saves if new

5. **Data Saving**

   - Saves incrementally to JSON using `save_job_incrementally()`
   - Format: `data/google_jobs/google_jobs_YYYYMMDD_HHMMSS.json`

6. **Upload & Notify**
   - Uploads JSON to Google Drive via `GoogleDriveUploader`
   - Triggers webhook via `WebhookNotifier`

### LinkedIn Posts Scraping Flow

1. **Initialization**

   - Loads cookies from linkedin_cookies.json
   - Loads scraped post IDs from `data/scraped_post_ids.json`

2. **Navigate to Saved Posts**

   - Opens LinkedIn saved posts page
   - Waits for posts to load

3. **Post Extraction Loop**

   - Scrolls through feed (configurable scroll attempts)
   - For each post:
     - Extracts post ID using `extract_post_id_from_link()`
     - Checks if already scraped
     - If new:
       - Extracts person/company name and link
       - Extracts post content (expands "see more")
       - Extracts timestamp and converts to date
       - Extracts post link (multiple fallback methods)

4. **Early Stopping**

   - Tracks consecutive existing posts
   - Stops if threshold reached (`STOP_AFTER_EXISTING_POSTS`)

5. **Data Saving**

   - Saves incrementally using `save_post_incrementally()`
   - Adds post ID to `data/scraped_post_ids.json`
   - Format: `data/linkedin_jobs/linkedin_jobs_YYYYMMDD_HHMMSS.json`

6. **Upload & Notify**
   - Same as Google Jobs scraper

## 🔌 API & Integrations

### Google Drive API

- **Authentication**: OAuth 2.0 with offline refresh token
- **Scopes**: `https://www.googleapis.com/auth/drive.file`
- **Token Storage**: `data/google_drive_token.pickle`

### Webhook Integration

- **Method**: POST request
- **Authentication**: Bearer token in header
- **Retry**: Up to 5 attempts with exponential backoff
- **URLs configured in** config.py

## 🔧 Troubleshooting

### Common Issues

1. **"Failed to authenticate with Google Drive"**

   - Ensure `client_secret_*.json` is in data folder
   - Delete `google_drive_token.pickle` and re-authenticate

2. **"Could not find element" errors**

   - Website UI may have changed
   - Update CSS selectors in config.py
   - Check .html file for current structure

3. **LinkedIn login required every time**

   - Check if linkedin_cookies.json exists
   - LinkedIn may have expired the session
   - Try disabling 2FA temporarily for automation

4. **No jobs found**

   - Verify `JOB_SEARCH_KEYWORDS` are correct
   - Check if Google Jobs is available in your region
   - Increase `SLEEP_LONG` timeouts in config.py

5. **Webhook not triggering**
   - Test webhook manually using webhook_tester.py
   - Verify `N8N_AUTH_TOKEN` is correct
   - Check n8n workflow is activated

### Logs

- All operations logged to `data/scraper.log`
- Check for errors and warnings

### Testing

```bash
# Test webhook only
python test/webhook_tester.py

# Enable testing mode in config.py
TESTING_MODE = True
MAX_JOBS_TO_SCRAPE = 3
```

## 📝 Notes

- **Rate Limiting**: Human-like delays configured in `SLEEP_*` constants
- **Anti-Detection**: Uses `playwright-stealth` to avoid bot detection
- **Data Retention**: Job hashes expire after 30 days in `JobHashStore`
- **LinkedIn Limitation**: Only scrapes already-saved posts (requires manual saving first)

## 📄 License

This project is for educational purposes. Ensure compliance with Google's and LinkedIn's Terms of Service when scraping.

---

**Happy Scraping! 🚀**
