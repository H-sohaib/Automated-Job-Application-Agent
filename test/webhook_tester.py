import logging
import sys
import os
from datetime import datetime
# Add the parent directory (project root) to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utility.webhook_notifier import WebhookNotifier
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def display_webhook_menu():
    """Display webhook selection menu"""
    print("\n" + "=" * 60)
    print("           WEBHOOK TESTER - SELECT WEBHOOK")
    print("=" * 60)
    print("Which webhook would you like to test?")
    print()
    print("1. Google Jobs Webhook")
    print("2. LinkedIn Posts Webhook")
    print("3. Exit")
    print()
    print("=" * 60)

def get_webhook_choice():
    """Get and validate webhook choice"""
    display_webhook_menu()
    while True:
        try:
            choice = int(input("Enter your choice (1-3): ").strip())
            if choice in [1, 2, 3]:
                return choice
            else:
                print("Please enter 1, 2, or 3")
        except ValueError:
            print("Please enter a valid number (1, 2, or 3)")

def test_webhook_with_existing_file(scraper_type="google_jobs"):
    """Test webhook with existing file information"""
    
    scraper_name = "LinkedIn" if scraper_type == "linkedin_posts" else "Google Jobs"
    content_type = "posts" if scraper_type == "linkedin_posts" else "jobs"
    
    print(f"\n" + "=" * 60)
    print(f"           {scraper_name.upper()} WEBHOOK TEST WITH EXISTING FILE")
    print("=" * 60)
    
    try:
        # Get file information from user
        print("Enter information about your existing file:")
        filename = input(f"Filename (e.g., linkedin_saved_posts_20251007_143022.json): ").strip()
        if not filename:
            print("❌ Filename is required!")
            return False
            
        drive_file_id = input("Google Drive file ID: ").strip()
        if not drive_file_id:
            print("❌ Drive file ID is required!")
            return False
            
        view_link = f"https://drive.google.com/file/d/{drive_file_id}/view"
        
        # Get stats from user
        if scraper_type == "linkedin_posts":
            items_count = int(input("Number of posts scraped: ") or "0")
            duplicates_skipped = 0  # LinkedIn doesn't track duplicates yet
        else:
            items_count = int(input("Number of jobs scraped: ") or "0")
            duplicates_skipped = int(input("Duplicates skipped (default 0): ") or "0")
            
        failed_extractions = int(input("Failed extractions (default 0): ") or "0")
        
        # Calculate estimated file size
        estimated_size = max(items_count * 16384, 1024)
        size_input = input(f"File size in bytes (default {estimated_size}): ").strip()
        file_size = size_input if size_input else str(estimated_size)
        
        # Create file info and stats
        file_info = {
            'filename': filename,
            'drive_file_id': drive_file_id,
            'size_bytes': file_size,
            'view_link': view_link,
            'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if scraper_type == "linkedin_posts":
            scrape_stats = {
                'posts_scraped': items_count,
                'duplicates_skipped': 0,
                'failed_extractions': failed_extractions
            }
        else:
            scrape_stats = {
                'jobs_scraped': items_count,
                'duplicates_skipped': duplicates_skipped,
                'failed_extractions': failed_extractions
            }
        
        # Display summary
        print(f"\n📋 Test Summary:")
        print(f"  - Scraper Type: {scraper_name}")
        print(f"  - {content_type.title()} scraped: {items_count}")
        if duplicates_skipped > 0:
            print(f"  - Duplicates skipped: {duplicates_skipped}")
        print(f"  - Failed extractions: {failed_extractions}")
        print(f"  - Filename: {filename}")
        print(f"  - Drive ID: {drive_file_id}")
        print(f"  - File size: {file_size} bytes")
        print(f"  - View link: {view_link}")
        print()
        
        # Confirm before sending
        confirm = input("Send this webhook? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ Test cancelled by user")
            return False
        
        # Initialize webhook notifier for the specific scraper type
        notifier = WebhookNotifier(scraper_type=scraper_type)
        
        print(f"🚀 Sending {scraper_name} webhook...")
        success = notifier.trigger_n8n_workflow(
            file_info=file_info,
            scrape_stats=scrape_stats,
            scraper_type=scraper_type
        )
        
        if success:
            print(f"✅ {scraper_name} webhook sent successfully!")
            print("Check your n8n workflow to see if it received the data.")
        else:
            print(f"❌ {scraper_name} webhook failed!")
            print("Check the logs above for error details.")
            
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️  Test cancelled by user")
        return False
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during webhook test: {e}")
        logger.error(f"Webhook test error: {e}")
        return False

def test_webhook_with_simulated_data(scraper_type="google_jobs"):
    """Test webhook with simulated data"""
    
    scraper_name = "LinkedIn" if scraper_type == "linkedin_posts" else "Google Jobs"
    content_type = "posts" if scraper_type == "linkedin_posts" else "jobs"
    
    print(f"\n" + "=" * 60)
    print(f"           {scraper_name.upper()} WEBHOOK TEST WITH SIMULATED DATA")
    print("=" * 60)
    
    # Initialize the webhook notifier for the specific scraper type
    notifier = WebhookNotifier(scraper_type=scraper_type)
    
    # Create simulated data based on scraper type
    if scraper_type == "linkedin_posts":
        simulated_file_info = {
            'filename': 'linkedin_saved_posts_20251007_143022.json',
            'drive_file_id': '1ABC123def456GHI789jkl',
            'size_bytes': '185760',  # ~180KB
            'view_link': 'https://drive.google.com/file/d/1ABC123def456GHI789jkl/view',
            'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        simulated_scrape_stats = {
            'posts_scraped': 12,
            'duplicates_skipped': 0,
            'failed_extractions': 2
        }
        
        print(f"Testing {scraper_name} webhook with simulated data:")
        print(f"  - Posts scraped: {simulated_scrape_stats['posts_scraped']}")
        print(f"  - Failed extractions: {simulated_scrape_stats['failed_extractions']}")
    else:
        simulated_file_info = {
            'filename': 'jobs_20251007_143022.json',
            'drive_file_id': '1ABC123def456GHI789jkl',
            'size_bytes': '245760',  # ~240KB
            'view_link': 'https://drive.google.com/file/d/1ABC123def456GHI789jkl/view',
            'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        simulated_scrape_stats = {
            'jobs_scraped': 15,
            'duplicates_skipped': 3,
            'failed_extractions': 1
        }
        
        print(f"Testing {scraper_name} webhook with simulated data:")
        print(f"  - Jobs scraped: {simulated_scrape_stats['jobs_scraped']}")
        print(f"  - Duplicates skipped: {simulated_scrape_stats['duplicates_skipped']}")
        print(f"  - Failed extractions: {simulated_scrape_stats['failed_extractions']}")
    
    print(f"  - File: {simulated_file_info['filename']}")
    print(f"  - Size: {simulated_file_info['size_bytes']} bytes")
    print()
    
    try:
        print(f"🚀 Sending {scraper_name} webhook notification...")
        success = notifier.trigger_n8n_workflow(
            file_info=simulated_file_info,
            scrape_stats=simulated_scrape_stats,
            scraper_type=scraper_type
        )
        
        if success:
            print(f"✅ {scraper_name} webhook notification sent successfully!")
            print("Check your n8n workflow to see if it received the data.")
        else:
            print(f"❌ {scraper_name} webhook notification failed!")
            print("Check the logs above for error details.")
            
        return success
            
    except Exception as e:
        print(f"❌ Error during {scraper_name} webhook test: {e}")
        logger.error(f"Webhook test error: {e}")
        return False

def run_webhook_tests():
    """Main function to run webhook tests"""
    
    print("=" * 60)
    print("           WEBHOOK NOTIFIER TESTER")
    print("=" * 60)
    print("This script will test webhook notification functionality")
    print("for both Google Jobs and LinkedIn scrapers")
    print()
    
    while True:
        webhook_choice = get_webhook_choice()
        
        if webhook_choice == 3:
            print("\nExiting webhook tester. Goodbye! 👋")
            break
        
        # Determine scraper type
        if webhook_choice == 1:
            scraper_type = "google_jobs"
            scraper_name = "Google Jobs"
        else:
            scraper_type = "linkedin_posts"
            scraper_name = "LinkedIn"
        
        print(f"\n🎯 Selected: {scraper_name} Webhook")
        
        # Test options menu
        while True:
            print(f"\n{scraper_name} Webhook Test Options:")
            print("1. Test with existing file (specify your file details)")
            print("2. Test with simulated data")
            print("3. Back to webhook selection")
            
            try:
                test_choice = int(input("\nEnter your choice (1-3): ").strip())
                
                if test_choice == 1:
                    success = test_webhook_with_existing_file(scraper_type)
                    if success:
                        print(f"\n✅ {scraper_name} webhook test completed successfully!")
                    else:
                        print(f"\n❌ {scraper_name} webhook test failed!")
                        
                elif test_choice == 2:
                    success = test_webhook_with_simulated_data(scraper_type)
                    if success:
                        print(f"\n✅ {scraper_name} webhook test completed successfully!")
                    else:
                        print(f"\n❌ {scraper_name} webhook test failed!")
                        
                elif test_choice == 3:
                    break
                else:
                    print("Please enter 1, 2, or 3")
                    
            except ValueError:
                print("Please enter a valid number (1, 2, or 3)")
            except KeyboardInterrupt:
                print("\n⚠️  Test interrupted by user")
                break

if __name__ == "__main__":
    try:
        run_webhook_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Webhook tester interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Unexpected error in webhook tester: {e}")