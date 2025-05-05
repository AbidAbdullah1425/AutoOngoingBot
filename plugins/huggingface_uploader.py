from aiohttp import ClientSession
from config import LOGGER
from datetime import datetime, timezone

logger = LOGGER(__name__)
HUGGINGFACE_URL = "https://abidabdullah199-Compressor.hf.space/"  # Make sure this is correct

async def send_to_huggingface(title: str, torrent_link: str):
    try:
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.info(f"[{current_time}] Starting request to HuggingFace Space")

        # Log parameters
        logger.info(f"[{current_time}] Parameters:")
        logger.info(f"  - Title: {title}")
        logger.info(f"  - Torrent: {torrent_link}")
        logger.info(f"  - CRF: 28")
        logger.info(f"  - Preset: ultrafast")

        async with ClientSession() as session:
            data = {
                "title": title,
                "torrent": torrent_link,  # Changed from torrent_link to torrent
                "crf": 28,
                "preset": "ultrafast"
            }
            
            async with session.post(HUGGINGFACE_URL, data=data) as response:
                logger.info(f"[{current_time}] Response Status: {response.status}")
                result = await response.json()
                logger.info(f"[{current_time}] Response Text: {result}")
                return result

    except Exception as e:
        logger.error(f"Error in send_to_huggingface: {e}")
        return {"status": "failed", "error": str(e)}