import aiohttp
from config import LOGGER
from datetime import datetime, timezone

# Initialize logger for this module
logger = LOGGER(__name__)

HF_URL = "https://abidabdullah199-Compressor.hf.space/"

async def send_to_huggingface(title, torrent_link):
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    logger.info(f"[{current_time}] Starting HuggingFace upload process for title: '{title}'")
    logger.debug(f"[{current_time}] Upload URL: {HF_URL}")
    
    async with aiohttp.ClientSession() as session:
        # Prepare request data
        data = {
            "title": title,
            "torrent_link": torrent_link,
            "crf": 28,
            "preset": "ultrafast"
        }
        logger.debug(f"[{current_time}] Prepared upload data: {data}")
        
        try:
            logger.info(f"[{current_time}] Sending POST request to HuggingFace")
            
            async with session.post(HF_URL, data=data) as resp:
                # Log response status
                logger.debug(f"[{current_time}] Response status code: {resp.status}")
                
                if resp.status != 200:
                    logger.warning(f"[{current_time}] Received non-200 status code: {resp.status}")
                
                try:
                    res = await resp.json()
                    logger.info(f"[{current_time}] Successfully received JSON response from HuggingFace")
                    logger.debug(f"[{current_time}] HuggingFace response: {res}")
                    
                    # Log success or failure based on response
                    if res.get("status") == "success":
                        logger.info(f"[{current_time}] Successfully processed '{title}' on HuggingFace")
                    else:
                        logger.warning(f"[{current_time}] HuggingFace processing reported non-success status for '{title}'")
                    
                    return res
                    
                except Exception as json_error:
                    error_msg = f"Error parsing JSON response: {str(json_error)}"
                    logger.error(f"[{current_time}] {error_msg}", exc_info=True)
                    return {"status": "failed", "error": error_msg}
                    
        except aiohttp.ClientError as client_error:
            error_msg = f"HTTP client error: {str(client_error)}"
            logger.error(f"[{current_time}] {error_msg}", exc_info=True)
            return {"status": "failed", "error": error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error sending to HuggingFace: {str(e)}"
            logger.error(f"[{current_time}] {error_msg}", exc_info=True)
            return {"status": "failed", "error": error_msg}
        
        finally:
            logger.debug(f"[{current_time}] Completed HuggingFace upload attempt for '{title}'")