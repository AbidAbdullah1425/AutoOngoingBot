from aiohttp import ClientSession
from config import LOGGER, HUGGINGFACE_URL
from datetime import datetime, timezone

logger = LOGGER(__name__)

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
            # Form data
            data = {
                "title": title,
                "torrent": torrent_link,
                "crf": 28,
                "preset": "ultrafast"
            }
            
            try:
                async with session.post(HUGGINGFACE_URL, data=data) as response:
                    logger.info(f"[{current_time}] Response Status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"[{current_time}] Response Text: {result}")
                        
                        # Check if we got file_id and message_id
                        if result.get("status") == "ok" and result.get("file_id") and result.get("message_id"):
                            return {
                                "status": "ok",
                                "file_id": result["file_id"],
                                "message_id": result["message_id"]
                            }
                        else:
                            logger.error(f"Invalid response format: {result}")
                            return {"status": "failed", "error": "Invalid response format"}
                    else:
                        logger.error(f"HuggingFace returned status {response.status}")
                        return {"status": "failed", "error": f"HuggingFace error: {response.status}"}
            
            except Exception as e:
                logger.error(f"Request error: {str(e)}")
                return {"status": "failed", "error": f"Request failed: {str(e)}"}

    except Exception as e:
        logger.error(f"Error in send_to_huggingface: {str(e)}")
        return {"status": "failed", "error": str(e)}