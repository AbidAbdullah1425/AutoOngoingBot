# rss_checker.py
from plugins.db import get_tracked_titles, is_processed, mark_processed
from plugins.huggingface_uploader import send_to_huggingface
from config import LOGGER
import feedparser, asyncio, traceback
from datetime import datetime, timezone

logger = LOGGER(__name__)

RSS_URL = "https://subsplease.org/rss/?t&r=720"

async def process_item(title, link, guid):
    """Process a single RSS feed item"""
    try:
        # Convert nyaa.si view link to direct download link
        torrent_id = link.split('/view/')[1].split('/')[0]
        direct_link = f"https://nyaa.si/download/{torrent_id}.torrent"
        logger.info(f"Processing: {title} with link: {direct_link}")
        
        # Send to HuggingFace
        result = await send_to_huggingface(title, direct_link)
        if result and result.get("status") == "success":
            logger.info(f"Successfully sent to HuggingFace: {title}")
            await mark_processed(guid)
            return True
        else:
            error = result.get("error", "Unknown error") if result else "No response"
            logger.error(f"Failed to process {title}: {error}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing {title}: {str(e)}")
        logger.error(traceback.format_exc())
        return False

async def check_feed(bot):
    """Main RSS checker function"""
    logger.info("RSS checker service started")
    
    while True:
        try:
            if not bot.feed_enabled:
                logger.debug("Feed checking is disabled")
                await asyncio.sleep(60)
                continue
                
            current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            logger.info(f"Starting RSS feed check at {current_time}")
            
            # Fetch and parse RSS feed
            feed = feedparser.parse(RSS_URL)
            if feed.bozo:
                logger.error(f"RSS Feed parsing error: {feed.bozo_exception}")
                await asyncio.sleep(60)
                continue
            
            # Get tracked titles
            titles = await get_tracked_titles()
            logger.info(f"Found {len(titles)} tracked titles")
            
            # Process feed entries
            entry_count = len(feed.entries)
            logger.info(f"Processing {entry_count} feed entries")
            
            for item in feed.entries:
                title = item.title
                link = item.link
                guid = item.guid
                
                for tracked in titles:
                    if tracked.lower() in title.lower():
                        logger.info(f"Match found! Tracked title '{tracked}' found in '{title}'")
                        
                        # Check if already processed
                        if await is_processed(guid):
                            logger.debug(f"Already processed: {guid}")
                            continue
                        
                        # Process the item
                        success = await process_item(title, link, guid)
                        if success:
                            logger.info(f"Successfully processed: {title}")
                        else:
                            logger.error(f"Failed to process: {title}")
                        
                        # Small delay between items to prevent overload
                        await asyncio.sleep(1)
            
            logger.info("Completed RSS feed check cycle")
            
        except Exception as e:
            logger.error(f"Critical error in RSS checker: {str(e)}")
            logger.error(traceback.format_exc())
        
        # Wait before next check (10 minutes)
        await asyncio.sleep(600)