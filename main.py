import asyncio
import os
import sys
# import logging - removed

import nextcord
import uvicorn
from nextcord.ext import commands
from dotenv import load_dotenv
from fastapi import FastAPI

# Removed logging configuration

# Load environment variables
load_dotenv()

# Set up Discord bot with specific event loop to ensure consistency
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True

# Create a single loop for everything to use
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

bot = commands.Bot(command_prefix='!', intents=intents, loop=loop)
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
        activity=nextcord.Activity(
            type=nextcord.ActivityType.listening,
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
        # Changed from print to just sending message to user
        await ctx.send("An error occurred while executing the command.")


async def load_cogs():
    cog_modules = ['cogs.general', 'cogs.moderation', 'cogs.voice']
    for cog in cog_modules:
        try:
            bot.load_extension(cog)
            # Removed print statement
        except Exception as e:
            # Removed print statement for error
            pass


async def start_server():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()


# Modify main to use the same loop
async def main():
    # Load cogs
    await load_cogs()
    
    # Start the bot
    await bot.start(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("Error: DISCORD_BOT environment variable not set.")
    else:
        # Use our defined loop
        try:
            loop.run_until_complete(main())
        except KeyboardInterrupt:
            loop.run_until_complete(bot.close())
        finally:
            loop.close()
