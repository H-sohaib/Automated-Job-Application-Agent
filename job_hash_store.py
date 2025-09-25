import sqlite3
import hashlib
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class JobHashStore:
    """Manages a database of job hashes to prevent duplicate scraping."""
    
    def __init__(self, db_path='data/job_hashes.db', expiry_days=30):
        """
        Initialize the job hash store.
        
        Args:
            db_path: Path to the SQLite database file
            expiry_days: Number of days after which to consider a job hash expired
        """
        self.db_path = db_path
        self.expiry_days = expiry_days
        self._ensure_dir_exists()
        self._init_db()
    
    def _ensure_dir_exists(self):
        """Ensure the directory for the database exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _init_db(self):
        """Initialize the database if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_hashes (
                    hash TEXT PRIMARY KEY,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    basic_hash TEXT
                )
            ''')
            # Create an index on the basic_hash field for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_basic_hash ON job_hashes(basic_hash)')
            conn.commit()
        finally:
            conn.close()
    
    def _generate_basic_hash(self, job_data):
        """
        Generate a simple hash using just the job title, company and location.
        
        Args:
            job_data: Dictionary containing job information
        
        Returns:
            str: A hash string based on basic job details
        """
        # Use only the stable fields available before clicking on the job
        hash_input = f"{job_data['title']}|{job_data['company']}|{job_data['location']}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _generate_full_hash(self, job_data):
        """
        Generate a complete hash for a job based on all critical fields.
        
        Args:
            job_data: Dictionary containing job information
        
        Returns:
            str: A hash string that uniquely identifies the job
        """
        # Use all stable fields including description
        desc_part = job_data.get('description', '')[:100] if job_data.get('description') else ''
        hash_input = f"{job_data['title']}|{job_data['company']}|{job_data['location']}|{desc_part}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def is_basic_duplicate(self, job_data):
        """
        Check if a job is likely a duplicate based only on basic fields.
        Used for preliminary checks before fetching full description.
        
        Args:
            job_data: Dictionary containing basic job information
        
        Returns:
            bool: True if the job is likely a duplicate, False otherwise
        """
        basic_hash = self._generate_basic_hash(job_data)
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM job_hashes WHERE basic_hash = ?", (basic_hash,))
            count = cursor.fetchone()[0]
            return count > 0
        finally:
            conn.close()
    
    def is_duplicate(self, job_data):
        """
        Check if a job has been seen before using the full hash.
        Should be called after retrieving the full job details including description.
        
        Args:
            job_data: Dictionary containing complete job information
        
        Returns:
            bool: True if the job is a duplicate, False otherwise
        """
        # Generate both hash types
        full_hash = self._generate_full_hash(job_data)
        basic_hash = self._generate_basic_hash(job_data)
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT hash FROM job_hashes WHERE hash = ?", (full_hash,))
            result = cursor.fetchone()
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if result:
                # Update the last_seen timestamp
                cursor.execute(
                    "UPDATE job_hashes SET last_seen = ? WHERE hash = ?", 
                    (now, full_hash)
                )
                conn.commit()
                return True
            else:
                # Insert new hash
                cursor.execute(
                    "INSERT INTO job_hashes (hash, first_seen, last_seen, title, company, location, basic_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (full_hash, now, now, job_data['title'], job_data['company'], job_data['location'], basic_hash)
                )
                conn.commit()
                return False
        finally:
            conn.close()
    
    def cleanup_expired(self):
        """Remove job hashes that haven't been seen in the expiry period."""
        cutoff_date = (datetime.now() - timedelta(days=self.expiry_days)).strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM job_hashes WHERE last_seen < ?", (cutoff_date,))
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.info(f"Removed {deleted_count} expired job hashes older than {self.expiry_days} days")
        finally:
            conn.close()
    
    def get_stats(self):
        """Get statistics about the job hash store."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM job_hashes")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT MIN(first_seen), MAX(last_seen) FROM job_hashes")
            result = cursor.fetchone()
            first = result[0] if result and result[0] is not None else "N/A"
            last = result[1] if result and result[1] is not None else "N/A"
            
            return {
                "total_jobs_tracked": total,
                "oldest_job_date": first,
                "newest_job_date": last
            }
        finally:
            conn.close()