from plugins.db import get_tracked_titles, is_processed, mark_processed
from plugins.huggingface_uploader import send_to_huggingface
from config import LOGGER
import feedparser
import asyncio
import traceback
from datetime import datetime, timezone

logger = LOGGER(__name__)

RSS_URL = "https://subsplease.org/rss/?t&r=720"
_rss_task = None

async def check_rss_feed(client):
    """RSS feed checker function"""
    while True:
        try:
            current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            logger.info(f"[{current_time}] Checking RSS feed")
            
            # Parse RSS feed
            feed = feedparser.parse(RSS_URL)
            if feed.bozo:
                logger.error(f"RSS Feed parsing error: {feed.bozo_exception}")
                await asyncio.sleep(60)
                continue
                
            # Get tracked titles
            titles = await get_tracked_titles()
            logger.info(f"Found {len(titles)} tracked titles")
            
            # Check each feed entry
            for item in feed.entries:
                title = item.title
                link = item.link
                guid = item.guid
                
                for tracked in titles:
                    if tracked.lower() in title.lower():
                        logger.info(f"Match found! '{tracked}' in '{title}'")
                        
                        # Skip if already processed
                        if await is_processed(guid):
                            continue
                            
                        try:
                            # Convert to direct download link
                            torrent_id = link.split('/view/')[1].split('/')[0]
                            direct_link = f"https://nyaa.si/download/{torrent_id}.torrent"
                            
                            # Send to HuggingFace
                            result = await send_to_huggingface(title, direct_link)
                            
                            if result and result.get("status") == "success":
                                await mark_processed(guid)
                                logger.info(f"Successfully processed: {title}")
                            else:
                                error = result.get("error", "Unknown error") if result else "No response"
                                logger.error(f"Failed to process {title}: {error}")
                                
                        except Exception as e:
                            logger.error(f"Error processing {title}: {str(e)}")
                            logger.error(traceback.format_exc())
                            
                        await asyncio.sleep(1)
                        
        except Exception as e:
            logger.error(f"Error in RSS checker: {str(e)}")
            logger.error(traceback.format_exc())
            
        await asyncio.sleep(60)  # Wait 60 seconds before next check

async def start_rss_checker(client):
    """Start the RSS checker task"""
    global _rss_task
    
    try:
        if _rss_task and not _rss_task.done():
            return
            
        _rss_task = asyncio.create_task(check_rss_feed(client))
        logger.info("RSS checker task started")
        
    except Exception as e:
        logger.error(f"Error starting RSS checker: {str(e)}")
        raise

async def stop_rss_checker(client):
    """Stop the RSS checker task"""
    global _rss_task
    
    try:
        if _rss_task and not _rss_task.done():
            _rss_task.cancel()
            try:
                await _rss_task
            except asyncio.CancelledError:
                pass
            _rss_task = None
            logger.info("RSS checker task stopped")
            
    except Exception as e:
        logger.error(f"Error stopping RSS checker: {str(e)}")
        raise