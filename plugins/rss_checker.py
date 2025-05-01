from pyrogram import Client
from plugins.db import get_tracked_titles, is_processed, mark_processed 
from plugins.huggingface_uploader import send_to_huggingface 
import feedparser
import asyncio

RSS_URL = "https://subsplease.org/rss/?t&r=720"

async def check_feed(app: Client):
    while True:
        feed = feedparser.parse(RSS_URL)
        titles = await get_tracked_titles()

        for item in feed.entries:
            title = item.title
            link = item.link  # torrent link
            guid = item.guid

            # Match tracked titles
            for tracked in titles:
                if tracked.lower() in title.lower():
                    if await is_processed(guid):
                        continue

                    await mark_processed(guid)
                    await send_to_huggingface(title, link)

        await asyncio.sleep(600)  # every 10 minutes