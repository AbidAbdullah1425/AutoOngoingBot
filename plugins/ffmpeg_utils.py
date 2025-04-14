import os
import subprocess
import logging
from datetime import datetime
from .video_handler import user_data, logger
from .cleanup import cleanup
from .progress_handler import progress_bar, update_status
from config import DB_CHANNEL
from .link_generation import generate_link
from .channel_post import post_to_main_channel

async def merge_subtitles_task(client, message, user_id):
    data = user_data[user_id]
    video = data["video"]
    subtitle = data["subtitle"]
    new_name = data["new_name"]
    caption = data["caption"]
    output_file = f"{new_name}.mkv"

    font = 'Assist/Font/OathBold.otf'
    thumbnail = 'Assist/Images/thumbnail.jpg'

    try:
        # Create status message in PM
        status_msg = await message.reply("Initializing...")
        # Create status message in channel
        channel_msg = await client.send_message(DB_CHANNEL, "Initializing...")
        # Link the messages
        status_msg.channel_message = channel_msg
        
        start_time = datetime.now()

        # Download progress callback
        async def download_progress(current, total):
            try:
                await progress_bar(
                    current,
                    total,
                    status_msg,
                    start_time,
                    "Downloading Video",
                    message.from_user.username or f"User_{user_id}"
                )
            except Exception as e:
                logger.error(f"Download progress update failed: {str(e)}")

        # Update both PM and channel
        await update_status(status_msg, "📥 Starting video download...")
        
        # Handle video download progress
        if not os.path.exists(video):
            downloaded_file = await client.download_media(
                video,
                progress=download_progress
            )
            video = downloaded_file

        await update_status(status_msg, "🗑 Removing existing subtitles...")
        logger.info(f"Removing existing subtitles from video for user {user_id}")
        remove_subs_cmd = [
            "ffmpeg", "-i", video,
            "-map", "0:v", "-map", "0:a?",
            "-c", "copy", "-y", "removed_subtitles.mkv"
        ]
        subprocess.run(remove_subs_cmd, check=True)

        await update_status(status_msg, "🔄 Merging subtitles and fonts...")
        logger.info(f"Merging subtitles for user {user_id}: {output_file}")
        ffmpeg_cmd = [
            "ffmpeg", "-i", "removed_subtitles.mkv",
            "-i", subtitle,
            "-attach", font, "-metadata:s:t:0", "mimetype=application/x-font-otf",
            "-map", "0", "-map", "1",
            "-metadata:s:s:0", "title=HeavenlySubs",
            "-metadata:s:s:0", "language=eng", "-disposition:s:s:0", "default",
            "-c", "copy", output_file
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        await update_status(status_msg, "📤 Starting upload...")
        start_time = datetime.now()  # Reset start time for upload
        
        # Upload progress callback
        async def upload_progress(current, total):
            try:
                await progress_bar(
                    current,
                    total,
                    status_msg,
                    start_time,
                    "Uploading Video",
                    message.from_user.username or f"User_{user_id}"
                )
            except Exception as e:
                logger.error(f"Upload progress update failed: {str(e)}")

        # Send to user
        sent_message = await message.reply_document(
            document=output_file,
            caption=caption,
            thumb=thumbnail,
            progress=upload_progress
        )

        # Save to DB_CHANNEL and generate link
        try:
            # Save copy to DB_CHANNEL
            db_msg = await sent_message.copy(chat_id=DB_CHANNEL)
            logger.info(f"File saved to DB_CHANNEL: {output_file}")
            
            # Generate shareable link
            link, reply_markup = await generate_link(client, db_msg)
            if link:
                await message.reply_text(
                    f"<b>🔗 Shareable Link:</b>\n\n{link}",
                    reply_markup=reply_markup
                )                
                
                # Post to main channel
                await post_to_main_channel(client, new_name, link)
                            
        except Exception as e:
            logger.error(f"Failed to save to DB_CHANNEL or generate link: {e}")

        await update_status(status_msg, "✅ Process Complete!")

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to merge subtitles: {e}")
        await update_status(status_msg, f"❌ Error: {e}")
    finally:
        if os.path.exists("removed_subtitles.mkv"):
            os.remove("removed_subtitles.mkv")
        cleanup(user_id)