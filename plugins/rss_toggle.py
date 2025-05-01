# plugins/rss_toggle.py
from pyrogram import filters
from pyrogram.types import Message
from bot import Bot
from config import LOGGER
from datetime import datetime, timezone

# Initialize logger for this module
logger = LOGGER(__name__)

@Bot.on_message(filters.command("taskon"))
async def task_on(client, msg: Message):
    try:
        # Get current timestamp
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Log command receipt
        logger.info(f"[{current_time}] Received taskon command from user {msg.from_user.id}")
        
        # Check current state
        previous_state = "enabled" if client.feed_enabled else "disabled"
        logger.debug(f"[{current_time}] Previous RSS feed state was: {previous_state}")
        
        # Enable feed
        client.feed_enabled = True
        logger.info(f"[{current_time}] RSS AutoFeed enabled by user {msg.from_user.id}")
        
        # Send confirmation message
        try:
            await msg.reply("RSS AutoFeed: ✅ <b>Enabled</b>")
            logger.debug(f"[{current_time}] Sent confirmation message for enabling RSS AutoFeed")
        except Exception as reply_error:
            logger.error(f"[{current_time}] Failed to send confirmation message: {str(reply_error)}", exc_info=True)
            
        # Log state change details
        logger.info(f"[{current_time}] RSS AutoFeed state changed: {previous_state} -> enabled")
        
    except Exception as e:
        error_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.error(f"[{error_time}] Unexpected error in task_on handler: {str(e)}", exc_info=True)
        try:
            await msg.reply("❌ An error occurred while enabling RSS AutoFeed")
        except:
            logger.error(f"[{error_time}] Failed to send error message to user")

@Bot.on_message(filters.command("taskoff"))
async def task_off(client, msg: Message):
    try:
        # Get current timestamp
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Log command receipt
        logger.info(f"[{current_time}] Received taskoff command from user {msg.from_user.id}")
        
        # Check current state
        previous_state = "enabled" if client.feed_enabled else "disabled"
        logger.debug(f"[{current_time}] Previous RSS feed state was: {previous_state}")
        
        # Disable feed
        client.feed_enabled = False
        logger.info(f"[{current_time}] RSS AutoFeed disabled by user {msg.from_user.id}")
        
        # Send confirmation message
        try:
            await msg.reply("RSS AutoFeed: ❌ <b>Disabled</b>")
            logger.debug(f"[{current_time}] Sent confirmation message for disabling RSS AutoFeed")
        except Exception as reply_error:
            logger.error(f"[{current_time}] Failed to send confirmation message: {str(reply_error)}", exc_info=True)
            
        # Log state change details
        logger.info(f"[{current_time}] RSS AutoFeed state changed: {previous_state} -> disabled")
        
    except Exception as e:
        error_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.error(f"[{error_time}] Unexpected error in task_off handler: {str(e)}", exc_info=True)
        try:
            await msg.reply("❌ An error occurred while disabling RSS AutoFeed")
        except:
            logger.error(f"[{error_time}] Failed to send error message to user")