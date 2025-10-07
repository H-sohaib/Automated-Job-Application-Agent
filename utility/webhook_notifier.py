import requests
import logging
from typing import Dict, Any, Optional
from config import N8N_WEBHOOK_URL, N8N_AUTH_TOKEN

logger = logging.getLogger(__name__)

class WebhookNotifier:
    """Utility class for sending notifications to n8n webhooks"""
    
    def __init__(self):
        self.webhook_url = N8N_WEBHOOK_URL
        self.auth_token = N8N_AUTH_TOKEN
    
    def trigger_n8n_workflow(self, file_info: Dict[str, Any], scrape_stats: Dict[str, Any]) -> bool:
        """
        Trigger n8n workflow with file upload information
        
        Args:
            file_info: Information about the uploaded file
            scrape_stats: Statistics about the scraping session
            
        Returns:
            bool: True if webhook was triggered successfully, False otherwise
        """
        try:
            payload = {
                "event": "google_drive_upload_completed",
                "timestamp": file_info.get('completed_at'),
                "file": {
                    "name": file_info.get('filename'),
                    "drive_file_id": file_info.get('drive_file_id'),
                    "size_bytes": file_info.get('size_bytes'),
                    "view_link": file_info.get('view_link')
                },
                "scraping_stats": {
                    "jobs_scraped": scrape_stats.get('jobs_scraped', 0),
                    "duplicates_skipped": scrape_stats.get('duplicates_skipped', 0),
                    "failed_extractions": scrape_stats.get('failed_extractions', 0)
                }
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.auth_token}' if self.auth_token else None
            }
            
            # Remove None authorization header if no token provided
            if not self.auth_token:
                headers.pop('Authorization', None)
            
            logger.info(f"Triggering n8n webhook: {self.webhook_url}")
            logger.info(f"Payload: {payload}")
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("n8n webhook triggered successfully")
                logger.info(f"Response: {response.text}")
                return True
            else:
                logger.error(f"n8n webhook failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error triggering n8n webhook: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error triggering n8n webhook: {e}")
            return False