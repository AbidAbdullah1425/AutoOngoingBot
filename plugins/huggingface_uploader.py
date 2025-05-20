from aiohttp import ClientSession, ClientTimeout
from config import LOGGER, HUGGINGFACE_URL, LOG_CHANNEL
from datetime import datetime, timezone
from pyrogram.enums import ParseMode
import json

logger = LOGGER(__name__)

TIMEOUT = ClientTimeout(total=600)  # 10 minutes timeout

async def get_response_text(response):
    """Get response text safely"""
    try:
        return await response.text()
    except:
        return ""

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
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        async with ClientSession(timeout=TIMEOUT) as session:
            async with session.post(
                HUGGINGFACE_URL,
                data=data,
                headers=headers,
                allow_redirects=True
            ) as response:
                status = response.status
                logger.info(f"[{current_time}] Status: {status}")
                
                # Get response text
                response_text = await get_response_text(response)
                
                # Try to parse JSON response
                try:
                    json_response = json.loads(response_text)
                    if json_response.get("status") == "ok":
                        return {"status": "ok", "data": json_response}
                except:
                    json_response = {}

                if status != 200:
                    # For 206 status, include response text in error
                    error_details = ""
                    if status == 206:
                        try:
                            # Try to get meaningful error from response
                            if response_text:
                                error_details = f"\n💡 Details: {response_text[:200]}"
                        except:
                            pass

                    error_report = (
                        "🤖 <b>HuggingFace Upload Report</b>\n\n"
                        f"🎥 <b>File:</b> {title}\n"
                        f"⏰ <b>Time:</b> {current_time}\n"
                        f"📊 <b>Status:</b> {status}\n"
                        f"❌ <b>Error:</b> HTTP {status}{error_details}"
                    )
                    if client and LOG_CHANNEL:
                        await client.send_message(
                            LOG_CHANNEL,
                            error_report,
                            parse_mode=ParseMode.HTML
                        )
                    return {
                        "status": "failed", 
                        "error": f"HTTP {status}",
                        "details": response_text
                    }

                # If we get here with a 200 status but no valid JSON
                if status == 200 and not json_response:
                    error_report = (
                        "🤖 <b>HuggingFace Upload Report</b>\n\n"
                        f"🎥 <b>File:</b> {title}\n"
                        f"⏰ <b>Time:</b> {current_time}\n"
                        f"📊 <b>Status:</b> {status}\n"
                        f"❌ <b>Error:</b> Invalid Response Format"
                    )
                    if client and LOG_CHANNEL:
                        await client.send_message(
                            LOG_CHANNEL,
                            error_report,
                            parse_mode=ParseMode.HTML
                        )
                    return {"status": "failed", "error": "Invalid response format"}

                return {"status": "ok"}

    except Exception as e:
        error_report = (
            "🤖 <b>HuggingFace Upload Report</b>\n\n"
            f"🎥 <b>File:</b> {title}\n"
            f"⏰ <b>Time:</b> {current_time}\n"
            f"❌ <b>Error:</b> {str(e)}"
        )
        logger.error(f"Error in send_to_huggingface: {str(e)}")
        if client and LOG_CHANNEL:
            await client.send_message(
                LOG_CHANNEL,
                error_report,
                parse_mode=ParseMode.HTML
            )
        return {"status": "failed", "error": str(e)}