from motor.motor_asyncio import AsyncIOMotorClient
import os
from config import DB_URL, DB_NAME

client = AsyncIOMotorClient(DB_URL)
db = client.DB_NAME

async def add_task(title): await db.tasks.update_one({"title": title}, {"$set": {"title": title}}, upsert=True)
async def remove_task(title): await db.tasks.delete_one({"title": title})
async def get_tracked_titles(): return [doc["title"] async for doc in db.tasks.find()]
async def is_processed(hash): return await db.processed.find_one({"hash": hash}) is not None
async def mark_processed(hash): await db.processed.insert_one({"hash": hash})