import os
import json
import pickle
from datetime import datetime
import logging
from typing import Optional, Dict, Any
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import io  # <-- add
from config import SCOPES, GOOGLE_DRIVE_FOLDER_ID, GOOGLE_DRIVE_CREDENTIALS_PATH

logger = logging.getLogger(__name__)

class GoogleDriveUploader:
    """Simple Google Drive uploader for scraper results"""
    
    def __init__(self):
        self.service: Optional[Resource] = None
        self.folder_id = GOOGLE_DRIVE_FOLDER_ID
        self.token_path = 'data/google_drive_token.pickle'
        
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
                except Exception as e:
                    logger.warning(f"Could not load token; re-authenticating: {e}")
                    creds = None
            
            # Get new credentials if needed
            if not creds or not getattr(creds, "valid", False):
                if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
                    creds.refresh(Request())
                else:
                    if not os.path.exists(GOOGLE_DRIVE_CREDENTIALS_PATH):
                        logger.error(f"Credentials file not found: {GOOGLE_DRIVE_CREDENTIALS_PATH}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        GOOGLE_DRIVE_CREDENTIALS_PATH, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials
                try:
                    with open(self.token_path, 'wb') as token:
                        pickle.dump(creds, token)
                except Exception as e:
                    logger.warning(f"Could not save credentials: {e}")
            
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Google Drive authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            self.service = None
            return False
    
    def _upload_file(self, file_path: str, drive_filename: str) -> Optional[Dict]:
        """Upload a single file to Google Drive from disk"""
        try:
            if not self.service:
                logger.error("Google Drive service not initialized")
                return None
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            file_metadata: Dict[str, Any] = {'name': drive_filename}
            if self.folder_id:
                file_metadata['parents'] = [self.folder_id]  # List[str]
            
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
            
        except Exception as e:
            logger.error(f"Upload failed for {file_path}: {e}")
            return None

    def _upload_json_content(self, data: Dict[str, Any], drive_filename: str) -> Optional[Dict]:
        """Upload a JSON document to Google Drive directly from memory (avoids Windows file locks)"""
        try:
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
        except Exception as e:
            logger.error(f"Upload failed for in-memory JSON '{drive_filename}': {e}")
            return None
    
    def upload_scraper_results(self, json_file_path: str, jobs_count: int = 0, 
                             duplicates_skipped: int = 0, failed_extractions: int = 0) -> Optional[Dict]:
        """
        Upload scraper results with metadata to Google Drive
        """
        try:
            if not os.path.exists(json_file_path):
                logger.error(f"File not found: {json_file_path}")
                return None
            
            # 1) Upload main JSON file from disk
            main_upload = self._upload_file(json_file_path, os.path.basename(json_file_path))
            if not main_upload:
                return None
            
            # 2) Upload metadata JSON directly from memory (no temp file on disk)
            metadata = {
                'scraping_session': {
                    'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
            metadata_drive_name = os.path.basename(json_file_path).replace('.json', '_metadata.json')
            metadata_upload = self._upload_json_content(metadata, metadata_drive_name)

            logger.info(f"Successfully uploaded {jobs_count} jobs to Google Drive")
            logger.info(f"Main file: {main_upload['view_link']}")
            
            return {
                'main_file': main_upload,
                'metadata_file': metadata_upload,
                'summary': f"Uploaded {jobs_count} jobs, skipped {duplicates_skipped} duplicates"
            }
            
        except Exception as e:
            logger.error(f"Failed to upload scraper results: {e}")
            return None