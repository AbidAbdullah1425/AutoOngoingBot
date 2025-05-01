from pyrogram import filters
from pyrogram.types import Message
from bot import Bot
from plugins.db import add_task, remove_task
from config import LOGGER
from datetime import datetime, timezone

# Initialize logger for this module
logger = LOGGER(__name__)

@Bot.on_message(filters.command("addtask"))
async def add(bot, msg: Message):
    try:
        # Get current timestamp
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Log command receipt
        logger.info(f"[{current_time}] Received addtask command from user {msg.from_user.id}")
        
        # Check if command has arguments
        if len(msg.command) < 2:
            logger.warning(f"[{current_time}] User {msg.from_user.id} sent addtask command without title")
            await msg.reply("⚠️ Please provide a title to add!")
            return
            
        title = " ".join(msg.command[1:])
        logger.info(f"[{current_time}] Adding new task: '{title}'")
        
        # Attempt to add task to database
        try:
            await add_task(title)
            logger.info(f"[{current_time}] Successfully added task: '{title}' to database")
            
            # Send confirmation message
            await msg.reply(f"✅ Added: `{title}`")
            logger.debug(f"[{current_time}] Sent confirmation message for adding '{title}'")
            
        except Exception as db_error:
            logger.error(f"[{current_time}] Database error while adding task '{title}': {str(db_error)}", exc_info=True)
            await msg.reply("❌ Failed to add task due to database error")
            
    except Exception as e:
        logger.error(f"[{current_time}] Unexpected error in add_task handler: {str(e)}", exc_info=True)
        await msg.reply("❌ An unexpected error occurred")

@Bot.on_message(filters.command("deltask"))
async def delete(bot, msg: Message):
    try:
        # Get current timestamp
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Log command receipt
        logger.info(f"[{current_time}] Received deltask command from user {msg.from_user.id}")
        
        # Check if command has arguments
        if len(msg.command) < 2:
            logger.warning(f"[{current_time}] User {msg.from_user.id} sent deltask command without title")
            await msg.reply("⚠️ Please provide a title to remove!")
            return
            
        title = " ".join(msg.command[1:])
        logger.info(f"[{current_time}] Removing task: '{title}'")
        
        # Attempt to remove task from database
        try:
            await remove_task(title)
            logger.info(f"[{current_time}] Successfully removed task: '{title}' from database")
            
            # Send confirmation message
            await msg.reply(f"❌ Removed: `{title}`")
            logger.debug(f"[{current_time}] Sent confirmation message for removing '{title}'")
            
        except Exception as db_error:
            logger.error(f"[{current_time}] Database error while removing task '{title}': {str(db_error)}", exc_info=True)
            await msg.reply("❌ Failed to remove task due to database error")
            
    except Exception as e:
        logger.error(f"[{current_time}] Unexpected error in delete_task handler: {str(e)}", exc_info=True)
        await msg.reply("❌ An unexpected error occurred")