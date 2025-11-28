import os
import pickle
from datetime import datetime
import logging
from typing import Optional, Dict, Any
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from config import SCOPES, GOOGLE_DRIVE_FOLDER_ID, GOOGLE_DRIVE_CREDENTIALS_PATH
from utility.webhook_notifier import WebhookNotifier

logger = logging.getLogger(__name__)

class GoogleDriveUploader:
    """Simple Google Drive uploader for scraper results with retry mechanism"""
    
    def __init__(self, scraper_type: str = "google_jobs"):
        self.service: Optional[Resource] = None
        self.folder_id = GOOGLE_DRIVE_FOLDER_ID
        self.token_path = 'data/google_drive_token.pickle'
        self.scraper_type = scraper_type
        self.webhook_notifier = WebhookNotifier(scraper_type=scraper_type)
        
        if not self._authenticate():
            raise Exception("Failed to authenticate with Google Drive")
    
    def _authenticate(self) -> bool:
        """Authenticate with Google Drive API"""
        try:
            creds = None
            os.makedirs('data', exist_ok=True)
            
            # Load existing token
            if os.path.exists(self.token_path):
                try:
                    with open(self.token_path, 'rb') as token:
                        creds = pickle.load(token)
                    logger.info("Loaded existing credentials")
                except Exception as e:
                    logger.warning(f"Could not load token, will re-authenticate: {e}")
                    try:
                        os.remove(self.token_path)
                    except:
                        pass
                    creds = None
            
            # Refresh or get new credentials
            if creds and not creds.valid:
                if creds.expired and creds.refresh_token:
                    try:
                        logger.info("Refreshing expired credentials...")
                        creds.refresh(Request())
                        logger.info("Credentials refreshed successfully")
                    except Exception as e:
                        logger.error(f"Failed to refresh credentials: {e}")
                        try:
                            os.remove(self.token_path)
                        except:
                            pass
                        creds = None
                else:
                    creds = None
            
            # Get new credentials if needed
            if not creds:
                if not os.path.exists(GOOGLE_DRIVE_CREDENTIALS_PATH):
                    logger.error(f"Credentials file not found: {GOOGLE_DRIVE_CREDENTIALS_PATH}")
                    return False
                
                logger.info("Starting OAuth flow for new credentials...")
                flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_DRIVE_CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
                logger.info("New credentials obtained successfully")
            
            # Save credentials
            try:
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info("Credentials saved successfully")
            except Exception as e:
                logger.warning(f"Could not save credentials: {e}")
            
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Google Drive authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _is_client_error(self, error: Exception) -> bool:
        """Check if error is a client error (4xx) that should not be retried"""
        if isinstance(error, HttpError):
            return 400 <= error.resp.status < 500
        return False
    
    def _upload_with_retry(self, upload_func, description: str, max_retries: int = 10) -> Optional[Dict]:
        """
        Execute upload function with retry logic for all errors except client errors
        
        Args:
            upload_func: Function to execute
            description: Description for logging
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dict or None: Upload result or None if failed
        """
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Upload attempt {attempt + 1}/{max_retries + 1}: {description}")
                result = upload_func()
                
                if result:
                    if attempt > 0:
                        logger.info(f"Upload successful on attempt {attempt + 1}: {description}")
                    return result
                else:
                    logger.warning(f"Upload returned None: {description}")
                    
            except Exception as e:
                is_client_error = self._is_client_error(e)
                
                if is_client_error:
                    logger.error(f"Client error, stopping retries: {e}")
                    return None
                
                if attempt == max_retries:
                    logger.error(f"Upload failed after {max_retries + 1} attempts: {description}")
                    logger.error(f"Final error: {e}")
                    return None
                
                logger.warning(f"Error on attempt {attempt + 1}: {e}")
                logger.info(f"Retries remaining: {max_retries - attempt}")
                
                # Wait for user input before retrying
                print(f"\n>>> Upload failed. Press Enter to retry (Attempt {attempt + 2}/{max_retries + 1})...")
                try:
                    input()
                except KeyboardInterrupt:
                    logger.info("Upload retry interrupted by user")
                    return None
        
        return None
    
    def _upload_file(self, file_path: str, drive_filename: str) -> Optional[Dict]:
        """Upload a file to Google Drive"""
        def _do_upload():
            if not self.service:
                logger.error("Google Drive service not initialized")
                return None
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            file_metadata: Dict[str, Any] = {'name': drive_filename}
            if self.folder_id:
                file_metadata['parents'] = [self.folder_id]
            
            media = MediaFileUpload(file_path, mimetype='application/json')
            
            result = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,webViewLink'
            ).execute()
            
            return {
                'file_id': result['id'],
                'filename': result['name'],
                'size': result.get('size', '0'),
                'view_link': result['webViewLink']
            }
        
        return self._upload_with_retry(_do_upload, f"file '{drive_filename}'")
    
    def upload_scraper_results(self, json_file_path: str, items_count: int = 0, 
                             duplicates_skipped: int = 0, failed_extractions: int = 0,
                             scraper_type: str = None) -> Optional[Dict]:
        """
        Upload scraper results to Google Drive and trigger webhook
        
        Args:
            json_file_path: Path to the JSON file to upload
            items_count: Number of items scraped
            duplicates_skipped: Number of duplicates skipped
            failed_extractions: Number of failed extractions
            scraper_type: Type of scraper (optional, uses instance default if not provided)
        
        Returns:
            Dict with upload details or None if failed
        """
        try:
            effective_scraper_type = scraper_type or self.scraper_type
            
            if not os.path.exists(json_file_path):
                logger.error(f"File not found: {json_file_path}")
                return None
            
            filename = os.path.basename(json_file_path)
            content_type = "posts" if effective_scraper_type == "linkedin_posts" else "jobs"
            
            logger.info(f"Starting upload of {items_count} {content_type} to Google Drive...")
            logger.info(f"Local file: {json_file_path}")
            
            # Upload main file
            logger.info(f"Uploading {content_type} file...")
            main_upload = self._upload_file(json_file_path, filename)
            
            if not main_upload:
                logger.error(f"Failed to upload {content_type} file")
                return None
            
            logger.info(f"File uploaded successfully: {main_upload['filename']} ({main_upload['size']} bytes)")
            
            # Log summary
            logger.info("=" * 60)
            logger.info("UPLOAD COMPLETED SUCCESSFULLY!")
            logger.info(f"Uploaded {items_count} {content_type}, failed extractions: {failed_extractions}")
            if duplicates_skipped > 0:
                logger.info(f"Skipped {duplicates_skipped} duplicates")
            logger.info(f"View file: {main_upload['view_link']}")
            
            # Trigger webhook
            logger.info("Triggering n8n workflow...")
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            stats_key = 'posts_scraped' if effective_scraper_type == "linkedin_posts" else 'jobs_scraped'
            
            webhook_success = self.webhook_notifier.trigger_n8n_workflow(
                file_info={
                    'filename': main_upload['filename'],
                    'drive_file_id': main_upload['file_id'],
                    'size_bytes': main_upload['size'],
                    'view_link': main_upload['view_link'],
                    'completed_at': current_time
                },
                scrape_stats={
                    stats_key: items_count,
                    'duplicates_skipped': duplicates_skipped,
                    'failed_extractions': failed_extractions
                }
            )
            
            if webhook_success:
                logger.info("n8n workflow triggered successfully!")
            else:
                logger.warning("Failed to trigger n8n workflow (but upload was successful)")
            
            logger.info("=" * 60)
            
            return {
                'main_file': main_upload,
                'webhook_triggered': webhook_success,
                'summary': f"Uploaded {items_count} {content_type}, failed: {failed_extractions}"
            }
            
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return None