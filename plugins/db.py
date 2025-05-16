from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URL, DB_NAME, LOGGER
from datetime import datetime, timezone

# Initialize logger for this module
logger = LOGGER(__name__)

# Log database connection attempt
try:
    client = AsyncIOMotorClient(DB_URL)
    db = client[DB_NAME]
    logger.info(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Successfully connected to database: {DB_NAME}")
except Exception as e:
    logger.critical(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Failed to connect to database: {str(e)}", exc_info=True)
    raise

@Bot.on_message(filters.command("addtask") & filters.private & filters.user(OWNER_ID))
async def add_task_command(client, message):
    try:
        # Check if title is provided
        if len(message.command) < 2:
            await message.reply_text(
                "❌ Please provide a title to track!\n\n"
                "Usage: /addtask <title>"
            )
            return

        # Get the title from command (combine all words after command)
        title = " ".join(message.command[1:])
        
        # Add task to database
        result = await add_task(title)
        
        if result:
            await message.reply_text(f"✅ Successfully added task to track: `{title}`")
        else:
            await message.reply_text(f"❌ Failed to add task: `{title}`")

    except Exception as e:
        logger.error(f"Error in addtask command: {str(e)}")
        await message.reply_text("❌ Failed to add task! Something went wrong.")

@Bot.on_message(filters.command("deltask") & filters.private & filters.user(OWNER_ID))
async def remove_task_command(client, message):
    try:
        # Check if title is provided
        if len(message.command) < 2:
            await message.reply_text(
                "❌ Please provide a title to remove!\n\n"
                "Usage: /deltask <title>"
            )
            return

        # Get the title from command (combine all words after command)
        title = " ".join(message.command[1:])
        
        # Remove task from database
        result = await remove_task(title)
        
        if result:
            await message.reply_text(f"✅ Successfully removed task: `{title}`")
        else:
            await message.reply_text(f"❌ Task not found: `{title}`")

    except Exception as e:
        logger.error(f"Error in deltask command: {str(e)}")
        await message.reply_text("❌ Failed to remove task! Something went wrong.")

@Bot.on_message(filters.command("listtask") & filters.private & filters.user(OWNER_ID))
async def list_tasks_command(client, message):
    try:
        # Get all tracked titles
        titles = await get_tracked_titles()
        
        if titles:
            # Create a formatted list of titles
            title_list = "\n".join([f"• `{title}`" for title in titles])
            await message.reply_text(
                f"📝 Currently tracking {len(titles)} titles:\n\n"
                f"{title_list}"
            )
        else:
            await message.reply_text("📝 No titles are currently being tracked.")

    except Exception as e:
        logger.error(f"Error in listtask command: {str(e)}")
        await message.reply_text("❌ Failed to list tasks! Something went wrong.")

async def add_task(title):
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        logger.info(f"[{current_time}] Attempting to add/update task: '{title}'")
        result = await db.tasks.update_one(
            {"title": title},
            {"$set": {"title": title}},
            upsert=True
        )
        
        if result.modified_count > 0:
            logger.info(f"[{current_time}] Updated existing task: '{title}'")
        elif result.upserted_id:
            logger.info(f"[{current_time}] Added new task: '{title}'")
        
        logger.debug(f"[{current_time}] Operation result - Modified: {result.modified_count}, Upserted: {result.upserted_id}")
        return True
        
    except Exception as e:
        logger.error(f"[{current_time}] Error adding task '{title}': {str(e)}", exc_info=True)
        raise

async def remove_task(title):
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        logger.info(f"[{current_time}] Attempting to remove task: '{title}'")
        result = await db.tasks.delete_one({"title": title})
        
        if result.deleted_count > 0:
            logger.info(f"[{current_time}] Successfully removed task: '{title}'")
        else:
            logger.warning(f"[{current_time}] No task found to remove with title: '{title}'")
            
        logger.debug(f"[{current_time}] Delete operation result - Deleted count: {result.deleted_count}")
        return result.deleted_count > 0
        
    except Exception as e:
        logger.error(f"[{current_time}] Error removing task '{title}': {str(e)}", exc_info=True)
        raise

async def get_tracked_titles():
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        logger.info(f"[{current_time}] Fetching all tracked titles")
        titles = [doc["title"] async for doc in db.tasks.find()]
        
        logger.info(f"[{current_time}] Retrieved {len(titles)} tracked titles")
        logger.debug(f"[{current_time}] Retrieved titles: {titles}")
        
        return titles
        
    except Exception as e:
        logger.error(f"[{current_time}] Error fetching tracked titles: {str(e)}", exc_info=True)
        raise

async def is_processed(hash):
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        logger.debug(f"[{current_time}] Checking if hash is processed: {hash}")
        result = await db.processed.find_one({"hash": hash})
        
        is_found = result is not None
        logger.debug(f"[{current_time}] Hash '{hash}' processed status: {is_found}")
        
        return is_found
        
    except Exception as e:
        logger.error(f"[{current_time}] Error checking processed status for hash '{hash}': {str(e)}", exc_info=True)
        raise

async def mark_processed(hash):
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        logger.info(f"[{current_time}] Marking hash as processed: {hash}")
        result = await db.processed.insert_one({"hash": hash})
        
        logger.debug(f"[{current_time}] Successfully marked hash as processed: {hash}, ID: {result.inserted_id}")
        return result.inserted_id
        
    except Exception as e:
        logger.error(f"[{current_time}] Error marking hash '{hash}' as processed: {str(e)}", exc_info=True)
        raise


