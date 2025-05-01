# plugins/rss_toggle.py
from pyrogram import filters
from pyrogram.types import Message
from bot import bot

@bot.on_message(filters.command("taskon"))
async def task_on(client, msg: Message):
    client.feed_enabled = True
    await msg.reply("RSS AutoFeed: ✅ <b>Enabled</b>")

@bot.on_message(filters.command("taskoff"))
async def task_off(client, msg: Message):
    client.feed_enabled = False
    await msg.reply("RSS AutoFeed: ❌ <b>Disabled</b>")