import os
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from bot import Bot
from config import OWNER_ID, MAIN_CHANNEL
from datetime import datetime
from .shared_data import logger
from .post_handler import PostHandler
from .upload_handler import UploadHandler
from .progress import Progress
from .aria2_client import aria2

# Initialize handlers
post_handler = PostHandler()

class VideoHandler:
    def __init__(self):
        logger.info("VideoHandler initialized")
        self.thumbnail_path = "Assist/Images/thumbnail.jpg"
        
    async def _handle_ddl(self, client, message, ddl_url=None):
        """Handle DDL command and process downloads"""
        try:
            # Get URL from message or parameter
            if isinstance(message, Message):
                if len(message.command) < 2 and not ddl_url:
                    return await message.reply("Please provide a direct download link!\nUsage: /ddl <url>")
                url = ddl_url or message.command[1]
                reply_to = message
            else:
                url = ddl_url
                reply_to = message
            
            # Create initial status messages
            status_msg = await reply_to.reply("📥 Starting Download...")
            channel_msg = await client.send_message(
                MAIN_CHANNEL,
                "Status: Starting download..."
            )

            # Create progress tracker
            progress = Progress(client, status_msg, channel_msg, "📥 Downloading...")

            try:
                # Add download to aria2
                download = aria2.add_uris([url])
                file_path = None

                while not download.is_complete:
                    download.update()
                    current = download.completed_length
                    total = download.total_length
                    
                    await progress.update_progress(current, total)
                    await asyncio.sleep(1)

                if download.is_complete:
                    file_path = download.files[0].path
                    
                if file_path and os.path.exists(file_path):
                    # Get user's post data
                    user_id = reply_to.from_user.id
                    post_data = post_handler.get_post_data(user_id)
                    
                    # Create upload handler and process upload
                    upload_handler = UploadHandler(
                        client, 
                        user_id, 
                        status_msg, 
                        channel_msg,
                        post_data
                    )
                    
                    # Upload file with thumbnail
                    msg_id = await upload_handler.upload_file(
                        file_path,
                        thumb=self.thumbnail_path
                    )
                    
                    if msg_id:
                        # Generate shareable link
                        from .link_generation import generate_link
                        share_link = await generate_link(client, MAIN_CHANNEL, msg_id)
                        
                        if share_link:
                            # Send success message to user
                            await status_msg.edit(f"✅ Upload Complete!\n\n🔗 Share Link: {share_link}")
                            
                            # Create post in main channel with cover image and button
                            if post_data.get('cover_url'):
                                # Create button with share link
                                keyboard = [[InlineKeyboardButton("🎥 Watch Now", url=share_link)]]
                                reply_markup = InlineKeyboardMarkup(keyboard)
                                
                                # Send post with cover image
                                await client.send_photo(
                                    chat_id=MAIN_CHANNEL,
                                    photo=post_data['cover_url'],
                                    caption=post_handler.format_post(post_data),
                                    reply_markup=reply_markup
                                )
                            else:
                                # Send post without cover image
                                keyboard = [[InlineKeyboardButton("🎥 Watch Now", url=share_link)]]
                                reply_markup = InlineKeyboardMarkup(keyboard)
                                await client.send_message(
                                    chat_id=MAIN_CHANNEL,
                                    text=post_handler.format_post(post_data),
                                    reply_markup=reply_markup
                                )
                    
                    # Clear post data after successful upload
                    post_handler.clear_post_data(user_id)
                    
                    # Clean up downloaded file
                    try:
                        os.remove(file_path)
                    except:
                        pass
                        
                else:
                    await status_msg.edit("❌ Download failed!")
                    await channel_msg.delete()

            except Exception as e:
                error_msg = str(e)
                if "not found" in error_msg.lower():
                    error_msg = "File not found. Please check the URL and try again."
                elif "access denied" in error_msg.lower():
                    error_msg = "Access denied. Please check if the link is accessible."
                    
                logger.error(f"Download failed: {e}")
                await status_msg.edit(f"❌ Download failed: {error_msg}")
                await channel_msg.delete()

        except Exception as e:
            logger.error(f"DDL processing failed: {e}")
            await reply_to.reply(f"❌ Error: {str(e)}")
            if 'channel_msg' in locals():
                await channel_msg.delete()

# Create handler instance
video_handler = VideoHandler()

# Command handlers
@Bot.on_message(filters.command('ddl') & filters.user(OWNER_ID))
async def handle_ddl(client, message):
    await video_handler._handle_ddl(client, message)

@Bot.on_message(filters.command('post') & filters.user(OWNER_ID))
async def handle_post(client, message):
    await post_handler.handle_post_command(client, message)

@Bot.on_callback_query()
async def handle_callbacks(client, callback_query):
    try:
        if callback_query.data == "create_post":
            success, ddl_url = await post_handler.handle_callback(client, callback_query)
            if success and ddl_url:
                await video_handler._handle_ddl(client, callback_query.message, ddl_url)
        else:
            await post_handler.handle_callback(client, callback_query)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback_query.answer("An error occurred", show_alert=True)

@Bot.on_message(filters.private & filters.user(OWNER_ID))
async def handle_post_input(client, message):
    await post_handler.handle_input(client, message)