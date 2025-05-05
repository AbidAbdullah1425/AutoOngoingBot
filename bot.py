from aiohttp import web
from plugins import web_server
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
import pyrogram.utils
pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

from config import API_HASH, API_ID, LOGGER, TELEGRAM_TOKEN, TG_BOT_WORKERS, PORT, DB_CHANNEL_ID

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
        # Remove the comma after LOGGER and fix logging
        self.logger = LOGGER
        self.db_channel = None

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.db_channel = await self.get_chat(DB_CHANNEL_ID)
        self.uptime = datetime.now()

        self.set_parse_mode(ParseMode.HTML)
        # Fix the logger calls
        self.logger(__name__).info("Bot Running..!\n\nCreated by \nhttps://t.me/codeflix_bots")
        self.logger(__name__).info("""       

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
        self.logger(__name__).info("Bot stopped.")