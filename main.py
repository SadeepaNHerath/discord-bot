import asyncio
import json  # Ensure json is properly imported
import os
from datetime import datetime, timedelta

import discord
import uvicorn
from discord.ext import commands, tasks
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException

# Load environment variables
load_dotenv()

# Bot setup
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

# Dictionary to track PRs pending approval
pending_prs = {}

# Voice queues
queues = {}


# Function to check music queue
def check_queue(ctx):
    guild_id = ctx.guild.id
    if guild_id in queues and queues[guild_id]:
        voice = ctx.guild.voice_client
        if voice and not voice.is_playing():
            source = queues[guild_id].pop(0)
            voice.play(source, after=lambda e: check_queue(ctx))


@bot.event
async def on_ready():
    print(f'Bot is ready as {bot.user}')
    if not check_pending_prs.is_running():
        check_pending_prs.start()  # Ensure the loop starts


@tasks.loop(hours=24)
async def check_pending_prs():
    """Remind reviewers to approve PRs that haven't been merged in 24 hours."""
    now = datetime.utcnow()
    to_remove = []

    for pr_number, pr_data in pending_prs.items():
        if (now - pr_data["created_at"]) >= timedelta(days=1):
            message = (f"⏳ **PR pending approval:** {pr_data['url']}\n"
                       f"<@{pr_data['reviewer']}>, please review and merge!")

            # Send reminder message to Discord
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(message)
            else:
                print(f"Error: Channel with ID {CHANNEL_ID} not found.")

            to_remove.append(pr_number)

    # Remove reminded PRs
    for pr_number in to_remove:
        del pending_prs[pr_number]


@check_pending_prs.before_loop
async def before_check_pending_prs():
    """Ensure the bot is ready before starting the task."""
    await bot.wait_until_ready()


# FastAPI webhook for GitHub events
@app.post("/github-webhook")
async def github_webhook(request: Request, x_github_event: str = Header(None)):
    try:
        payload = await request.json()

        print(f"Received GitHub event: {x_github_event}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        if x_github_event == "pull_request":
            pr_data = payload.get("pull_request", {})
            if not pr_data:
                raise HTTPException(status_code=400, detail="No pull request data found in payload")

            pr_title = pr_data.get("title", "No title")
            pr_url = pr_data.get("html_url", "No URL")
            pr_author = pr_data.get("user", {}).get("login", "Unknown")
            pr_state = pr_data.get("state", "Unknown")
            conflict_status = pr_data.get("mergeable", False)
            mergeable_state = pr_data.get("mergeable_state", "unknown")

            if pr_state == "open" and not conflict_status:
                reviewer_id = MENTOR_ID  # Assign the mentor as the reviewer
                pending_prs[pr_data.get("number")] = {
                    "created_at": datetime.utcnow(),
                    "reviewer": reviewer_id,
                    "url": pr_url,
                }

                message = f"⚠️ **Conflict in PR by {pr_author}**: [{pr_title}]({pr_url})\n<@{reviewer_id}>, resolve conflicts!"
                channel = bot.get_channel(CHANNEL_ID)
                if channel:
                    await channel.send(message)
                else:
                    print(f"Error: Channel with ID {CHANNEL_ID} not found.")

            return {"message": "PR processed"}

        else:
            raise HTTPException(status_code=400, detail="Unsupported GitHub event type")

    except Exception as e:
        print(f"Error processing webhook: {e}")
        raise HTTPException(status_code=400, detail="Error processing webhook")


async def start_server():
    """Start the FastAPI server."""
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()


async def start_bot():
    """Start the Discord bot."""
    await bot.start(DISCORD_BOT_TOKEN)


async def main():
    """Run both the FastAPI server and Discord bot concurrently."""
    await asyncio.gather(start_server(), start_bot())


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("Error: DISCORD_BOT environment variable not set.")
    else:
        asyncio.run(main())  # Use asyncio.run to handle event loop correctly
