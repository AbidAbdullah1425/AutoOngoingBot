from pyrogram import Client, filters
from plugins.task_manager import start_rss_checker, stop_rss_checker
from plugins.huggingface_uploader import send_to_huggingface
from bot import Bot
from config import LOGGER, BOT_USERNAME, DB_CHANNEL_ID, ADMINS


from datetime import datetime, timezone
from fastapi import FastAPI, Request
from base64 import b64encode

logger = LOGGER(__name__)
app = FastAPI()

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

        if result and result.get("status") == "ok":
            # Generate shareable link
            file_id = result.get("file_id")
            message_id = result.get("message_id")
            
            if file_id and message_id:
                # Generate base64 string using DB_CHANNEL_ID from config
                
                base64_string = await encode(f"get-{message_id * abs(DB_CHANNEL_ID)}")
                
                # Create shareable link using BOT_USERNAME from config
                
                link = f"https://t.me/{BOT_USERNAME}?start={base64_string}"
                
                # Create button markup
                reply_markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔁 Share URL", 
                        url=f'https://telegram.me/share/url?url={link}')
                ]])

                await message.reply_text(
                    f"✅ File processed successfully!\n\nShare Link: {link}",
                    reply_markup=reply_markup
                )
            else:
                await message.reply_text("❌ Failed to generate link: Missing file_id or message_id")
        else:
            error = result.get("error", "Unknown error") if result else "No response"
            await message.reply_text(f"❌ Failed to send torrent: {error}")

    except Exception as e:
        logger.error(f"Error in torrent command: {e}")
        await message.reply_text("❌ Failed to process torrent!")



# encode func
async def encode(string):
    return b64encode(string.encode()).decode()





@app.post("/process_file")
async def process_file(request: Request):
    try:
        data = await request.json()
        file_id = data.get("file_id")
        message_id = data.get("message_id")  # Get message_id from request

        if not file_id or not message_id:
            return {"error": "Missing file_id or message_id"}

        try:
            # Generate base64 string using the actual message_id
            base64_string = await encode(f"get-{message_id * abs(Bot.db_channel.id)}")
            
            # Create shareable link
            link = f"https://t.me/{BOT_USERNAME}?start={base64_string}"

            # Create button markup
            reply_markup = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔁 Share URL", 
                    url=f'https://telegram.me/share/url?url={link}')
            ]])

            # Send to admin
            
            for admin in ADMINS:
                try:
                    await Bot.send_message(
                        chat_id=admin,
                        text=f"<b>Here is your link</b>\n\n{link}",
                        reply_markup=reply_markup
                    )
                except Exception as e:
                    continue

            return {"status": "success", "link": link}

        except Exception as e:
            return {"error": str(e)}

    except Exception as e:
        return {"error": str(e)}