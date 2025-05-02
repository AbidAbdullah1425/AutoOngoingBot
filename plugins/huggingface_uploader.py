import aiohttp
from config import LOGGER
from datetime import datetime, timezone
import asyncio

logger = LOGGER(__name__)

# FastAPI endpoint
HF_URL = "https://abidabdullah199-Compressor.hf.space/"  # Note the capital C in Compressor

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
        # Create form data exactly matching your FastAPI parameters
        form = aiohttp.FormData()
        form.add_field("title", str(title))  # Required field
        form.add_field("crf", str(crf))      # Optional with default 28
        form.add_field("preset", str(preset)) # Optional with default "ultrafast"
        form.add_field("torrent_link", str(torrent_link))  # Optional
        form.add_field("magnet", "")         # Optional, empty since we're using torrent_link
        
        # Log the request
        logger.info(f"[{current_time}] Sending request to HuggingFace Space")
        logger.info(f"[{current_time}] Title: {title}")
        logger.info(f"[{current_time}] Torrent: {torrent_link}")
        logger.info(f"[{current_time}] CRF: {crf}")
        logger.info(f"[{current_time}] Preset: {preset}")
        
        # Long timeout for video processing
        timeout = aiohttp.ClientTimeout(total=3600)  # 1 hour timeout
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(HF_URL, data=form) as response:
                response_text = await response.text()
                logger.info(f"[{current_time}] Response Status: {response.status}")
                logger.info(f"[{current_time}] Response Text: {response_text}")
                
                try:
                    # Match exact response format from your FastAPI app
                    if response.status == 200:
                        return {
                            "status": "success",
                            "message": "Uploaded and cleaned up."
                        }
                    else:
                        # Match your FastAPI error responses exactly
                        if response_text.find("No torrent or magnet link provided") != -1:
                            return {
                                "status": "failed",
                                "reason": "No torrent or magnet link provided"
                            }
                        elif response_text.find("aria2c failed") != -1:
                            return {
                                "status": "aria2c failed"
                            }
                        elif response_text.find("ffmpeg failed") != -1:
                            return {
                                "status": "ffmpeg failed"
                            }
                        elif response_text.find("No video file found") != -1:
                            return {
                                "status": "failed",
                                "reason": "No video file found"
                            }
                        elif response_text.find("upload_failed") != -1:
                            return {
                                "status": "upload_failed",
                                "error": response_text
                            }
                        else:
                            return {
                                "status": "failed",
                                "reason": response_text
                            }
                            
                except Exception as e:
                    logger.error(f"[{current_time}] Error parsing response: {str(e)}")
                    return {
                        "status": "failed",
                        "reason": f"Failed to process response: {str(e)}"
                    }
                    
    except asyncio.TimeoutError:
        error_msg = "Request timed out after 1 hour"
        logger.error(f"[{current_time}] {error_msg}")
        return {
            "status": "failed",
            "reason": error_msg
        }
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(f"[{current_time}] {error_msg}")
        return {
            "status": "failed",
            "reason": error_msg
        }