import asyncio
import os
import sys

import discord
import uvicorn
from discord.ext import commands
from dotenv import load_dotenv
from fastapi import FastAPI

# Load environment variables
load_dotenv()

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
app = FastAPI()

# Environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT")
MENTOR_ID = os.getenv("MENTOR_ID")
MY_ID = os.getenv("MY_ID")
try:
    CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
    DISCORD_SERVER_ID = int(os.getenv("DISCORD_SERVER_ID", 0))
except ValueError:
    print("Invalid CHANNEL_ID or DISCORD_SERVER_ID - must be integers")
    sys.exit(1)
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')

# Store key variables on the bot
bot.RAPIDAPI_KEY = RAPIDAPI_KEY
bot.CHANNEL_ID = CHANNEL_ID

@bot.event
async def on_ready():
    print(f"Bot is ready as {bot.user}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="!help for commands"
        )
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use !help to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Bad argument. Please check your input.")
    else:
        print(f"Unhandled error: {error}")
        await ctx.send("An error occurred while executing the command.")


async def load_cogs():
    cog_modules = ['cogs.general', 'cogs.moderation', 'cogs.voice']
    for cog in cog_modules:
        try:
            await bot.load_extension(cog)
            print(f"Loaded extension: {cog}")
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
