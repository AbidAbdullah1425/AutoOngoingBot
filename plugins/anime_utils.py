from config import LOGGER, ANILIST_API
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List
import aiohttp
import json

logger = LOGGER(__name__)

class AnimeInfo:
    @staticmethod
    async def extract_info_from_filename(filename: str) -> Dict:
        """Extract anime name and episode number from filename"""
        try:
            # Remove [SubsPlease] and quality tag
            name = filename.replace("[SubsPlease]", "").split("[")[0].strip()
            
            # Split into name and episode
            parts = name.rsplit(" - ", 1)
            if len(parts) != 2:
                return {"success": False}
                
            anime_name = parts[0].strip()
            episode = parts[1].strip()
            
            return {
                "success": True,
                "anime_name": anime_name,
                "episode": episode
            }
        except Exception as e:
            logger.error(f"Error extracting info from filename: {str(e)}")
            return {"success": False}

    @staticmethod
    async def get_anime_data(anime_name: str) -> Dict:
        """Get anime info from Anilist"""
        query = '''
        query ($search: String) {
            Media (search: $search, type: ANIME) {
                id
                title {
                    romaji
                    english
                }
                status
                description
                averageScore
                genres
                siteUrl
            }
        }
        '''
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    ANILIST_API,
                    json={
                        'query': query,
                        'variables': {'search': anime_name}
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "data": data['data']['Media']
                        }
                    else:
                        return {"success": False}
        except Exception as e:
            logger.error(f"Error getting anime data: {str(e)}")
            return {"success": False}

    @staticmethod
    async def format_post(anime_data: Dict, episode: str, share_link: str) -> Dict:
        """Format anime post according to template"""
        try:
            # Capitalize first letter of each genre
            genres = [genre.capitalize() for genre in anime_data['genres']]
            
            # Get the cover image from anilist media ID
            media_id = anime_data.get('id')
            cover_url = f"https://img.anili.st/media/{media_id}"
            
            # Truncate synopsis and add read more link with HTML
            synopsis = anime_data['description']
            if synopsis and len(synopsis) > 150:
                synopsis = f"{synopsis[:150]}...\n<a href='{anime_data['siteUrl']}'>Read More</a>"
            
            post_text = (
                f"<b>☗   {anime_data['title']['english'] or anime_data['title']['romaji']}</b>\n\n"
                f"<b>⦿   Ratings:</b> {anime_data['averageScore']/10:.1f}\n"
                f"<b>⦿   Status:</b> {anime_data['status'].capitalize()}\n"
                f"<b>⦿   Episode:</b> {episode}\n"
                f"<b>⦿   Quality:</b> 720p\n"
                f"<b>⦿   Genres:</b> {', '.join(genres)}\n\n"
                f"<b>◆   Synopsis:</b> {synopsis}"
            )
            
            buttons = [[
                InlineKeyboardButton(
                    "📥 Download",
                    url=share_link
                )
            ]]
            
            return {
                "success": True,
                "text": post_text,
                "buttons": buttons,
                "cover_url": cover_url  # Using anilist media ID for cover
            }
        except Exception as e:
            logger.error(f"Error formatting post: {str(e)}")
            return {"success": False}