from aiohttp import web
from plugins import web_server
from pyrogram.enums import ParseMode
from config import API_HASH, API_ID, LOGGER, TELEGRAM_TOKEN, TG_BOT_WORKERS, PORT
from pyrogram import Client
import asyncio
from datetime import datetime
from db import get_tracked_titles, is_processed, mark_processed
from rss_parser import fetch_rss_items
from config import OWNER_ID
import logging
import pyrogram.utils

pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

feed_status = {"enabled": False}  # Shared feed toggle

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=API_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TELEGRAM_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info("Bot Running...")

        self.uptime = datetime.now()
        self.loop.create_task(self.rss_watcher())

        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")

    async def rss_watcher(self):        
        while True:
            if feed_status["enabled"]:
                logging.info("Checking RSS feed...")
                try:
                    titles = await get_tracked_titles()
                    items = await fetch_rss_items()

                    for item in items:
                        if any(title.lower() in item["title"].lower() for title in titles):
                            if not await is_processed(item["hash"]):
                                await mark_processed(item["hash"])
                                msg = f"<b>Processing Title:</b>\n{item['title']}\n<a href='{item['link']}'>Link</a>"
                                await self.send_message(OWNER_ID, msg)
                                logging.info(f"Processing: {item['title']}")
                except Exception as e:
                    logging.error(f"RSS error: {e}")
            await asyncio.sleep(60)

bot = Bot()
bot.run()



















'''
from aiohttp import web
from plugins import web_server
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
import pyrogram.utils
pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

from config import API_HASH, API_ID, LOGGER, TELEGRAM_TOKEN, TG_BOT_WORKERS, PORT

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=API_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TELEGRAM_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"Bot Running..!\n\nCreated by \nhttps://t.me/codeflix_bots")
        self.LOGGER(__name__).info(f"""       


  ___ ___  ___  ___ ___ _    _____  _____  ___ _____ ___ 
 / __/ _ \|   \| __| __| |  |_ _\ \/ / _ )/ _ \_   _/ __|
| (_| (_) | |) | _|| _|| |__ | | >  <| _ \ (_) || | \__ \
 \___\___/|___/|___|_| |____|___/_/\_\___/\___/ |_| |___/
                                                         
 
                                          """)
        self.username = usr_bot_me.username
        # web-response
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")
        
'''