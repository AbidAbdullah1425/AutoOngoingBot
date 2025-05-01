from pyrogram import filters
from pyrogram.types import Message
from bot import Bot
from plugins.db import add_task, remove_task

@Bot.on_message(filters.command("addtask"))
async def add(bot, msg: Message):
    title = " ".join(msg.command[1:])
    await add_task(title)
    await msg.reply(f"✅ Added: `{title}`")

@Bot.on_message(filters.command("deltask"))
async def delete(bot, msg: Message):
    title = " ".join(msg.command[1:])
    await remove_task(title)
    await msg.reply(f"❌ Removed: `{title}`")