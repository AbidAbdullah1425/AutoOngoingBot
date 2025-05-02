import aiohttp
from config import LOGGER
from datetime import datetime, timezone

logger = LOGGER(__name__)

HF_URL = "https://abidabdullah199-compressor.hf.space/"

async def send_to_huggingface(title, torrent_link):
    """Send file to HuggingFace for processing"""
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    try:
        # Create form data
        form_data = aiohttp.FormData()
        form_data.add_field("title", title)
        form_data.add_field("torrent_link", torrent_link)
        form_data.add_field("crf", "28")
        form_data.add_field("preset", "ultrafast")
        
        logger.info(f"[{current_time}] Sending to HuggingFace - Title: {title}")
        logger.info(f"[{current_time}] Torrent Link: {torrent_link}")
        
        # Set timeout for the request
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(HF_URL, data=form_data) as response:
                response_text = await response.text()
                logger.info(f"[{current_time}] Response Status: {response.status}")
                logger.info(f"[{current_time}] Response Text: {response_text}")
                
                if response.status != 200:
                    return {
                        "status": "failed",
                        "error": f"HTTP {response.status}: {response_text}"
                    }
                
                try:
                    result = await response.json()
                    logger.info(f"[{current_time}] HuggingFace Response: {result}")
                    return result
                except Exception as e:
                    return {
                        "status": "failed",
                        "error": f"Failed to parse response: {str(e)}"
                    }
                    
    except asyncio.TimeoutError:
        error_msg = f"Request timed out after 300 seconds"
        logger.error(f"[{current_time}] {error_msg}")
        return {"status": "failed", "error": error_msg}
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(f"[{current_time}] {error_msg}")
        return {"status": "failed", "error": error_msg}