# rss_checker.py
from plugins.db import get_tracked_titles, is_processed, mark_processed
from plugins.huggingface_uploader import send_to_huggingface
from config import LOGGER
import feedparser, asyncio, traceback  # Added traceback for better error logging
from datetime import datetime, timezone

logger = LOGGER(__name__)

RSS_URL = "https://subsplease.org/rss/?t&r=720"

async def check_feed(bot):
    logger.info("RSS checker service started")
    while True:
        try:
            if bot.feed_enabled:
                current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                logger.info(f"Starting RSS feed check at {current_time}")
                
                feed = feedparser.parse(RSS_URL)
                if feed.bozo:
                    logger.error(f"RSS Feed parsing error: {feed.bozo_exception}")
                    continue
                
                titles = await get_tracked_titles()
                logger.info(f"Found {len(titles)} tracked titles")
                
                entry_count = len(feed.entries)
                logger.info(f"Processing {entry_count} feed entries")
                
                for item in feed.entries:
                    title = item.title
                    link = item.link
                    guid = item.guid
                    logger.debug(f"Processing feed item: {title}")
                    
                    for tracked in titles:
                        if tracked.lower() in title.lower():
                            logger.info(f"Match found! Tracked title '{tracked}' found in '{title}'")
                            
                            if await is_processed(guid):
                                logger.debug(f"Item already processed (GUID: {guid})")
                                continue
                            
                            try:
                                # Convert nyaa.si view link to direct download link
                                if 'nyaa.si/view' in link:
                                    torrent_id = link.split('/view/')[1].split('/')[0]
                                    direct_link = f"https://nyaa.si/download/{torrent_id}.torrent"
                                    logger.info(f"Direct download link: {direct_link}")
                                else:
                                    logger.error(f"Invalid link format: {link}")
                                    continue

                                # Mark as processed
                                await mark_processed(guid)
                                
                                # Send to HuggingFace
                                logger.info(f"Sending to HuggingFace - Title: {title}")
                                logger.info(f"Sending to HuggingFace - Link: {direct_link}")
                                
                                result = await send_to_huggingface(title, direct_link)
                                logger.info(f"HuggingFace Response: {result}")
                                
                                if not result:
                                    logger.error("No response from HuggingFace")
                                    continue
                                    
                                if result.get("status") == "success":
                                    logger.info(f"Successfully processed: {title}")
                                else:
                                    error = result.get("error", "Unknown error")
                                    logger.error(f"Failed to process: {title}. Error: {error}")
                                
                            except Exception as e:
                                logger.error(f"Error processing '{title}': {str(e)}")
                                logger.error(traceback.format_exc())  # Add full traceback
                                continue
                
                logger.info("Completed RSS feed check cycle")
            else:
                logger.debug("Feed checking is currently disabled")
                
        except Exception as e:
            logger.error(f"Critical error: {str(e)}")
            logger.error(traceback.format_exc())
            
        finally:
            await asyncio.sleep(600)  # 10 minutes