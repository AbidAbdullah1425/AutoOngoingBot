import aiohttp
from config import LOGGER
from datetime import datetime, timezone

# Initialize logger for this module
logger = LOGGER(__name__)

HF_URL = "https://abidabdullah199-Compressor.hf.space/"  # Your FastAPI URL

async def send_to_huggingface(title, torrent_link):
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    logger.info(f"[{current_time}] Starting upload process for: {title}")
    
    # Create form data exactly as your FastAPI expects
    form_data = aiohttp.FormData()
    form_data.add_field("title", title)
    form_data.add_field("torrent_link", torrent_link)
    form_data.add_field("crf", "28")
    form_data.add_field("preset", "ultrafast")

    try:
        async with aiohttp.ClientSession() as session:
            logger.info(f"[{current_time}] Sending to FastAPI: {title} with link {torrent_link}")
            async with session.post(HF_URL, data=form_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"[{current_time}] FastAPI error: {error_text}")
                    return {"status": "failed", "error": error_text}

                result = await response.json()
                logger.info(f"[{current_time}] FastAPI response: {result}")
                return result

    except Exception as e:
        error_msg = f"Error sending to FastAPI: {str(e)}"
        logger.error(f"[{current_time}] {error_msg}")
        return {"status": "failed", "error": error_msg}