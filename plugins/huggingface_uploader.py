import aiohttp
from config import LOGGER, HF_ACCESS_TOKEN  # Add HF_ACCESS_TOKEN to your config.py
from datetime import datetime, timezone

# Initialize logger for this module
logger = LOGGER(__name__)

HF_URL = "https://abidabdullah199-compressor.hf.space/"  # Base URL of your space

async def send_to_huggingface(title, torrent_link):
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    logger.info(f"[{current_time}] Starting HuggingFace upload process for title: '{title}'")
    
    headers = {
        "Authorization": f"Bearer {HF_ACCESS_TOKEN}",
    }
    
    # Form data as your FastAPI endpoint expects
    form_data = aiohttp.FormData()
    form_data.add_field("title", title)
    form_data.add_field("torrent_link", torrent_link)
    form_data.add_field("crf", "28")
    form_data.add_field("preset", "ultrafast")
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            logger.info(f"[{current_time}] Sending POST request to HuggingFace")
            
            async with session.post(HF_URL, data=form_data) as resp:
                logger.debug(f"[{current_time}] Response status code: {resp.status}")
                
                response_text = await resp.text()
                logger.debug(f"[{current_time}] Raw response: {response_text}")
                
                if resp.status != 200:
                    error_msg = f"Server returned status code: {resp.status}. Response: {response_text}"
                    logger.error(f"[{current_time}] {error_msg}")
                    return {"status": "failed", "error": error_msg}
                
                try:
                    res = await resp.json()
                    logger.info(f"[{current_time}] Successfully received JSON response from HuggingFace")
                    
                    if res.get("status") == "success":
                        logger.info(f"[{current_time}] Successfully processed '{title}' on HuggingFace")
                        return res
                    else:
                        error_msg = f"Processing failed: {res.get('reason', res.get('error', 'Unknown error'))}"
                        logger.error(f"[{current_time}] {error_msg}")
                        return {"status": "failed", "error": error_msg}
                    
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