# rss_checker.py
from plugins.db import get_tracked_titles, is_processed, mark_processed
from plugins.huggingface_uploader import send_to_huggingface
from config import LOGGER
import feedparser, asyncio
from datetime import datetime, timezone

# Initialize logger for this module
logger = LOGGER(__name__)

RSS_URL = "https://subsplease.org/rss/?t&r=720"

async def check_feed(bot):  # now receives the Bot object
    logger.info("RSS checker service started")
    while True:
        try:
            if bot.feed_enabled:
                current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                logger.info(f"Starting RSS feed check at {current_time}")
                
                # Fetch and parse RSS feed
                logger.debug(f"Fetching RSS feed from {RSS_URL}")
                feed = feedparser.parse(RSS_URL)
                if feed.bozo:
                    logger.error(f"RSS Feed parsing error: {feed.bozo_exception}")
                    continue
                
                # Get tracked titles
                logger.debug("Retrieving tracked titles from database")
                titles = await get_tracked_titles()
                logger.info(f"Found {len(titles)} tracked titles")
                
                # Process feed entries
                entry_count = len(feed.entries)
                logger.info(f"Processing {entry_count} feed entries")
                
                for item in feed.entries:
                    title = item.title
                    link = item.link
                    guid = item.guid
                    logger.debug(f"Checking feed item: '{title}'")
                    
                    for tracked in titles:
                        if tracked.lower() in title.lower():
                            logger.info(f"Match found! Tracked title '{tracked}' found in '{title}'")
                            
                            # Check if already processed
                            if await is_processed(guid):
                                logger.debug(f"Item already processed (GUID: {guid})")
                                continue
                                
                            try:
                                # Process new item
                                logger.info(f"Processing new item: {title}")
                                await mark_processed(guid)
                                logger.debug(f"Marked as processed: {guid}")
                                
                                # Send to HuggingFace
                                await send_to_huggingface(title, link)
                                logger.info(f"Successfully uploaded to HuggingFace: {title}")
                                
                            except Exception as e:
                                logger.error(f"Error processing item '{title}': {str(e)}", exc_info=True)
                
                logger.info("Completed RSS feed check cycle")
            else:
                logger.debug("Feed checking is currently disabled")
                
        except Exception as e:
            logger.error(f"Critical error in RSS checker: {str(e)}", exc_info=True)
            
        finally:
            # Sleep before next check
            sleep_time = 600  # 10 minutes
            logger.debug(f"Sleeping for {sleep_time} seconds before next check")
            await asyncio.sleep(sleep_time)