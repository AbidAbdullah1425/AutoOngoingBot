import os
from datetime import datetime
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import CHANNEL_ID, MAIN_CHANNEL, THUMBNAIL
from .shared_data import logger
from .link_generation import generate_link
from .progress import Progress

class UploadHandler:
    def __init__(self, client, user_id, status_msg, channel_msg, post_data):
        self.client = client
        self.user_id = user_id
        self.status_msg = status_msg
        self.channel_msg = channel_msg
        self.post_data = post_data.get(str(user_id), {}).get('data', {}) if isinstance(post_data, dict) else {}
        self.progress = Progress(client, status_msg, channel_msg, action="📤 Uploading to channel...")

    async def upload_file(self, file_path):
        if not os.path.exists(file_path):
            await self.status_msg.edit("❌ File not found!")
            return None

        try:
            # Upload with progress
            uploaded = await self.client.send_document(
                CHANNEL_ID,
                file_path,
                force_document=True,
                progress=self.progress.update_progress
            )

            if not uploaded:
                raise Exception("Upload failed: No response from Telegram")

            # Generate shareable link
            share_link = await generate_link(uploaded)
            if not share_link:
                raise Exception("Failed to generate share link")

            # Create post text
            post_text = self._create_formatted_post()
            
            # Create button for download
            keyboard = [[InlineKeyboardButton("📥 Download", url=share_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send to main channel
            try:
                cover_url = self.post_data.get('cover_url')
                
                if cover_url and isinstance(cover_url, str) and cover_url.startswith('http'):
                    await self.client.send_photo(
                        MAIN_CHANNEL,
                        photo=cover_url,
                        caption=post_text,
                        reply_markup=reply_markup
                    )
                else:
                    await self.client.send_message(
                        MAIN_CHANNEL,
                        post_text,
                        disable_web_page_preview=True,
                        reply_markup=reply_markup
                    )

                # Clean up
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Failed to remove file: {e}")

                await self.status_msg.edit("✅ Upload complete!")
                if self.channel_msg:
                    await self.channel_msg.delete()

                return uploaded.id

            except Exception as e:
                logger.error(f"Failed to send post: {e}")
                raise

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Upload failed: {error_msg}")
            await self.status_msg.edit(f"❌ Upload failed: {error_msg}")
            if self.channel_msg:
                await self.channel_msg.delete()
            return None

    def _create_formatted_post(self):
        """Creates the exact post format required"""
        try:
            # Get all required fields
            title = self.post_data.get('title', '')
            rating = self.post_data.get('rating', '')
            episode = self.post_data.get('episode', '')
            genres = self.post_data.get('genres', '')
            description = self.post_data.get('description', '')

            # Create post parts
            post_parts = []
            
            # Title with the exact format
            post_parts.append(f"☗   {title}\n")
            
            # Add other fields only if they exist
            if rating:
                post_parts.append(f"⦿   Ratings: {rating}")
            if episode:
                post_parts.append(f"⦿   Episode: {episode}")
            if genres:
                post_parts.append(f"⦿   Genres: {genres}")
            
            # Add synopsis with spacing
            if description:
                post_parts.append("")  # Empty line before synopsis
                post_parts.append(f"◆   Synopsis: {description}")

            return "\n".join(post_parts)

        except Exception as e:
            logger.error(f"Error in post creation: {e}")
            return f"☗   {self.post_data.get('title', '')}"