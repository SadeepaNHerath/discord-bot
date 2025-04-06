import discord
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member = None, *, reason="No reason provided"):
        if member is None:
            await ctx.send("Error: You must mention a user to kick.")
            return
        try:
            await member.send(f"You have been kicked from {ctx.guild.name} for the following reason: {reason}")
        except discord.Forbidden:
            await ctx.send("Could not send a DM to the user.")
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="User Kicked",
            description=f"{member.mention} has been kicked. Reason: {reason}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to kick members.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid member specified.")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member = None, *, reason="No reason provided"):
        if member is None:
            await ctx.send("Error: You must mention a user to ban.")
            return
        try:
            await member.send(f"You have been banned from {ctx.guild.name} for the following reason: {reason}")
        except discord.Forbidden:
            await ctx.send("Could not send a DM to the user.")
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="User Banned",
            description=f"{member.mention} has been banned. Reason: {reason}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ban members.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid member specified.")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member_name: str):
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member_name.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                embed = discord.Embed(
                    title="User Unbanned",
                    description=f"{user.mention} has been unbanned.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                try:
                    await user.send(f"You have been unbanned from {ctx.guild.name}.")
                except discord.Forbidden:
                    await ctx.send("Could not send a DM to the user.")
                return

        await ctx.send(f"User {member_name}#{member_discriminator} not found in ban list.")

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to unban members.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid member specified.")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
