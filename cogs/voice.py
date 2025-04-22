import asyncio
import time

import nextcord
from nextcord import FFmpegPCMAudio, PCMVolumeTransformer
from nextcord.ext import commands

class Voice(commands.Cog):
    """Voice channel functionality for the Discord bot."""
    
    # Constants for better code maintenance
    INACTIVITY_TIMEOUT = 300  # 5 minutes
    ALONE_TIMEOUT = 120  # 2 minutes
    MIN_VOLUME = 0
    MAX_VOLUME = 100
    
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.currently_playing = {}
        self.track_start_time = {}
        self.inactive_voice_clients = {}
        self.disconnect_task = {}

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready."""
        pass

    def check_queue(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.queues and self.queues[guild_id]:
            voice = ctx.guild.voice_client
            if voice and not voice.is_playing():
                source = self.queues[guild_id].pop(0)
                track_name = getattr(source, 'track_name', 'Unknown')
                voice.play(source, after=lambda e: self.play_next(ctx, e))
                self.currently_playing[guild_id] = {'source': source, 'name': track_name}
                self.track_start_time[guild_id] = time.time()

                if not getattr(ctx, 'skip_message', False):
                    embed = nextcord.Embed(
                        title="🎵 Now Playing",
                        description=f"**{track_name}**",
                        color=nextcord.Color.blue()
                    )
                    self.bot.loop.create_task(ctx.send(embed=embed))

                if guild_id in self.disconnect_task and not self.disconnect_task[guild_id].done():
                    self.disconnect_task[guild_id].cancel()

        if guild_id not in self.queues or not self.queues[guild_id]:
            self.disconnect_task[guild_id] = self.bot.loop.create_task(self.disconnect_after_inactivity(ctx))

    def play_next(self, ctx, error):
        if error:
            embed = nextcord.Embed(
                title="❌ Playback Error",
                description=f"An error occurred during playback: {str(error)}",
                color=nextcord.Color.red()
            )
            self.bot.loop.create_task(ctx.send(embed=embed))

        guild_id = ctx.guild.id
        if guild_id in self.currently_playing:
            self.currently_playing.pop(guild_id)

        self.check_queue(ctx)

        # Start inactivity timer if queue is empty
        if guild_id not in self.queues or not self.queues[guild_id]:
            # Make sure to use bot's loop for creating tasks
            self.disconnect_task[guild_id] = self.bot.loop.create_task(self.disconnect_after_inactivity(ctx))

    async def disconnect_after_inactivity(self, ctx):
        await asyncio.sleep(self.INACTIVITY_TIMEOUT)
        voice_client = ctx.guild.voice_client
        if voice_client and not voice_client.is_playing():
            await voice_client.disconnect()
            embed = nextcord.Embed(
                title="🔌 Disconnected",
                description="Disconnected due to inactivity",
                color=nextcord.Color.light_grey()
            )
            await ctx.send(embed=embed)

    @commands.command(name="join", help="Join the voice channel you are in")
    async def join_voice(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            try:
                # Clean up eisting voice client if any
                if ctx.voice_client:
                    await ctx.voice_client.disconnect()
                
                # Use the bot's loop when making voice connections
                voice_client = await channel.connect(reconnect=True, cls=nextcord.VoiceClient)
                
                embed = nextcord.Embed(
                    title="🎧 Voice Channel Joined",
                    description=f"Connected to **{channel.name}**",
                    color=nextcord.Color.green()
                )
                await ctx.send(embed=embed)
            except Exception as e:
                embed = nextcord.Embed(
                    title="❌ Connection Error",
                    description="Could not connect to voice channel. Please try again later.",
                    color=nextcord.Color.red()
                )
                await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="❌ Error",
                description="You need to be in a voice channel first",
                color=nextcord.Color.red()
            )
            await ctx.send(embed=embed)

    @join_voice.error
    async def join_voice_error(self, ctx, error):
        embed = nextcord.Embed(
            title="❌ Connection Error",
            description=f"Could not connect to voice channel: {str(error)}",
            color=nextcord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command(name="leave", help="Leave the current voice channel")
    async def leave_voice(self, ctx):
        if ctx.voice_client:
            guild_id = ctx.guild.id

            # Cancel any pending disconnect task
            if guild_id in self.disconnect_task and not self.disconnect_task[guild_id].done():
                self.disconnect_task[guild_id].cancel()

            # Clear guild data
            if guild_id in self.queues:
                self.queues[guild_id] = []
            if guild_id in self.currently_playing:
                self.currently_playing.pop(guild_id)

            await ctx.voice_client.disconnect()

            embed = nextcord.Embed(
                title="👋 Disconnected",
                description="Successfully left the voice channel",
                color=nextcord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="ℹ️ Information",
                description="I'm not currently in a voice channel",
                color=nextcord.Color.gold()
            )
            await ctx.send(embed=embed)

    @commands.command(name="play", help="Play an audio file from the given name")
    async def play_audio(self, ctx, *, track_name: str = None):
        # Try to join voice channel if not connected
        if not ctx.voice_client and ctx.author.voice:
            try:
                # Use the bot's loop
                await ctx.author.voice.channel.connect(reconnect=True, cls=nextcord.VoiceClient)
            except Exception as e:
                embed = nextcord.Embed(
                    title="⚠️ Connection Error",
                    description="Could not connect to voice channel. Please try again later.",
                    color=nextcord.Color.red()
                )
                return await ctx.send(embed=embed)
        elif not ctx.voice_client:
            embed = nextcord.Embed(
                title="⚠️ Not Connected",
                description="You need to be in a voice channel for me to play audio",
                color=nextcord.Color.gold()
            )
            return await ctx.send(embed=embed)
        
        # Get voice client after ensuring connection
        voice = ctx.voice_client
        
        if not voice:
            # If not connected, try to join the voice channel automatically
            if ctx.author.voice:
                try:
                    # Use the bot's loop
                    voice = await ctx.author.voice.channel.connect(reconnect=True, cls=nextcord.VoiceClient)
                except Exception as e:
                    embed = nextcord.Embed(
                        title="⚠️ Connection Error",
                        description=f"Could not connect to voice channel: {str(e)}",
                        color=nextcord.Color.red()
                    )
                    return await ctx.send(embed=embed)
            else:
                embed = nextcord.Embed(
                    title="⚠️ Not Connected",
                    description="I must be in a voice channel to play audio. Use `!join` first",
                    color=nextcord.Color.gold()
                )
                return await ctx.send(embed=embed)

        if voice.is_paused():
            voice.resume()
            embed = nextcord.Embed(
                title="▶️ Resumed",
                description="Playback has been resumed",
                color=nextcord.Color.green()
            )
            await ctx.send(embed=embed)
        elif track_name:
            try:
                source = PCMVolumeTransformer(FFmpegPCMAudio(f"music/{track_name}.mp3", options="-vn"))
                source.track_name = track_name

                # If something is already playing, add to queue
                if voice.is_playing():
                    guild_id = ctx.guild.id
                    if guild_id not in self.queues:
                        self.queues[guild_id] = []

                    self.queues[guild_id].append(source)

                    embed = nextcord.Embed(
                        title="🎵 Added to Queue",
                        description=f"**{track_name}** added to queue at position #{len(self.queues[guild_id])}",
                        color=nextcord.Color.blue()
                    )
                    await ctx.send(embed=embed)
                else:
                    # Play immediately
                    voice.play(source, after=lambda e: self.play_next(ctx, e))
                    self.currently_playing[ctx.guild.id] = {'source': source, 'name': track_name}
                    self.track_start_time[ctx.guild.id] = time.time()

                    embed = nextcord.Embed(
                        title="🎵 Now Playing",
                        description=f"**{track_name}**",
                        color=nextcord.Color.blue()
                    )
                    await ctx.send(embed=embed)
            except Exception as e:
                embed = nextcord.Embed(
                    title="❌ Playback Error",
                    description=f"Could not play the track: {str(e)}",
                    color=nextcord.Color.red()
                )
                await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="⚠️ Missing Information",
                description="Please provide a track name to play",
                color=nextcord.Color.gold()
            )
            await ctx.send(embed=embed)

    @commands.command(name="queue", help="Add an audio file to the queue")
    async def queue_audio(self, ctx, *, track_name: str):
        """Add a track to the queue and play it if nothing is currently playing."""
        guild_id = ctx.guild.id

        try:
            source = PCMVolumeTransformer(FFmpegPCMAudio(f"music/{track_name}.mp3", options="-vn"))
            source.track_name = track_name

            if guild_id not in self.queues:
                self.queues[guild_id] = []

            position = len(self.queues[guild_id]) + 1
            self.queues[guild_id].append(source)

            embed = nextcord.Embed(
                title="🎵 Added to Queue",
                description=f"**{track_name}** added to queue at position #{position}",
                color=nextcord.Color.blue()
            )
            await ctx.send(embed=embed)

            # If nothing is playing, start playing
            voice = ctx.voice_client
            if voice and not voice.is_playing() and not voice.is_paused():
                ctx.skip_message = True  # Flag to avoid duplicate announcement
                self.check_queue(ctx)
        except Exception as e:
            embed = nextcord.Embed(
                title="❌ Queue Error",
                description=f"Could not add track to queue: {str(e)}",
                color=nextcord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name="pause", help="Pause the currently playing audio")
    async def pause_audio(self, ctx):
        voice = ctx.voice_client
        if voice and voice.is_playing():
            voice.pause()
            embed = nextcord.Embed(
                title="⏸️ Paused",
                description="Audio playback has been paused",
                color=nextcord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="ℹ️ Information",
                description="Nothing is playing right now",
                color=nextcord.Color.gold()
            )
            await ctx.send(embed=embed)

    @commands.command(name="resume", help="Resume the currently paused audio")
    async def resume_audio(self, ctx):
        voice = ctx.voice_client
        if voice and voice.is_paused():
            voice.resume()
            embed = nextcord.Embed(
                title="▶️ Resumed",
                description="Audio playback has been resumed",
                color=nextcord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="ℹ️ Information",
                description="Nothing is paused right now",
                color=nextcord.Color.gold()
            )
            await ctx.send(embed=embed)

    @commands.command(name="stop", help="Stop the currently playing audio")
    async def stop_audio(self, ctx):
        voice = ctx.voice_client
        guild_id = ctx.guild.id

        # Check voice client status
        is_playing = voice and voice.is_playing() if voice else False
        is_paused = voice and voice.is_paused() if voice else False

        if voice and (is_playing or is_paused):
            # Get current track name before stopping
            current_track = None
            if guild_id in self.currently_playing:
                current_track = self.currently_playing[guild_id].get('name', 'Unknown')
            
            # Stop and clear current playback
            voice.stop()
            if guild_id in self.currently_playing:
                self.currently_playing.pop(guild_id)

            embed = nextcord.Embed(
                title="⏹️ Stopped",
                description=f"Stopped playing **{current_track}**",
                color=nextcord.Color.blue()
            )
            await ctx.send(embed=embed)

            # Start inactivity timer
            self.disconnect_task[guild_id] = self.bot.loop.create_task(self.disconnect_after_inactivity(ctx))
        else:
            embed = nextcord.Embed(
                title="ℹ️ Information",
                description="Nothing is playing right now",
                color=nextcord.Color.gold()
            )
            await ctx.send(embed=embed)

    @commands.command(name="skip", help="Skip to the next audio in the queue")
    async def skip_audio(self, ctx):
        guild_id = ctx.guild.id
        voice = ctx.voice_client

        if voice and (voice.is_playing() or voice.is_paused()):
            current_track = None
            if guild_id in self.currently_playing:
                current_track = self.currently_playing[guild_id].get('name', 'Unknown')

            voice.stop()  # This will trigger the after function which calls check_queue

            embed = nextcord.Embed(
                title="⏭️ Skipped",
                description=f"Skipped **{current_track}**",
                color=nextcord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="ℹ️ Information",
                description="Nothing is playing to skip",
                color=nextcord.Color.gold()
            )
            await ctx.send(embed=embed)

    @commands.command(name="volume", help="Set the volume of the audio (0-100)")
    async def set_volume(self, ctx, volume: int):
        if not self.MIN_VOLUME <= volume <= self.MAX_VOLUME:
            embed = nextcord.Embed(
                title="⚠️ Invalid Volume",
                description=f"Volume must be between {self.MIN_VOLUME} and {self.MAX_VOLUME}",
                color=nextcord.Color.gold()
            )
            return await ctx.send(embed=embed)

        voice = ctx.voice_client
        if voice and voice.source:
            voice.source.volume = volume / 100
            embed = nextcord.Embed(
                title="🔊 Volume Changed",
                description=f"Volume set to **{volume}%**",
                color=nextcord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="ℹ️ Information",
                description="Nothing is playing right now",
                color=nextcord.Color.gold()
            )
            await ctx.send(embed=embed)

    @commands.command(name="nowplaying", aliases=["np"], help="Show the currently playing audio")
    async def now_playing(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.currently_playing and self.currently_playing[guild_id]:
            track_info = self.currently_playing[guild_id]
            track_name = track_info.get('name', 'Unknown')

            # Calculate elapsed time if available
            elapsed = "Unknown"
            if guild_id in self.track_start_time:
                elapsed_seconds = int(time.time() - self.track_start_time[guild_id])
                minutes, seconds = divmod(elapsed_seconds, 60)
                elapsed = f"{minutes}:{seconds:02d}"

            embed = nextcord.Embed(
                title="🎵 Now Playing",
                description=f"**{track_name}**",
                color=nextcord.Color.blue()
            )
            embed.add_field(name="Elapsed Time", value=elapsed, inline=True)

            # Add queue position info if available
            if guild_id in self.queues and self.queues[guild_id]:
                embed.add_field(name="Queue Length", value=f"{len(self.queues[guild_id])} tracks", inline=True)

            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="ℹ️ Information",
                description="Nothing is playing right now",
                color=nextcord.Color.gold()
            )
            await ctx.send(embed=embed)

    @commands.command(name="clearqueue", help="Clear the current audio queue")
    async def clear_queue(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.queues and self.queues[guild_id]:
            queue_length = len(self.queues[guild_id])
            self.queues[guild_id] = []

            embed = nextcord.Embed(
                title="🧹 Queue Cleared",
                description=f"Cleared {queue_length} tracks from the queue",
                color=nextcord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="ℹ️ Information",
                description="The queue is already empty",
                color=nextcord.Color.gold()
            )
            await ctx.send(embed=embed)

    @commands.command(name="viewqueue", aliases=["queuelist", "list"], help="View the current queue")
    async def view_queue(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.queues and self.queues[guild_id]:
            queue_list = []
            for i, source in enumerate(self.queues[guild_id]):
                track_name = getattr(source, 'track_name', f'Track {i + 1}')
                queue_list.append(f"**{i + 1}.** {track_name}")

            queue_text = "\n".join(queue_list)

            embed = nextcord.Embed(
                title="🎶 Current Queue",
                description=queue_text,
                color=nextcord.Color.blue()
            )
            embed.set_footer(text=f"Total tracks: {len(self.queues[guild_id])}")
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="ℹ️ Queue Information",
                description="The queue is currently empty",
                color=nextcord.Color.gold()
            )
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        if before.channel is None and after.channel is not None:
            channel = self.bot.get_channel(self.bot.CHANNEL_ID)
            if channel:
                embed = nextcord.Embed(
                    title="🎤 Voice Activity",
                    description=f"{member.mention} joined {after.channel.name}",
                    color=nextcord.Color.green()
                )
                await channel.send(embed=embed)
        elif before.channel is not None and after.channel is None:
            channel = self.bot.get_channel(self.bot.CHANNEL_ID)
            if channel:
                embed = nextcord.Embed(
                    title="🎤 Voice Activity",
                    description=f"{member.mention} left {before.channel.name}",
                    color=nextcord.Color.gold()
                )
                await channel.send(embed=embed)

        # Handle bot being alone in voice channel
        for guild in self.bot.guilds:
            voice_client = guild.voice_client
            if voice_client and voice_client.channel:
                members = voice_client.channel.members
                # If only the bot is in the channel
                if len(members) == 1 and members[0].id == self.bot.user.id:
                    guild_id = guild.id
                    # Start auto-disconnect timer if not already running
                    if guild_id not in self.disconnect_task or self.disconnect_task[guild_id].done():
                        # Get a text channel to send the message
                        text_channel = None
                        for channel in guild.text_channels:
                            if channel.permissions_for(guild.me).send_messages:
                                text_channel = channel
                                break

                        if text_channel:
                            # Use the bot's loop for task creation
                            self.disconnect_task[guild_id] = self.bot.loop.create_task(
                                self.auto_disconnect(voice_client, text_channel, guild_id)
                            )

    async def auto_disconnect(self, voice_client, text_channel, guild_id):
        # Wait before disconnecting if alone
        await asyncio.sleep(self.ALONE_TIMEOUT)
        if voice_client.is_connected() and len(voice_client.channel.members) == 1:
            await voice_client.disconnect()

            # Clear guild data
            if guild_id in self.queues:
                self.queues[guild_id] = []
            if guild_id in self.currently_playing:
                self.currently_playing.pop(guild_id)

            embed = nextcord.Embed(
                title="🔌 Auto-Disconnected",
                description="Left the voice channel because I was alone",
                color=nextcord.Color.blue()
            )
            await text_channel.send(embed=embed)


def setup(bot):
    # Check if Voice cog is already loaded to prevent duplicate instances
    if 'Voice' in bot.cogs:
        return bot.add_cog  # Return a valid callable instead of True
        
    bot.add_cog(Voice(bot))
    return bot.add_cog  # Return a valid callable instead of True
