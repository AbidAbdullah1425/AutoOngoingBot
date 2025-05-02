import aiohttp
from config import LOGGER
from datetime import datetime, timezone

logger = LOGGER(__name__)

# Your HuggingFace space URL
HF_URL = "https://abidabdullah199-Compressor.hf.space"

async def send_to_huggingface(title: str, torrent_link: str, crf: int = 28, preset: str = "ultrafast"):
    """
    Send torrent to HuggingFace for processing
    Args:
        title: Title of the video
        torrent_link: Direct torrent download link
        crf: Compression factor (default: 28)
        preset: FFmpeg preset (default: ultrafast)
    """
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    try:
        # Create form data
        form_data = aiohttp.FormData()
        form_data.add_field("title", title)
        form_data.add_field("torrent_link", torrent_link)
        form_data.add_field("crf", str(crf))  # Convert to string as Form data
        form_data.add_field("preset", preset)
        
        # Log the request
        logger.info(f"[{current_time}] Sending request to HuggingFace")
        logger.info(f"[{current_time}] Title: {title}")
        logger.info(f"[{current_time}] Torrent: {torrent_link}")
        logger.info(f"[{current_time}] CRF: {crf}")
        logger.info(f"[{current_time}] Preset: {preset}")
        
        # Set timeout (30 minutes since video processing takes time)
        timeout = aiohttp.ClientTimeout(total=1800)  # 30 minutes
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(HF_URL, data=form_data) as response:
                # Log response status
                logger.info(f"[{current_time}] Response Status: {response.status}")
                
                try:
                    result = await response.json()
                    logger.info(f"[{current_time}] Response: {result}")
                    
                    if response.status == 200 and result.get("status") == "success":
                        return {
                            "status": "success",
                            "message": result.get("message", "Upload successful")
                        }
                    else:
                        error = result.get("reason") or result.get("error") or "Unknown error"
                        return {
                            "status": "failed",
                            "error": f"Upload failed: {error}"
                        }
                        
                except Exception as e:
                    return {
                        "status": "failed",
                        "error": f"Failed to parse response: {str(e)}"
                    }
                    
    except asyncio.TimeoutError:
        error_msg = "Request timed out after 30 minutes"
        logger.error(f"[{current_time}] {error_msg}")
        return {
            "status": "failed",
            "error": error_msg
        }
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(f"[{current_time}] {error_msg}")
        return {
            "status": "failed",
            "error": error_msg
        }