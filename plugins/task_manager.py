from plugins.db import get_tracked_titles, is_torrent_processed, mark_torrent_processed
from plugins.huggingface_uploader import send_to_huggingface
from plugins.anime_utils import AnimeInfo
from config import LOGGER, BOT_USERNAME, DB_CHANNEL_ID, OWNER_ID, HUGGINGFACE_URL
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import feedparser
import asyncio
import traceback
from datetime import datetime, timezone
from base64 import b64encode
import aiohttp
from bot import Bot

logger = LOGGER(__name__)

RSS_URL = "https://subsplease.org/rss/?t&r=720"
_rss_task = None

async def encode(string):
    return b64encode(string.encode()).decode()

async def create_share_link(message_id):
    """Create a shareable link from a message ID"""
    try:
        base64_string = await encode(f"get-{message_id * abs(DB_CHANNEL_ID)}")
        link = f"https://t.me/{BOT_USERNAME}?start={base64_string}"
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

async def check_space_status():
    """Check if HuggingFace Space is ready"""
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(HUGGINGFACE_URL) as response:
                return response.status == 200
    except:
        return False

async def check_rss_feed(client):
    while True:
        try:
            current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            logger.info(f"[{current_time}] Checking RSS feed")
            
            # Set up admin list
            if isinstance(OWNER_ID, list):
                admin_list = OWNER_ID
            else:
                admin_list = [OWNER_ID]

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
                
                try:
                    torrent_id = link.split('/view/')[1].split('/')[0]
                except IndexError:
                    logger.error(f"Could not extract torrent ID from {link}")
                    continue
                
                for tracked in titles:
                    if tracked.lower() in title.lower():
                        logger.info(f"Match found! '{tracked}' in '{title}'")
                        
                        if await is_torrent_processed(torrent_id):
                            logger.info(f"Skipping already processed torrent: {torrent_id} - {title}")
                            continue
                        
                        try:
                            # Check if Space is ready
                            if not await check_space_status():
                                logger.error("HuggingFace Space is not ready")
                                for admin in admin_list:
                                    await client.send_message(
                                        chat_id=admin,
                                        text="⚠️ HuggingFace Space is not ready. Waiting for next cycle."
                                    )
                                continue

                            direct_link = f"https://nyaa.si/download/{torrent_id}.torrent"
                            result = await send_to_huggingface(title, direct_link)
                            
                            if result and result.get("status") == "ok":
                                file_id = result.get("file_id")
                                message_id = result.get("message_id")
                                
                                if file_id and message_id:
                                    share_result = await create_share_link(message_id)
                                    
                                    if share_result["status"] == "ok":
                                        try:
                                            # Mark as processed first to avoid duplicates
                                            await mark_torrent_processed(
                                                torrent_id=torrent_id,
                                                title=title,
                                                file_id=file_id,
                                                message_id=message_id,
                                                share_link=share_result["link"]
                                            )

                                            # Get anime info
                                            anime_info = await AnimeInfo.extract_info_from_filename(title)
                                            if anime_info["success"]:
                                                anime_data = await AnimeInfo.get_anime_data(anime_info["anime_name"])
                                                if anime_data["success"]:
                                                    post_data = await AnimeInfo.format_post(
                                                        anime_data["data"],
                                                        anime_info["episode"],
                                                        share_result["link"]
                                                    )
                                                    
                                                    if post_data["success"]:
                                                        for admin in admin_list:
                                                            try:
                                                                await client.send_photo(
                                                                    chat_id=admin,
                                                                    photo=post_data["cover_url"],
                                                                    caption=post_data["text"],
                                                                    reply_markup=InlineKeyboardMarkup(post_data["buttons"])
                                                                )
                                                            except Exception as e:
                                                                logger.error(f"Failed to send formatted message: {str(e)}")
                                                                # Fallback to simple message
                                                                await client.send_message(
                                                                    chat_id=admin,
                                                                    text=f"✅ New file processed:\n\n"
                                                                         f"Title: {title}\n"
                                                                         f"Share Link: {share_result['link']}",
                                                                    reply_markup=share_result["reply_markup"]
                                                                )
                                                    else:
                                                        raise Exception("Failed to format post")
                                                else:
                                                    raise Exception("Failed to get anime data")
                                            else:
                                                raise Exception("Failed to extract anime info")
                                                
                                        except Exception as e:
                                            logger.error(f"Error in anime processing: {str(e)}")
                                            # Send simple notification on error
                                            for admin in admin_list:
                                                await client.send_message(
                                                    chat_id=admin,
                                                    text=f"✅ New file processed:\n\n"
                                                         f"Title: {title}\n"
                                                         f"Share Link: {share_result['link']}",
                                                    reply_markup=share_result["reply_markup"]
                                                )
                            elif result and result.get("status") == "error":
                                logger.error(f"HuggingFace error: {result.get('error')}")
                                for admin in admin_list:
                                    await client.send_message(
                                        chat_id=admin,
                                        text=f"❌ Failed to process file:\n\n"
                                             f"Title: {title}\n"
                                             f"Error: {result.get('error')}"
                                    )
                                    
                        except Exception as e:
                            logger.error(f"Error processing torrent {torrent_id}: {str(e)}")
                            logger.error(traceback.format_exc())
                        
                        await asyncio.sleep(1)
                        
        except Exception as e:
            logger.error(f"Error in RSS checker: {str(e)}")
            logger.error(traceback.format_exc())
            
        await asyncio.sleep(60)

async def start_rss_checker(client):
    """Start the RSS checker task"""
    global _rss_task
    
    try:
        if _rss_task and not _rss_task.done():
            return {
                "status": "ok",
                "message": "RSS checker task is already running"
            }
            
        _rss_task = asyncio.create_task(check_rss_feed(client))
        logger.info("RSS checker task started")
        
        return {
            "status": "ok",
            "message": "RSS checker task started successfully"
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