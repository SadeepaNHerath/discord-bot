import random

import aiohttp
from discord.ext import commands, tasks


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_message.start()
        self.banned_words = ["kill", "fuck", "nigga"]

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Bot is ready as {self.bot.user}')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if any(banned_word in message.content.lower() for banned_word in self.banned_words):
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, your message contained inappropriate language and was removed.")
            return

        greetings = ["hello", "hi", "hey", "greetings"]
        if any(greeting in message.content.lower() for greeting in greetings):
            await message.channel.send(f"Hello {message.author.mention}! How can I assist you today?")

        await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        joke_url = "https://jokes-always.p.rapidapi.com/family"
        headers = {
            "x-rapidapi-key": self.bot.RAPIDAPI_KEY,
            "x-rapidapi-host": "jokes-always.p.rapidapi.com"
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(joke_url, headers=headers) as response:
                    joke_data = await response.json()
                    joke = joke_data.get('data', "Welcome! I couldn't fetch a joke, but I'm still fun! 😂")
            except aiohttp.ClientError:
                joke = "Welcome! Unfortunately, I couldn't fetch a joke for you. 😂"

        channel = self.bot.get_channel(self.bot.CHANNEL_ID)
        if channel:
            await channel.send(f"🎉 **Welcome to the server, {member.mention}!** 🎉\n\n"
                               f"Here's a joke to get you started:\n\n"
                               f"**{joke}**\n\n"
                               "Feel free to introduce yourself and have fun! 😄")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.bot.get_channel(self.bot.CHANNEL_ID)
        if channel:
            await channel.send(f'Goodbye {member.mention} 😢.')

    @tasks.loop(hours=24)
    async def daily_message(self):
        channel = self.bot.get_channel(self.bot.CHANNEL_ID)
        if channel:
            quotes = [
                "Believe in yourself! Have faith in your abilities!",
                "Your limitation—it's only your imagination.",
                "Push yourself, because no one else is going to do it for you.",
                "Great things never come from comfort zones.",
                "Dream it. Wish it. Do it."
            ]
            joke_url = "https://jokes-always.p.rapidapi.com/family"
            headers = {
                "x-rapidapi-key": self.bot.RAPIDAPI_KEY,
                "x-rapidapi-host": "jokes-always.p.rapidapi.com"
            }

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(joke_url, headers=headers) as response:
                        joke_data = await response.json()
                        joke = joke_data.get('data', random.choice(quotes))
                except aiohttp.ClientError:
                    joke = random.choice(quotes)

            await channel.send(f"🌟 **Daily Motivation** 🌟\n\n{joke}")

    @daily_message.before_loop
    async def before_daily_message(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(General(bot))
