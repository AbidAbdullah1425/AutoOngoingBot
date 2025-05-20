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

        # Form data - convert all values to strings to match curl behavior
        data = {
            "title": str(title),
            "torrent": str(torrent_link),
            "crf": "28",  # Convert to string
            "preset": "ultrafast"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"  # Add Accept header
        }

        # Ensure URL ends with a slash
        url = HUGGINGFACE_URL if HUGGINGFACE_URL.endswith('/') else f"{HUGGINGFACE_URL}/"

        async with ClientSession(timeout=TIMEOUT) as session:
            for attempt in range(3):
                try:
                    logger.info(f"Attempt {attempt + 1}/3 - Making request to {url}")
                    async with session.post(
                        url,  # Use the URL with trailing slash
                        data=data,
                        headers=headers,
                        allow_redirects=True  # Allow redirects
                    ) as response:
                        logger.info(f"[{current_time}] Response Status: {response.status}")

                        # Get response text first
                        text = await response.text()
                        logger.info(f"[{current_time}] Raw Response: {text}")

                        if response.status == 200:
                            try:
                                import json
                                result = json.loads(text)
                                logger.info(f"[{current_time}] Parsed Response: {result}")

                                if result.get("status") == "ok":
                                    return result
                                else:
                                    error_msg = result.get("error", "Unknown error")
                                    logger.error(f"API Error: {error_msg}")
                                    if attempt == 2:  # Last attempt
                                        return {"status": "failed", "error": error_msg}
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON Parse Error: {str(e)}, Response: {text}")
                                if attempt == 2:
                                    return {"status": "failed", "error": f"Invalid JSON response: {text[:100]}..."}
                        elif response.status in [301, 302, 307, 308]:
                            # Handle redirects manually if needed
                            redirect_url = response.headers.get('Location')
                            logger.info(f"Redirecting to: {redirect_url}")
                            continue
                        else:
                            logger.error(f"HTTP {response.status}: {text}")
                            if attempt == 2:  # Last attempt
                                return {"status": "failed", "error": f"HTTP {response.status}"}

                except asyncio.TimeoutError:
                    logger.error(f"Request timeout on attempt {attempt + 1}")
                    if attempt < 2:
                        await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"Request error on attempt {attempt + 1}: {str(e)}")
                    if attempt < 2:
                        await asyncio.sleep(5)

                # Wait between attempts
                if attempt < 2:
                    await asyncio.sleep(5)

            return {"status": "failed", "error": "All attempts failed"}

    except Exception as e:
        logger.error(f"Error in send_to_huggingface: {str(e)}")
        return {"status": "failed", "error": str(e)}