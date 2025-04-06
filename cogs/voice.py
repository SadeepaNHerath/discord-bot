import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands


class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.currently_playing = {}

    def check_queue(self, ctx):
        guild_id = ctx.guild.id
        if self.queues.get(guild_id):
            voice = ctx.guild.voice_client
            if voice and not voice.is_playing():
                source = self.queues[guild_id].pop(0)
                voice.play(source, after=lambda e: self.check_queue(ctx))
                self.currently_playing[guild_id] = source

    @commands.command(name="join", help="Join the voice channel you are in.")
    async def join_voice(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client:
                await ctx.voice_client.move_to(channel)
            else:
                await channel.connect()
            await ctx.send(f"Joined {channel.name}!")
        else:
            await ctx.send("You are not in a voice channel.")

    @join_voice.error
    async def join_voice_error(self, ctx, error):
        await ctx.send(f"Error: {str(error)}")

    @commands.command(name="leave", help="Leave the current voice channel.")
    async def leave_voice(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Disconnected from the voice channel.")
        else:
            await ctx.send("I am not in a voice channel.")

    @leave_voice.error
    async def leave_voice_error(self, ctx, error):
        await ctx.send(f"Error: {str(error)}")

    @commands.command(name="play", help="Play an audio file from the given URL.")
    async def play_audio(self, ctx, url: str = None):
        voice = ctx.voice_client
        if not voice:
            return await ctx.send("I must be in a voice channel to play audio. Use `!join` first.")

        if voice.is_paused():
            voice.resume()
            await ctx.send("Resumed the audio.")
        elif url:
            source = PCMVolumeTransformer(FFmpegPCMAudio(f"music/{url}.mp3", options="-vn"))
            voice.play(source, after=lambda e: self.check_queue(ctx))
            self.currently_playing[ctx.guild.id] = source
            await ctx.send(f"Now playing: {url}")
        else:
            await ctx.send("Please provide an audio file URL.")

    @play_audio.error
    async def play_audio_error(self, ctx, error):
        await ctx.send(f"Error: {str(error)}")

    @commands.command(name="pause", help="Pause the currently playing audio.")
    async def pause_audio(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            voice.pause()
            await ctx.send("Paused the audio.")
        else:
            await ctx.send("No audio is playing.")

    @pause_audio.error
    async def pause_audio_error(self, ctx, error):
        await ctx.send(f"Error: {str(error)}")

    @commands.command(name="resume", help="Resume the currently paused audio.")
    async def resume_audio(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_paused():
            voice.resume()
            await ctx.send("Resumed the audio.")
        else:
            await ctx.send("No audio is paused.")

    @resume_audio.error
    async def resume_audio_error(self, ctx, error):
        await ctx.send(f"Error: {str(error)}")

    @commands.command(name="stop", help="Stop the currently playing audio.")
    async def stop_audio(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            voice.stop()
            await ctx.send("Stopped the audio.")
        else:
            await ctx.send("No audio is playing.")

    @stop_audio.error
    async def stop_audio_error(self, ctx, error):
        await ctx.send(f"Error: {str(error)}")

    @commands.command(name="queue", help="Add an audio file to the queue.")
    async def queue_audio(self, ctx, url: str):
        guild_id = ctx.guild.id
        source = PCMVolumeTransformer(FFmpegPCMAudio(f"music/{url}.mp3", options="-vn"))

        if guild_id not in self.queues:
            self.queues[guild_id] = []

        self.queues[guild_id].append(source)
        await ctx.send(f"Added to queue. Position: {len(self.queues[guild_id])}")

    @queue_audio.error
    async def queue_audio_error(self, ctx, error):
        await ctx.send(f"Error: {str(error)}")

    @commands.command(name="skip", help="Skip to the next audio in the queue.")
    async def skip_audio(self, ctx):
        guild_id = ctx.guild.id
        voice = ctx.guild.voice_client

        if guild_id in self.queues and self.queues[guild_id]:
            voice.stop()
            self.check_queue(ctx)
            await ctx.send("Skipped to the next audio.")
        else:
            await ctx.send("No more audio in the queue.")

    @skip_audio.error
    async def skip_audio_error(self, ctx, error):
        await ctx.send(f"Error: {str(error)}")

    @commands.command(name="volume", help="Set the volume of the audio (0-100).")
    async def set_volume(self, ctx, volume: int):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.source:
            voice.source.volume = volume / 100
            await ctx.send(f"Volume set to {volume}%")
        else:
            await ctx.send("No audio is playing.")

    @set_volume.error
    async def set_volume_error(self, ctx, error):
        await ctx.send(f"Error: {str(error)}")

    @commands.command(name="nowplaying", help="Show the currently playing audio.")
    async def now_playing(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.currently_playing:
            await ctx.send(f"Currently playing: {self.currently_playing[guild_id].title}")
        else:
            await ctx.send("No audio is playing.")

    @now_playing.error
    async def now_playing_error(self, ctx, error):
        await ctx.send(f"Error: {str(error)}")

    @commands.command(name="clearqueue", help="Clear the current audio queue.")
    async def clear_queue(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.queues:
            self.queues[guild_id] = []
            await ctx.send("Cleared the audio queue.")
        else:
            await ctx.send("No audio in the queue.")

    @clear_queue.error
    async def clear_queue_error(self, ctx, error):
        await ctx.send(f"Error: {str(error)}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel is None and after.channel is not None:
            channel = self.bot.get_channel(self.bot.CHANNEL_ID)
            if channel:
                await channel.send(f"{member.mention} has joined {after.channel.name} voice channel.")
        elif before.channel is not None and after.channel is None:
            channel = self.bot.get_channel(self.bot.CHANNEL_ID)
            if channel:
                await channel.send(f"{member.mention} has left {before.channel.name} voice channel.")


async def setup(bot):
    await bot.add_cog(Voice(bot))
