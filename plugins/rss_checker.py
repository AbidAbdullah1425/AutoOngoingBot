from aiohttp import web
from plugins import web_server
from pyrogram.enums import ParseMode
from config import API_HASH, API_ID, LOGGER, TELEGRAM_TOKEN, TG_BOT_WORKERS, PORT, OWNER_ID
from pyrogram import Client
from datetime import datetime
import asyncio
import logging
import pyrogram.utils

from rss_checker import check_feed  # <== FIXED: correct import

pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

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

        # Start feed watcher with self passed into check_feed()
        self.loop.create_task(check_feed(self))  # <== USES check_feed() from rss_checker

        # Start aiohttp web server
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")

bot = Bot()
bot.run()