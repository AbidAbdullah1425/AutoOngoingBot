import aiohttp
from config import LOGGER
from datetime import datetime, timezone
import asyncio
import json

logger = LOGGER(__name__)

# FastAPI endpoint
HF_URL = "https://abidabdullah199-Compressor.hf.space/"

async def send_to_huggingface(title: str, torrent_link: str, crf: int = 28, preset: str = "ultrafast"):
    """
    Send torrent to HuggingFace for processing
    Args:
        title: Title of the video (required)
        torrent_link: Direct torrent download link
        crf: Compression factor (default: 28)
        preset: FFmpeg preset (default: ultrafast)
    """
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    try:
        logger.info(f"[{current_time}] Starting request to HuggingFace Space")
        logger.info(f"[{current_time}] Parameters:")
        logger.info(f"  - Title: {title}")
        logger.info(f"  - Torrent: {torrent_link}")
        logger.info(f"  - CRF: {crf}")
        logger.info(f"  - Preset: {preset}")

        # Create form data
        form = aiohttp.FormData()
        form.add_field("title", str(title))
        form.add_field("torrent_link", str(torrent_link))
        form.add_field("crf", str(crf))
        form.add_field("preset", str(preset))
        # Don't add magnet field if we're using torrent_link
        
        # Set proper headers for multipart form data
        headers = {
            "Accept": "application/json",
            "User-Agent": "AutoOngoingBot/1.0"
        }
        
        timeout = aiohttp.ClientTimeout(total=3600)  # 1 hour timeout
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                # Make POST request (since only POST is allowed)
                async with session.post(
                    HF_URL,
                    data=form,
                    headers=headers,
                    allow_redirects=True
                ) as response:
                    
                    response_text = await response.text()
                    logger.info(f"[{current_time}] Response Status: {response.status}")
                    logger.info(f"[{current_time}] Response Text: {response_text}")
                    
                    if response.status == 200:
                        return {
                            "status": "success",
                            "message": "Video processing started"
                        }
                    elif response.status == 405:
                        logger.error(f"[{current_time}] Method not allowed. Endpoint only accepts POST requests.")
                        return {
                            "status": "failed",
                            "reason": "API endpoint configuration error"
                        }
                    else:
                        # Try to parse response as JSON
                        try:
                            error_data = json.loads(response_text)
                            error_reason = error_data.get("reason") or error_data.get("detail") or "Unknown error"
                        except json.JSONDecodeError:
                            error_reason = response_text or "Unknown error"
                            
                        logger.error(f"[{current_time}] Error: {error_reason}")
                        return {
                            "status": "failed",
                            "reason": error_reason
                        }
                        
            except aiohttp.ClientError as e:
                logger.error(f"[{current_time}] Connection error: {str(e)}")
                return {
                    "status": "failed",
                    "reason": f"Connection error: {str(e)}"
                }
                    
    except asyncio.TimeoutError:
        logger.error(f"[{current_time}] Request timed out")
        return {
            "status": "failed",
            "reason": "Request timed out"
        }
        
    except Exception as e:
        logger.error(f"[{current_time}] Unexpected error: {str(e)}")
        import traceback
        logger.error(f"[{current_time}] Traceback: {traceback.format_exc()}")
        return {
            "status": "failed",
            "reason": f"Unexpected error: {str(e)}"
        }