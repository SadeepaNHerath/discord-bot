import os

import discord
import requests
from discord import FFmpegPCMAudio
from discord.ext import commands
from discord.ext.commands import has_permissions
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

queues = {}


def check_queue(ctx):
    guild_id = ctx.guild.id
    if queues.get(guild_id):
        voice = ctx.guild.voice_client
        if voice and not voice.is_playing():
            source = queues[guild_id].pop(0)
            voice.play(source, after=lambda e: check_queue(ctx))


@bot.event
async def on_ready():
    print(f'Bot is ready as {bot.user}')


@bot.command()
async def hello(ctx):
    await ctx.send('Hey there! I have been modified in main!')



@bot.event
async def on_member_join(member):
    joke_url = "https://jokes-always.p.rapidapi.com/family"
    headers = {
        "x-rapidapi-key": os.getenv('RAPIDAPI_KEY'),
        "x-rapidapi-host": "jokes-always.p.rapidapi.com"
    }

    try:
        joke_data = requests.get(joke_url, headers=headers).json()
        joke = joke_data.get('data', "Welcome! I couldn't fetch a joke, but I'm still fun! 😂")
    except Exception:
        joke = "Welcome! Unfortunately, I couldn't fetch a joke for you. 😂"

    channel = bot.get_channel(int(os.getenv('CHANNEL_ID')))
    if channel:
        await channel.send(f"🎉 **Welcome to the server, {member.mention}!** 🎉\n\n"
                           f"Here's a joke to get you started:\n\n"
                           f"**{joke}**\n\n"
                           "Feel free to introduce yourself and have fun! 😄")


@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(int(os.getenv('CHANNEL_ID')))
    if channel:
        await channel.send(f'Goodbye {member.mention} 😢.')


@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f"Joined {channel.name}!")
    else:
        await ctx.send("You are not in a voice channel.")


@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected from voice channel.")
    else:
        await ctx.send("I am not in a voice channel.")


@bot.command()
async def play(ctx, url: str = None):
    voice = ctx.voice_client
    if not voice:
        return await ctx.send("I must be in a voice channel to play audio. Use `!join` first.")

    if voice.is_paused():
        voice.resume()
        await ctx.send("Resumed the song.")
    elif url:
        source = FFmpegPCMAudio(f"music/{url}.mp3")
        voice.play(source, after=lambda e: check_queue(ctx))
        await ctx.send(f"Now playing: {url}")
    else:
        await ctx.send("Please provide an audio file URL.")


@bot.command()
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.pause()
        await ctx.send("Paused the song.")
    else:
        await ctx.send("No song is playing.")


@bot.command()
async def resume(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_paused():
        voice.resume()
        await ctx.send("Resumed the song.")
    else:
        await ctx.send("No song is paused.")


@bot.command()
async def stop(ctx):
    """Stops the audio."""
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.stop()
        await ctx.send("Stopped the song.")
    else:
        await ctx.send("No song is playing.")


@bot.command()
async def queue(ctx, url: str):
    """Adds a song to the queue."""
    guild_id = ctx.guild.id
    source = FFmpegPCMAudio(f"music/{url}.mp3")

    if guild_id not in queues:
        queues[guild_id] = []

    queues[guild_id].append(source)
    await ctx.send(f"Added to queue. Position: {len(queues[guild_id])}")


@bot.command()
async def next(ctx):
    guild_id = ctx.guild.id
    voice = ctx.guild.voice_client

    if guild_id in queues and queues[guild_id]:
        voice.stop()
        check_queue(ctx)
        await ctx.send("Skipped to the next song.")
    else:
        await ctx.send("No more songs in the queue.")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.lower() == "kill":
        await message.delete()
        await message.channel.send("Don't say that again. Otherwise, I will take action.")

    await bot.process_commands(message)


@bot.command()
@has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member = None, *, reason="No reason provided"):
    if member is None:
        await ctx.send("Error: You must mention a user to kick.")
        return
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} has been kicked. Reason: {reason}")


@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to kick members.")


@bot.command()
@has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason="No reason provided"):
    if member is None:
        await ctx.send("Error: You must mention a user to ban.")
        return
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} has been banned. Reason: {reason}")


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to ban members.")


# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT')
    if not token:
        print("Error: DISCORD_BOT environment variable not set.")
    else:
        bot.run(token)
