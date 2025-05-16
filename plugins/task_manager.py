from plugins.db import get_tracked_titles, is_processed, mark_processed
from plugins.huggingface_uploader import send_to_huggingface
from config import LOGGER, BOT_USERNAME, DB_CHANNEL_ID
import feedparser
import asyncio
import traceback
from datetime import datetime, timezone
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from base64 import b64encode
from bot import Bot

logger = LOGGER(__name__)

RSS_URL = "https://subsplease.org/rss/?t&r=720"
_rss_task = None
_latest_processed = None

# Encode function for creating shareable links
async def encode(string):
    return b64encode(string.encode()).decode()

async def create_share_link(message_id):
    """Create a shareable link from a message ID"""
    try:
        # Generate base64 string using DB_CHANNEL_ID
        base64_string = await encode(f"get-{message_id * abs(DB_CHANNEL_ID)}")
        
        # Create shareable link using BOT_USERNAME
        link = f"https://t.me/{BOT_USERNAME}?start={base64_string}"
        
        # Create button markup
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔁 Share URL", 
                url=f'https://telegram.me/share/url?url={link}')
        ]])
        
        return {
            "status": "ok",
            "link": link,
            "reply_markup": reply_markup
        }
    except Exception as e:
        logger.error(f"Error creating share link: {str(e)}")
        return {"status": "error", "error": str(e)}

async def check_rss_feed(client):
    """RSS feed checker function"""
    global _latest_processed
    
    while True:
        try:
            current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            logger.info(f"[{current_time}] Checking RSS feed")
            
            feed = feedparser.parse(RSS_URL)
            if feed.bozo:
                logger.error(f"RSS Feed parsing error: {feed.bozo_exception}")
                await asyncio.sleep(60)
                continue
            
            titles = await get_tracked_titles()
            logger.info(f"Found {len(titles)} tracked titles")
            
            for item in feed.entries:
                title = item.title
                link = item.link
                guid = item.guid
                
                for tracked in titles:
                    if tracked.lower() in title.lower():
                        logger.info(f"Match found! '{tracked}' in '{title}'")
                        
                        # Skip if already processed
                        if await is_processed(guid):
                            logger.info(f"Skipping already processed: {title}")
                            continue
                        
                        try:
                            # Convert to direct download link
                            torrent_id = link.split('/view/')[1].split('/')[0]
                            direct_link = f"https://nyaa.si/download/{torrent_id}.torrent"
                            
                            # Send to HuggingFace
                            result = await send_to_huggingface(title, direct_link)
                            
                            if result and result.get("status") == "ok":
                                # Store the latest processed result
                                _latest_processed = {
                                    "title": title,
                                    "file_id": result.get("file_id"),
                                    "message_id": result.get("message_id"),
                                    "torrent_id": torrent_id
                                }
                                
                                # Mark as processed with all info
                                await mark_processed(guid, _latest_processed)
                                
                                # Create and send share link to admins
                                share_result = await create_share_link(_latest_processed["message_id"])
                                if share_result["status"] == "ok":
                                    _latest_processed["share_link"] = share_result["link"]
                                    
                                    # Send notification to admins
                                    for admin in Bot.admins:
                                        try:
                                            await client.send_message(
                                                chat_id=admin,
                                                text=f"✅ New file processed: {title}\n\nShare Link: {share_result['link']}",
                                                reply_markup=share_result["reply_markup"]
                                            )
                                        except Exception as e:
                                            logger.error(f"Failed to notify admin {admin}: {str(e)}")
                                
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
            
        await asyncio.sleep(60)

async def start_rss_checker(client):
    """Start the RSS checker task"""
    global _rss_task, _latest_processed
    
    try:
        if _rss_task and not _rss_task.done():
            # If task is already running and we have latest processed info
            if _latest_processed:
                share_result = await create_share_link(_latest_processed["message_id"])
                if share_result["status"] == "ok":
                    return {
                        "status": "ok",
                        "file_id": _latest_processed["file_id"],
                        "message_id": _latest_processed["message_id"],
                        "share_link": share_result["link"],
                        "reply_markup": share_result["reply_markup"]
                    }
            
            # If no latest processed, return task info
            return {
                "status": "ok",
                "file_id": "ongoing_task",
                "message_id": int(datetime.now().timestamp()),
                "info": "Task already running"
            }
            
        _rss_task = asyncio.create_task(check_rss_feed(client))
        task_id = int(datetime.now().timestamp())
        _rss_task.set_name(f"rss_task_{task_id}")
        logger.info("RSS checker task started")
        
        # Return initial success result
        return {
            "status": "ok",
            "file_id": "new_task",
            "message_id": task_id,
            "info": "Task started successfully"
        }
        
    except Exception as e:
        logger.error(f"Error starting RSS checker: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

async def stop_rss_checker():
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
            return {"status": "ok", "message": "Task stopped successfully"}
            
    except Exception as e:
        logger.error(f"Error stopping RSS checker: {str(e)}")
        return {"status": "error", "error": str(e)}