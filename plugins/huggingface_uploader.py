import aiohttp
from config import LOGGER
from datetime import datetime, timezone
import asyncio
import json

logger = LOGGER(__name__)

# Corrected URL with capital C in Compressor
HF_URL = "https://abidabdullah199-Compressor.hf.space/"

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
        form_data.add_field("crf", str(crf))
        form_data.add_field("preset", preset)
        
        # Log the request
        logger.info(f"[{current_time}] Sending request to HuggingFace")
        logger.info(f"[{current_time}] Title: {title}")
        logger.info(f"[{current_time}] Torrent: {torrent_link}")
        logger.info(f"[{current_time}] CRF: {crf}")
        logger.info(f"[{current_time}] Preset: {preset}")
        
        # Set timeout (30 minutes since video processing takes time)
        timeout = aiohttp.ClientTimeout(total=1800)
        
        # Headers to ensure proper content type handling
        headers = {
            "Accept": "application/json",
            "Content-Type": "multipart/form-data"
        }
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(HF_URL, data=form_data, headers=headers) as response:
                # Log response status and headers
                logger.info(f"[{current_time}] Response Status: {response.status}")
                logger.info(f"[{current_time}] Response Content-Type: {response.headers.get('content-type', 'unknown')}")
                
                # Get response text first
                response_text = await response.text()
                logger.info(f"[{current_time}] Raw Response: {response_text}")
                
                if response.status != 200:
                    return {
                        "status": "failed",
                        "error": f"HTTP {response.status}: {response_text}"
                    }
                
                try:
                    # Try to parse JSON response
                    if response.headers.get('content-type', '').startswith('application/json'):
                        result = json.loads(response_text)
                    else:
                        # If response is not JSON, create a result based on status
                        if "success" in response_text.lower():
                            result = {"status": "success", "message": response_text}
                        else:
                            result = {"status": "failed", "error": response_text}
                    
                    logger.info(f"[{current_time}] Processed Response: {result}")
                    
                    if result.get("status") == "success":
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
                    logger.error(f"[{current_time}] Error parsing response: {str(e)}")
                    # If we can't parse the response but got a 200 status, assume success
                    if response.status == 200:
                        return {
                            "status": "success",
                            "message": "Request completed successfully"
                        }
                    return {
                        "status": "failed",
                        "error": f"Failed to process response: {str(e)}"
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