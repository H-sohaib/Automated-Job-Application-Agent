import requests
import logging
from typing import Dict, Any
from config import (
    GOOGLE_JOBS_WEBHOOK_URL, 
    LINKEDIN_WEBHOOK_URL, 
    N8N_AUTH_TOKEN,
    MAX_RETRIES
)

logger = logging.getLogger(__name__)

class WebhookNotifier:
    """Utility class for sending notifications to n8n webhooks"""
    
    def __init__(self, scraper_type: str = "google_jobs"):
        """Initialize webhook notifier with scraper-specific configuration"""
        self.scraper_type = scraper_type
        self.auth_token = N8N_AUTH_TOKEN
        
        # Set webhook URL and configuration based on scraper type
        if scraper_type == "linkedin_posts":
            self.webhook_url = LINKEDIN_WEBHOOK_URL
            self.event_name = "linkedin_posts_upload_completed"
            self.data_key = "posts_scraped"
            self.scraper_name = "LinkedIn"
        else:
            self.webhook_url = GOOGLE_JOBS_WEBHOOK_URL
            self.event_name = "google_jobs_upload_completed"
            self.data_key = "jobs_scraped"
            self.scraper_name = "Google Jobs"
        
        # Log initialization
        mode = "TEST" if "webhook-test" in self.webhook_url else "PROD"
        logger.info(f"WebhookNotifier initialized - Scraper: {self.scraper_name}, Mode: {mode}, URL: {self.webhook_url}")
    
    def _build_payload(self, file_info: Dict[str, Any], scrape_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Build webhook payload"""
        return {
            "event": self.event_name,
            "scraper_type": self.scraper_type,
            "timestamp": file_info.get('completed_at'),
            "file": {
                "name": file_info.get('filename'),
                "drive_file_id": file_info.get('drive_file_id'),
                "size_bytes": file_info.get('size_bytes'),
                "view_link": file_info.get('view_link')
            },
            "scraping_stats": {
                self.data_key: scrape_stats.get('jobs_scraped', scrape_stats.get('posts_scraped', 0)),
                "duplicates_skipped": scrape_stats.get('duplicates_skipped', 0),
                "failed_extractions": scrape_stats.get('failed_extractions', 0)
            }
        }
    
    def trigger_n8n_workflow(self, file_info: Dict[str, Any], scrape_stats: Dict[str, Any]) -> bool:
        """
        Trigger n8n workflow with manual retry logic
        
        Returns:
            bool: True if successful, False otherwise
        """
        payload = self._build_payload(file_info, scrape_stats)
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.auth_token
        }
        
        for attempt in range(MAX_RETRIES + 1):
            # Wait for user input at each try
            print(f"\n>>> Press Enter to trigger webhook (Attempt {attempt + 1}/{MAX_RETRIES + 1})...")
            input()
            
            try:
                logger.info(f"Triggering {self.scraper_name} webhook (attempt {attempt + 1}/{MAX_RETRIES + 1})")
                
                if attempt > 0:
                    logger.debug(f"Retry payload: {payload}")
                
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info(f"{self.scraper_name} webhook triggered successfully on attempt {attempt + 1}")
                    return True
                
                logger.warning(f"{self.scraper_name} webhook failed with status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}/{MAX_RETRIES + 1}: {e}")
        
        logger.error(f"Failed to trigger {self.scraper_name} webhook after {MAX_RETRIES + 1} attempts")
        return False