import asyncio
import os

import discord
import uvicorn
from discord.ext import commands
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
app = FastAPI()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT")
MENTOR_ID = os.getenv("MENTOR_ID")
MY_ID = os.getenv("MY_ID")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DISCORD_SERVER_ID = int(os.getenv("DISCORD_SERVER_ID"))
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')

bot.RAPIDAPI_KEY = RAPIDAPI_KEY
bot.CHANNEL_ID = CHANNEL_ID


async def load_cogs():
    for cog in ['cogs.general', 'cogs.moderation', 'cogs.voice']:
        try:
            await bot.load_extension(cog)
        except Exception as e:
            print(f"Failed to load cog {cog}: {e}")


async def start_server():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await load_cogs()
    async with bot:
        bot.loop.create_task(start_server())
        await bot.start(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("Error: DISCORD_BOT environment variable not set.")
    else:
        asyncio.run(main())
