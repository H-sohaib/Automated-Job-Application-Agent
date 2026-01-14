"""
SQLite database store for LinkedIn scraped post IDs.
Replaces the JSON-based duplicate detection system.
"""

import sqlite3
import logging
import os
from datetime import datetime
from typing import Set, Optional

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = 'data/linkedin_posts.db'


def init_database():
    """Initialize the SQLite database and create tables if they don't exist."""
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create table for storing scraped post IDs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraped_posts (
                post_id TEXT PRIMARY KEY,
                scraped_date TEXT NOT NULL,
                person_name TEXT,
                post_link TEXT
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_scraped_date 
            ON scraped_posts(scraped_date)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database initialized successfully at: {DB_PATH}")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False


def load_scraped_ids() -> Set[str]:
    """
    Load all scraped post IDs from the database.
    
    Returns:
        Set[str]: Set of all previously scraped post IDs
    """
    try:
        # Initialize database if it doesn't exist
        init_database()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT post_id FROM scraped_posts')
        rows = cursor.fetchall()
        
        conn.close()
        
        post_ids = {row[0] for row in rows}
        logger.debug(f"Loaded {len(post_ids)} post IDs from database")
        
        return post_ids
        
    except Exception as e:
        logger.error(f"Error loading scraped IDs from database: {e}")
        return set()


def save_scraped_id(post_id: str, person_name: Optional[str] = None, 
                    post_link: Optional[str] = None) -> bool:
    """
    Save a scraped post ID to the database.
    
    Args:
        post_id: The LinkedIn post ID
        person_name: Optional person/company name
        post_link: Optional post URL
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Initialize database if it doesn't exist
        init_database()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        scraped_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Use INSERT OR REPLACE to handle duplicates
        cursor.execute('''
            INSERT OR REPLACE INTO scraped_posts 
            (post_id, scraped_date, person_name, post_link)
            VALUES (?, ?, ?, ?)
        ''', (post_id, scraped_date, person_name, post_link))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Saved post ID '{post_id}' to database")
        return True
        
    except Exception as e:
        logger.error(f"Error saving post ID to database: {e}")
        return False


def is_post_scraped(post_id: str) -> bool:
    """
    Check if a post ID has already been scraped.
    
    Args:
        post_id: The LinkedIn post ID to check
        
    Returns:
        bool: True if post was already scraped, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT 1 FROM scraped_posts WHERE post_id = ? LIMIT 1', (post_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result is not None
        
    except Exception as e:
        logger.error(f"Error checking if post is scraped: {e}")
        return False


def get_total_scraped_count() -> int:
    """
    Get the total number of scraped posts in the database.
    
    Returns:
        int: Total count of scraped posts
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM scraped_posts')
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count
        
    except Exception as e:
        logger.error(f"Error getting scraped count: {e}")
        return 0


def clear_old_posts(days_old: int = 90):
    """
    Remove posts older than specified days from the database.
    Useful for database maintenance.
    
    Args:
        days_old: Number of days to keep (default: 90)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now()
        from datetime import timedelta
        cutoff_date = cutoff_date - timedelta(days=days_old)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('DELETE FROM scraped_posts WHERE scraped_date < ?', (cutoff_str,))
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted {deleted} posts older than {days_old} days from database")
        return deleted
        
    except Exception as e:
        logger.error(f"Error clearing old posts: {e}")
        return 0
