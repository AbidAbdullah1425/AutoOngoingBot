import aiohttp
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, Optional
import re
from config import LOGGER

logger = LOGGER(__name__)

class AnimeInfo:
    ANILIST_API = "https://graphql.anilist.co"
    
    @staticmethod
    async def extract_info_from_filename(filename: str) -> Dict:
        """Extract anime name and episode from filename"""
        try:
            # Remove release group and quality info
            clean_name = re.sub(r'\[.*?\]', '', filename).strip()
            parts = re.split(r'\s*-\s*', clean_name)
            
            if len(parts) >= 2:
                anime_name = parts[0].strip()
                ep_match = re.search(r'(\d+)', parts[1])
                episode = ep_match.group(1) if ep_match else None
                
                return {
                    "success": True,
                    "anime_name": anime_name,
                    "episode": episode
                }
        except Exception as e:
            logger.error(f"Error extracting anime info: {str(e)}")
        
        return {"success": False}

    @staticmethod
    async def get_anime_data(anime_name: str) -> Dict:
        """Fetch anime data from AniList"""
        query = """
        query ($search: String) {
          Media(search: $search, type: ANIME) {
            id
            title {
              romaji
              english
              native
            }
            description
            status
            averageScore
            episodes
            genres
            siteUrl
            coverImage {
              large
            }
          }
        }
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    AnimeInfo.ANILIST_API,
                    json={'query': query, 'variables': {'search': anime_name}}
                ) as response:
                    data = await response.json()
                    
                    if 'errors' in data:
                        logger.error(f"AniList API error: {data['errors']}")
                        return {"success": False}
                    
                    return {
                        "success": True,
                        "data": data['data']['Media']
                    }
        except Exception as e:
            logger.error(f"Error fetching anime data: {str(e)}")
            return {"success": False}

    @staticmethod
    async def format_post(anime_data: Dict, episode: str, share_link: str) -> Dict:
        """Format anime post according to template"""
        try:
            # Capitalize first letter of each genre
            genres = [genre.capitalize() for genre in anime_data['genres']]
            
            # Truncate synopsis and add read more link
            synopsis = anime_data['description']
            if synopsis and len(synopsis) > 150:
                synopsis = f"{synopsis[:150]}...\n[Read More]({anime_data['siteUrl']})"
            
            post_text = (
                f"☗   {anime_data['title']['english'] or anime_data['title']['romaji']}\n\n"
                f"⦿   Ratings: {anime_data['averageScore']/10:.1f}\n"
                f"⦿   Status: {anime_data['status'].capitalize()}\n"
                f"⦿   Episode: {episode}\n"
                f"⦿   Quality: 720p\n"
                f"⦿   Genres: {', '.join(genres)}\n\n"
                f"◆   Synopsis: {synopsis}"
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
                "cover_url": anime_data['coverImage']['large']
            }
        except Exception as e:
            logger.error(f"Error formatting post: {str(e)}")
            return {"success": False}