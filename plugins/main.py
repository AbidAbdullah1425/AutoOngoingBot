from pyrogram import Client, filters
from plugins.task_manager import start_rss_checker, stop_rss_checker
from plugins.huggingface_uploader import send_to_huggingface
from bot import Bot
from config import LOGGER
from datetime import datetime, timezone

logger = LOGGER(__name__)

# Command to start RSS checking task
@Bot.on_message(filters.command("taskon") & filters.private)
async def start_task(client, message):
    try:
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        user_id = message.from_user.id
        
        logger.info(f"[{current_time}] Received taskon command from user {user_id}")
        
        await start_rss_checker(client)
        await message.reply_text("✅ RSS Checker task started successfully!")
        
    except Exception as e:
        logger.error(f"Error in taskon command: {str(e)}")
        await message.reply_text("❌ Failed to start RSS checker task!")

# Command to stop RSS checking task
@Bot.on_message(filters.command("taskoff") & filters.private)
async def stop_task(client, message):
    try:
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        user_id = message.from_user.id
        
        logger.info(f"[{current_time}] Received taskoff command from user {user_id}")
        
        await stop_rss_checker(client)
        await message.reply_text("✅ RSS Checker task stopped successfully!")
        
    except Exception as e:
        logger.error(f"Error in taskoff command: {str(e)}")
        await message.reply_text("❌ Failed to stop RSS checker task!")

# Command to directly send torrent to HuggingFace
@Bot.on_message(filters.command("torrent") & filters.private)
async def process_torrent(client, message):
    try:
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        user_id = message.from_user.id
        
        # Check if torrent link is provided
        if len(message.command) != 2:
            await message.reply_text("❌ Please provide a torrent link!\nUsage: /torrent <link>")
            return
            
        torrent_link = message.command[1]
        logger.info(f"[{current_time}] Processing torrent link from user {user_id}: {torrent_link}")
        
        # Extract title from link or use generic title
        try:
            title = torrent_link.split('/')[-1]
        except:
            title = f"manual_torrent_{current_time}"
            
        # Send to HuggingFace
        result = await send_to_huggingface(title, torrent_link)
        
        if result and result.get("status") == "success":
            await message.reply_text(f"✅ Successfully sent torrent to HuggingFace!")
        else:
            error = result.get("error", "Unknown error") if result else "No response"
            await message.reply_text(f"❌ Failed to send torrent: {error}")
            
    except Exception as e:
        logger.error(f"Error in torrent command: {str(e)}")
        await message.reply_text("❌ Failed to process torrent!")