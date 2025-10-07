import os
import json
import pickle
from datetime import datetime
import logging
import time
from typing import Optional, Dict, Any
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
import io
from config import SCOPES, GOOGLE_DRIVE_FOLDER_ID, GOOGLE_DRIVE_CREDENTIALS_PATH
from utility.webhook_notifier import WebhookNotifier

logger = logging.getLogger(__name__)

class GoogleDriveUploader:
    """Simple Google Drive uploader for scraper results with retry mechanism"""
    
    def __init__(self):
        self.service: Optional[Resource] = None
        self.folder_id = GOOGLE_DRIVE_FOLDER_ID
        self.token_path = 'data/google_drive_token.pickle'
        self.webhook_notifier = WebhookNotifier()  # Add webhook notifier
        
        if not self._authenticate():
            raise Exception("Failed to authenticate with Google Drive")
    
    def _authenticate(self) -> bool:
        """Authenticate with Google Drive API with improved error handling"""
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
                    # Delete corrupted token file
                    try:
                        os.remove(self.token_path)
                        logger.info("Removed corrupted token file")
                    except:
                        pass
                    creds = None
            
            # Check credentials validity and refresh if needed
            if creds:
                if not creds.valid:
                    if creds.expired and creds.refresh_token:
                        try:
                            logger.info("Refreshing expired credentials...")
                            creds.refresh(Request())
                            logger.info("Credentials refreshed successfully")
                        except Exception as e:
                            logger.error(f"Failed to refresh credentials: {e}")
                            # Delete invalid token and force re-auth
                            try:
                                os.remove(self.token_path)
                                logger.info("Removed invalid token file")
                            except:
                                pass
                            creds = None
                    else:
                        logger.warning("Credentials invalid and no refresh token available")
                        creds = None
            
            # Get new credentials if needed
            if not creds:
                if not os.path.exists(GOOGLE_DRIVE_CREDENTIALS_PATH):
                    logger.error(f"Credentials file not found: {GOOGLE_DRIVE_CREDENTIALS_PATH}")
                    return False
                
                logger.info("Starting OAuth flow for new credentials...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    GOOGLE_DRIVE_CREDENTIALS_PATH, SCOPES)
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
            self.service = None
            return False
    
    
    def _is_network_error(self, error: Exception) -> bool:
        """Check if error is a network/connectivity issue that can be retried"""
        error_str = str(error).lower()
        network_indicators = [
            'unable to find the server',
            'connection refused',
            'network is unreachable',
            'timeout',
            'connection timed out',
            'connection reset',
            'dns resolution failed',
            'name resolution failure',
            'socket.gaierror',
            'connectionerror',
            'httperror: 503',  # Service unavailable
            'httperror: 502',  # Bad gateway
            'httperror: 504',  # Gateway timeout
            'httperror: 429',  # Too many requests
        ]
        return any(indicator in error_str for indicator in network_indicators)

    def _upload_with_retry(self, upload_func, description: str, max_retries: int = 10, 
                          initial_delay: float = 2.0) -> Optional[Dict]:
        """
        Execute upload function with exponential backoff retry for network errors
        
        Args:
            upload_func: Function to execute (should return Dict or None)
            description: Description for logging
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            
        Returns:
            Dict or None: Upload result or None if all retries failed
        """
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Upload attempt {attempt + 1}/{max_retries + 1}: {description}")
                result = upload_func()
                
                if result:
                    if attempt > 0:
                        logger.info(f"Upload successful on attempt {attempt + 1}: {description}")
                    return result
                else:
                    logger.warning(f"Upload returned None on attempt {attempt + 1}: {description}")
                    
            except Exception as e:
                is_network_error = self._is_network_error(e)
                
                if attempt == max_retries:
                    logger.error(f"Upload failed after {max_retries + 1} attempts: {description}")
                    logger.error(f"Final error: {e}")
                    return None
                
                if is_network_error:
                    delay = initial_delay * (1.5 ** attempt)  # Gentler exponential backoff
                    logger.warning(f"Network error on attempt {attempt + 1}: {e}")
                    logger.info(f"Retrying in {delay:.1f} seconds... ({max_retries - attempt} attempts remaining)")
                    
                    try:
                        time.sleep(delay)
                    except KeyboardInterrupt:
                        logger.info("Upload retry interrupted by user")
                        return None
                        
                else:
                    # Non-network error - don't retry
                    logger.error(f"Non-retryable error during upload: {e}")
                    return None
        
        return None
    
    def _upload_file(self, file_path: str, drive_filename: str) -> Optional[Dict]:
        """Upload a single file to Google Drive from disk"""
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
        
        return self._upload_with_retry(
            _do_upload, 
            f"main file '{drive_filename}'"
        )

    def _upload_json_content(self, data: Dict[str, Any], drive_filename: str) -> Optional[Dict]:
        """Upload a JSON document to Google Drive directly from memory"""
        def _do_upload():
            if not self.service:
                logger.error("Google Drive service not initialized")
                return None
            
            file_metadata: Dict[str, Any] = {'name': drive_filename}
            if self.folder_id:
                file_metadata['parents'] = [self.folder_id]

            payload = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
            buffer = io.BytesIO(payload)
            media = MediaIoBaseUpload(buffer, mimetype='application/json', resumable=False)

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
        
        return self._upload_with_retry(
            _do_upload, 
            f"metadata file '{drive_filename}'"
        )
    
    def upload_scraper_results(self, json_file_path: str, jobs_count: int = 0, 
                             duplicates_skipped: int = 0, failed_extractions: int = 0) -> Optional[Dict]:
        """
        Upload scraper results with metadata to Google Drive (with retry mechanism)
        """
        try:
            if not os.path.exists(json_file_path):
                logger.error(f"File not found: {json_file_path}")
                return None
            
            filename = os.path.basename(json_file_path)
            logger.info(f"Starting upload of {jobs_count} jobs to Google Drive...")
            logger.info(f"Local file: {json_file_path}")
            
            # 1) Upload main JSON file from disk with retry
            logger.info("Uploading main jobs file...")
            main_upload = self._upload_file(json_file_path, filename)
            if not main_upload:
                logger.error("Failed to upload main jobs file")
                return None
            
            logger.info(f"Main file uploaded successfully: {main_upload['filename']} ({main_upload['size']} bytes)")
            
            # 2) Upload metadata JSON directly from memory with retry
            logger.info("Uploading metadata file...")
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            metadata = {
                'scraping_session': {
                    'completed_at': current_time,
                    'jobs_scraped': jobs_count,
                    'duplicates_skipped': duplicates_skipped,
                    'failed_extractions': failed_extractions
                },
                'file_info': {
                    'drive_file_id': main_upload['file_id'],
                    'filename': main_upload['filename'],
                    'size_bytes': main_upload['size'],
                    'view_link': main_upload['view_link']
                }
            }
            
            metadata_drive_name = filename.replace('.json', '_metadata.json')
            metadata_upload = self._upload_json_content(metadata, metadata_drive_name)

            # Log results
            logger.info("=" * 60)
            logger.info("UPLOAD COMPLETED SUCCESSFULLY!")
            logger.info(f"Uploaded {jobs_count} jobs, skipped {duplicates_skipped} duplicates")
            logger.info(f"Main file: {main_upload['view_link']}")
            if metadata_upload:
                logger.info(f"Metadata file uploaded successfully")
            else:
                logger.warning("Metadata upload failed (but main file is safe)")
            
            # 3) Trigger n8n webhook after successful upload
            logger.info("Triggering n8n workflow...")
            webhook_success = self.webhook_notifier.trigger_n8n_workflow(
                file_info={
                    'filename': main_upload['filename'],
                    'drive_file_id': main_upload['file_id'],
                    'size_bytes': main_upload['size'],
                    'view_link': main_upload['view_link'],
                    'completed_at': current_time
                },
                scrape_stats={
                    'jobs_scraped': jobs_count,
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
                'metadata_file': metadata_upload,
                'webhook_triggered': webhook_success,
                'summary': f"Uploaded {jobs_count} jobs, skipped {duplicates_skipped} duplicates"
            }
            
        except KeyboardInterrupt:
            logger.info("Upload interrupted by user")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return None