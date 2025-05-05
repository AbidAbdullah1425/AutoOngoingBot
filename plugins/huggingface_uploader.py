from aiohttp import ClientSession, ClientTimeout
from config import LOGGER, HUGGINGFACE_URL
from datetime import datetime, timezone
import asyncio

logger = LOGGER(__name__)

# Set a longer timeout
TIMEOUT = ClientTimeout(total=600)  # 10 minutes timeout

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

        # Form data
        data = {
            "title": title,
            "torrent": torrent_link,
            "crf": 28,
            "preset": "ultrafast"
        }

        try:
            async with ClientSession(timeout=TIMEOUT) as session:
                for attempt in range(3):  # Try 3 times
                    try:
                        async with session.post(HUGGINGFACE_URL, data=data) as response:
                            logger.info(f"[{current_time}] Response Status: {response.status}")
                            
                            if response.status == 200:
                                try:
                                    result = await response.json()
                                    logger.info(f"[{current_time}] Response Text: {result}")
                                    
                                    if result.get("status") == "ok":
                                        return result
                                    else:
                                        logger.error(f"Invalid response format: {result}")
                                        return {"status": "failed", "error": result.get("error", "Unknown error")}
                                except Exception as e:
                                    logger.error(f"JSON decode error: {str(e)}")
                                    continue
                            else:
                                logger.error(f"HTTP {response.status}: {await response.text()}")
                                await asyncio.sleep(2)  # Wait before retry
                                continue
                            
                    except asyncio.TimeoutError:
                        logger.error(f"Request timeout on attempt {attempt + 1}")
                        if attempt < 2:  # Don't sleep on last attempt
                            await asyncio.sleep(5)
                        continue
                    except Exception as e:
                        logger.error(f"Request error on attempt {attempt + 1}: {str(e)}")
                        if attempt < 2:
                            await asyncio.sleep(5)
                        continue
                
                return {"status": "failed", "error": "Failed after 3 attempts"}

        except Exception as e:
            logger.error(f"Session error: {str(e)}")
            return {"status": "failed", "error": f"Connection error: {str(e)}"}

    except Exception as e:
        logger.error(f"Error in send_to_huggingface: {str(e)}")
        return {"status": "failed", "error": str(e)}