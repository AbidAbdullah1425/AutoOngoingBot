from aiohttp import ClientSession, ClientTimeout
from config import LOGGER, HUGGINGFACE_URL, LOG_CHANNEL
from datetime import datetime, timezone
import json
import asyncio

logger = LOGGER(__name__)

TIMEOUT = ClientTimeout(total=600)  # 10 minutes timeout
MAX_RETRIES = 10  # Maximum number of retries
RETRY_DELAY = 30  # Delay between retries in seconds

async def check_processing_status(session, url, title):
    """Check processing status of the file"""
    async with session.get(url) as response:
        if response.status == 200:
            return await response.json()
        return None

async def send_to_huggingface(title: str, torrent_link: str, client=None):
    """Send file to HuggingFace for processing"""
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    try:
        logger.info(f"[{current_time}] Starting HuggingFace request")

        data = {
            "title": str(title),
            "torrent": str(torrent_link),
            "crf": "28",
            "preset": "ultrafast"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        async with ClientSession(timeout=TIMEOUT) as session:
            # Initial upload request
            async with session.post(
                HUGGINGFACE_URL,
                data=data,
                headers=headers,
                allow_redirects=True
            ) as response:
                initial_status = response.status
                logger.info(f"[{current_time}] Initial Status: {initial_status}")

                if initial_status == 206:
                    # File is processing, start polling
                    progress_msg = (
                        f"🤖 <b>HuggingFace Processing Status</b>\n\n"
                        f"🎥 <b>File:</b> {title}\n"
                        f"⏰ <b>Time:</b> {current_time}\n"
                        f"⏳ <b>Status:</b> Processing Started\n"
                        f"📝 <b>Note:</b> This may take several minutes..."
                    )
                    if client and LOG_CHANNEL:
                        status_message = await client.send_message(
                            LOG_CHANNEL, 
                            progress_msg, 
                            parse_mode="html"
                        )

                    # Poll for completion
                    for retry in range(MAX_RETRIES):
                        await asyncio.sleep(RETRY_DELAY)
                        
                        async with session.get(HUGGINGFACE_URL) as check_response:
                            if check_response.status == 200:
                                try:
                                    result = await check_response.json()
                                    if result.get("status") == "ok":
                                        success_msg = (
                                            f"🤖 <b>HuggingFace Upload Success</b>\n\n"
                                            f"🎥 <b>File:</b> {title}\n"
                                            f"⏰ <b>Time:</b> {current_time}\n"
                                            f"✅ <b>Status:</b> Completed"
                                        )
                                        if client and LOG_CHANNEL:
                                            await status_message.edit(
                                                success_msg, 
                                                parse_mode="html"
                                            )
                                        return result
                                except:
                                    continue

                            # Update progress message
                            progress_msg = (
                                f"🤖 <b>HuggingFace Processing Status</b>\n\n"
                                f"🎥 <b>File:</b> {title}\n"
                                f"⏰ <b>Time:</b> {current_time}\n"
                                f"⏳ <b>Status:</b> Still Processing\n"
                                f"🔄 <b>Attempt:</b> {retry + 1}/{MAX_RETRIES}"
                            )
                            if client and LOG_CHANNEL:
                                await status_message.edit(
                                    progress_msg, 
                                    parse_mode="html"
                                )

                    # If we reach here, process timed out
                    timeout_msg = (
                        f"🤖 <b>HuggingFace Processing Timeout</b>\n\n"
                        f"🎥 <b>File:</b> {title}\n"
                        f"⏰ <b>Time:</b> {current_time}\n"
                        f"❌ <b>Status:</b> Timeout\n"
                        f"📝 <b>Note:</b> Process took too long"
                    )
                    if client and LOG_CHANNEL:
                        await status_message.edit(timeout_msg, parse_mode="html")
                    return {"status": "failed", "error": "Processing timeout"}

                elif initial_status == 200:
                    # Immediate success
                    try:
                        result = await response.json()
                        if result.get("status") == "ok":
                            success_msg = (
                                f"🤖 <b>HuggingFace Upload Success</b>\n\n"
                                f"🎥 <b>File:</b> {title}\n"
                                f"⏰ <b>Time:</b> {current_time}\n"
                                f"✅ <b>Status:</b> Success"
                            )
                            if client and LOG_CHANNEL:
                                await client.send_message(
                                    LOG_CHANNEL, 
                                    success_msg, 
                                    parse_mode="html"
                                )
                            return result
                    except:
                        pass

                # Handle other status codes as errors
                error_msg = (
                    f"🤖 <b>HuggingFace Upload Error</b>\n\n"
                    f"🎥 <b>File:</b> {title}\n"
                    f"⏰ <b>Time:</b> {current_time}\n"
                    f"❌ <b>Status:</b> {initial_status}"
                )
                if client and LOG_CHANNEL:
                    await client.send_message(LOG_CHANNEL, error_msg, parse_mode="html")
                return {"status": "failed", "error": f"HTTP {initial_status}"}

    except Exception as e:
        error_msg = (
            f"🤖 <b>HuggingFace Upload Error</b>\n\n"
            f"🎥 <b>File:</b> {title}\n"
            f"⏰ <b>Time:</b> {current_time}\n"
            f"❌ <b>Error:</b> {str(e)}"
        )
        logger.error(f"Error in send_to_huggingface: {str(e)}")
        if client and LOG_CHANNEL:
            await client.send_message(LOG_CHANNEL, error_msg, parse_mode="html")
        return {"status": "failed", "error": str(e)}