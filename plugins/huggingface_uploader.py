from aiohttp import ClientSession, ClientTimeout
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import LOGGER, HUGGINGFACE_URL, LOG_CHANNEL
from datetime import datetime, timezone
import asyncio

logger = LOGGER(__name__)

# Set a longer timeout
TIMEOUT = ClientTimeout(total=600)  # 10 minutes timeout

async def send_to_huggingface(title: str, torrent_link: str, client=None):
    try:
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.info(f"[{current_time}] Starting request to HuggingFace Space")

        # Log parameters
        logger.info(f"[{current_time}] Parameters:")
        logger.info(f"  - Title: {title}")
        logger.info(f"  - Torrent: {torrent_link}")
        logger.info(f"  - CRF: 28")
        logger.info(f"  - Preset: ultrafast")

        # Form data - convert all values to strings to match curl behavior
        data = {
            "title": str(title),
            "torrent": str(torrent_link),
            "crf": "28",  # Convert to string
            "preset": "ultrafast"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"  # Add Accept header
        }

        # Ensure URL ends with a slash
        url = HUGGINGFACE_URL if HUGGINGFACE_URL.endswith('/') else f"{HUGGINGFACE_URL}/"

        async with ClientSession(timeout=TIMEOUT) as session:
            try:
                logger.info(f"Making request to {url}")
                async with session.post(
                    url,  # Use the URL with trailing slash
                    data=data,
                    headers=headers,
                    allow_redirects=True  # Allow redirects
                ) as response:
                    logger.info(f"[{current_time}] Response Status: {response.status}")

                    # Get response text first
                    text = await response.text()
                    logger.info(f"[{current_time}] Raw Response: {text}")

                    # Prepare error message for LOG_CHANNEL
                    error_message = (
                        f"🤖 HuggingFace Upload Report\n\n"
                        f"🎥 File: {title}\n"
                        f"⏰ Time: {current_time}\n"
                        f"📊 Status: {response.status}\n"
                    )

                    if response.status == 200:
                        try:
                            import json
                            result = json.loads(text)
                            logger.info(f"[{current_time}] Parsed Response: {result}")

                            if result.get("status") == "ok":
                                if client and LOG_CHANNEL:
                                    await client.send_message(
                                        LOG_CHANNEL,
                                        f"{error_message}✅ Success: File processed successfully"
                                    )
                                return result
                            else:
                                error_msg = result.get("error", "Unknown error")
                                if client and LOG_CHANNEL:
                                    await client.send_message(
                                        LOG_CHANNEL,
                                        f"{error_message}❌ API Error: {error_msg}"
                                    )
                                return {"status": "failed", "error": error_msg}
                        except json.JSONDecodeError as e:
                            error_msg = f"JSON Parse Error: {str(e)}, Response: {text[:500]}..."
                            if client and LOG_CHANNEL:
                                await client.send_message(
                                    LOG_CHANNEL,
                                    f"{error_message}❌ Error: {error_msg}"
                                )
                            return {"status": "failed", "error": error_msg}
                    else:
                        error_msg = f"HTTP {response.status}: {text[:500]}..."
                        if client and LOG_CHANNEL:
                            await client.send_message(
                                LOG_CHANNEL,
                                f"{error_message}❌ Error: {error_msg}"
                            )
                        return {"status": "failed", "error": error_msg}

            except asyncio.TimeoutError as e:
                error_msg = f"Request timeout: {str(e)}"
                if client and LOG_CHANNEL:
                    await client.send_message(
                        LOG_CHANNEL,
                        f"{error_message}⏱️ Timeout Error: {error_msg}"
                    )
                return {"status": "failed", "error": error_msg}
            except Exception as e:
                error_msg = f"Request error: {str(e)}"
                if client and LOG_CHANNEL:
                    await client.send_message(
                        LOG_CHANNEL,
                        f"{error_message}❌ Error: {error_msg}"
                    )
                return {"status": "failed", "error": error_msg}

    except Exception as e:
        error_msg = f"Error in send_to_huggingface: {str(e)}"
        logger.error(error_msg)
        if client and LOG_CHANNEL:
            await client.send_message(
                LOG_CHANNEL,
                f"❌ General Error\n\n"
                f"🎥 File: {title}\n"
                f"⏰ Time: {current_time}\n"
                f"❌ Error: {error_msg}"
            )
        return {"status": "failed", "error": error_msg}