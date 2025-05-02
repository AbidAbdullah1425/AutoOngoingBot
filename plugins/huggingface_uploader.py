import aiohttp
from config import LOGGER
from datetime import datetime, timezone
import asyncio

logger = LOGGER(__name__)

# Your HuggingFace space URL
HF_URL = "https://abidabdullah199-Compressor.hf.space/"  # Added trailing slash

async def send_to_huggingface(title: str, torrent_link: str, crf: int = 28, preset: str = "ultrafast"):
    """
    Send torrent to HuggingFace for processing
    Args:
        title: Title of the video
        torrent_link: Direct torrent download link (must be direct .torrent file link)
        crf: Compression factor (default: 28)
        preset: FFmpeg preset (default: ultrafast)
    """
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    try:
        # Create form data exactly matching FastAPI endpoint
        form_data = aiohttp.FormData()
        form_data.add_field("title", str(title))
        form_data.add_field("torrent_link", str(torrent_link))
        form_data.add_field("crf", str(crf))
        form_data.add_field("preset", str(preset))
        # Note: magnet field is None by default, matching FastAPI's Optional parameter
        
        # Log the request
        logger.info(f"[{current_time}] Sending request to HuggingFace Space")
        logger.info(f"[{current_time}] Title: {title}")
        logger.info(f"[{current_time}] Torrent: {torrent_link}")
        logger.info(f"[{current_time}] CRF: {crf}")
        logger.info(f"[{current_time}] Preset: {preset}")
        
        # Long timeout for video processing
        timeout = aiohttp.ClientTimeout(total=3600)  # 1 hour timeout
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(HF_URL, data=form_data) as response:
                response_text = await response.text()
                logger.info(f"[{current_time}] Response Status: {response.status}")
                logger.info(f"[{current_time}] Response Text: {response_text}")
                
                try:
                    # Handle response based on your FastAPI app's response format
                    if response.status == 200:
                        return {
                            "status": "success",
                            "message": "Uploaded and cleaned up."
                        }
                    else:
                        # Parse error messages that match your FastAPI app's error responses
                        if "aria2c failed" in response_text:
                            return {"status": "failed", "error": "Download failed"}
                        elif "ffmpeg failed" in response_text:
                            return {"status": "failed", "error": "Compression failed"}
                        elif "No video file found" in response_text:
                            return {"status": "failed", "error": "No video file found"}
                        elif "No torrent or magnet link provided" in response_text:
                            return {"status": "failed", "error": "Invalid torrent link"}
                        else:
                            return {"status": "failed", "error": response_text}
                            
                except Exception as e:
                    logger.error(f"[{current_time}] Error parsing response: {str(e)}")
                    return {
                        "status": "failed",
                        "error": f"Failed to process response: {str(e)}"
                    }
                    
    except asyncio.TimeoutError:
        error_msg = "Request timed out after 1 hour"
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