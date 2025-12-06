from  helpers import *


async def perform_linkedin_scraping(page) -> Optional[int]:
    """
    Scrape LinkedIn saved posts with scrolling support and smart stop condition.
    
    Args:
        page: The Playwright page object to use for scraping
        
    Returns:
        int or None: Number of posts scraped, or None if scraping failed
    """
    global shutdown_flag
    
    logger.info("Starting LinkedIn posts scraping process...")
    
    try:
        # Create output filename
        output_filename = get_json_filename()
        logger.info(f"LinkedIn posts will be saved to: {output_filename}")
        
        # Load existing scraped IDs for smart stop condition (only if not in testing mode)
        scraped_ids = set()
        if not TESTING_MODE:
            scraped_ids = load_scraped_ids()
            logger.info(f"Loaded {len(scraped_ids)} previously scraped post IDs")
        else:
            logger.info("TESTING_MODE enabled - duplicate detection disabled")
        
        # Wait for post listings to load
        try:
            await page.wait_for_selector(LINKEDIN_POST_CONTAINER_SELECTOR, timeout=10000)
            logger.debug("LinkedIn post container selector found successfully")
        except Exception as e:
            logger.error(f"Could not find LinkedIn post listings: {e}")
            return None
        
        # Initialize tracking variables
        processed_post_keys = set()
        posts_count = 0
        failed_extractions = 0
        scroll_attempts = 0
        consecutive_existing_posts = 0  # Counter for smart stop condition
        
        
        # Allow unlimited scraping when MAX_POSTS_TO_SCRAPE <= 0
        post_limit = MAX_POSTS_TO_SCRAPE if MAX_POSTS_TO_SCRAPE > 0 else None
        limit_str = post_limit if post_limit is not None else "unlimited"
        logger.info(f"Starting LinkedIn scraping loop - target: {limit_str} posts, max scrolls: {MAX_SCROLL_ATTEMPTS}")
        logger.info(f"Smart stop condition: Will stop after {STOP_AFTER_EXISTING_POSTS} consecutive already-scraped posts")
        
        while scroll_attempts < MAX_SCROLL_ATTEMPTS :
            # Get current post elements
            post_elements = await page.query_selector_all(LINKEDIN_POST_CONTAINER_SELECTOR)
            current_post_count = len(post_elements)
            
            logger.debug(f"Found {current_post_count} post elements on page (scroll attempt {scroll_attempts})")
            
            # Process visible posts
            for post_element in post_elements:
                if shutdown_flag:
                    logger.warning("Shutdown signal received, stopping post processing")
                    break
                
                # Extract complete post information (including post link and ID)
                post_data = await extract_complete_post_info(page, post_element)
                if not post_data:
                    failed_extractions += 1
                    continue
                
                person_name = post_data.get('person_name', 'Unknown')
                posted_time = post_data.get('posted_time', 'Unknown')
                post_link = post_data.get('post_link', 'Unknown')
                post_id = post_data.get('post_id')
                
                # Create a unique key for this post to avoid duplicates in current session
                post_key = f"{person_name}_{posted_time}_{len(post_data.get('post_content', ''))}"
                
                # Skip if we've already processed this post in this session
                if post_key in processed_post_keys:
                    logger.debug(f"Skipping already processed post in this session by '{person_name}' at '{posted_time}'")
                    continue
                
                processed_post_keys.add(post_key)
                
                # Check if this post was already scraped in previous runs (smart stop condition)
                if post_id and post_id in scraped_ids:
                    consecutive_existing_posts += 1
                    logger.info(f"Post by '{person_name}' (ID: {post_id}) already exists. Consecutive existing: {consecutive_existing_posts}/{STOP_AFTER_EXISTING_POSTS}")
                    
                    # Smart stop condition: if we hit too many consecutive existing posts, stop
                    if consecutive_existing_posts >= STOP_AFTER_EXISTING_POSTS:
                        logger.info(f"Found {consecutive_existing_posts} consecutive already-scraped posts. Assuming all new posts have been processed. Stopping.")
                        break 
                    
                    continue  # Skip this post but continue processing
                else:
                    # Reset counter when we find a new post
                    consecutive_existing_posts = 0
                
                # Save post incrementally
                if save_post_incrementally(post_data, output_filename):
                    posts_count += 1
                    logger.info(f"Successfully processed NEW post {posts_count}: '{person_name}' - '{posted_time}' - ID: {post_id}")
                else:
                    logger.debug(f"Skipped saving post by '{person_name}' at '{posted_time}' (likely duplicate)")
                    continue
                
                # ADD THIS CHECK RIGHT AFTER THE FOR LOOP:
                # Smart stop condition: 
                if consecutive_existing_posts >= STOP_AFTER_EXISTING_POSTS:
                    logger.info(f"Stop condition met. Exiting main scraping loop.")
                    break  # Break the WHILE loop
                # Break out of the while loop if stop condition was met
                if consecutive_existing_posts >= STOP_AFTER_EXISTING_POSTS:
                    logger.info(f"Exiting main loop - stop condition met ({consecutive_existing_posts} consecutive existing posts)")
                    break

                # Check if we've reached the maximum number of posts
                if post_limit is not None and posts_count >= post_limit:
                    logger.info(f"Reached maximum post count ({posts_count})")
                    break
                
                # Add small delay between posts
                await human_sleep(SLEEP_SHORT)
            
            # Break if we've reached max posts or received shutdown signal
            if (post_limit is not None and posts_count >= post_limit) or shutdown_flag:
                break
            
            # Scroll down to load more posts
            logger.info("Scrolling to load more LinkedIn posts...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await human_sleep(SLEEP_SCROLL)
            
            # Check if new posts were loaded
            new_post_elements = await page.query_selector_all(LINKEDIN_POST_CONTAINER_SELECTOR)
            if len(new_post_elements) <= current_post_count:
                scroll_attempts += 1
                logger.info(f"No new posts loaded, scroll attempt {scroll_attempts}/{MAX_SCROLL_ATTEMPTS}")
            else:
                scroll_attempts = 0  # Reset counter if new posts found
                logger.info(f"Found {len(new_post_elements) - current_post_count} new posts after scrolling")
        
        # Log final statistics
        logger.info(f"LinkedIn scraping completed! Summary:")
        logger.info(f"  - Total NEW posts processed: {posts_count}")
        logger.info(f"  - Failed extractions: {failed_extractions}")
        logger.info(f"  - Consecutive existing posts at end: {consecutive_existing_posts}")
        logger.info(f"  - Shutdown requested: {shutdown_flag}")
        
        # Upload to Google Drive and trigger webhook
        if posts_count > 0 and output_filename and os.path.exists(output_filename) and not TESTING_MODE:
            try:
                from utility.google_drive_uploader import GoogleDriveUploader
                
                logger.info("Uploading LinkedIn results to Google Drive...")
                uploader = GoogleDriveUploader(scraper_type="linkedin_posts")
                
                upload_result = uploader.upload_scraper_results(
                    output_filename, 
                    posts_count, 
                    0,  # No duplicates tracking for LinkedIn (yet)
                    failed_extractions,
                )
                
                if upload_result:
                    logger.info("Upload successful!")
                    logger.info(f"View file: {upload_result['main_file']['view_link']}")
                else:
                    logger.error("Upload failed")
            except Exception as e:
                logger.error(f"Google Drive upload error: {e}")
        
        
        return posts_count
        
    except Exception as e:
        logger.error(f"Critical error in perform_linkedin_scraping: {e}")
        return None