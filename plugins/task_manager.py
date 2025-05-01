from pyrogram import filters
from pyrogram.types import Message
from bot import Bot, feed_status
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

@Bot.on_message(filters.command("taskon"))
async def task_on(bot, msg: Message):
    feed_status["enabled"] = True
    await msg.reply("RSS AutoFeed: ✅ <b>Enabled</b>")

@Bot.on_message(filters.command("taskoff"))
async def task_off(bot, msg: Message):
    feed_status["enabled"] = False
    await msg.reply("RSS AutoFeed: ❌ <b>Disabled</b>")