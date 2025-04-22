import nextcord
from nextcord.ext import commands

class Moderation(commands.Cog):
    """Moderation commands for server administrators."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: nextcord.Member = None, *, reason="No reason provided"):
        """Kick a member from the server with an optional reason."""
        if member is None:
            await ctx.send("Error: You must mention a user to kick.")
            return
            
        # Cannot kick yourself
        if member.id == ctx.author.id:
            await ctx.send("You cannot kick yourself.")
            return
            
        # Cannot kick the bot itself
        if member.id == self.bot.user.id:
            await ctx.send("I cannot kick myself.")
            return
            
        # Check if bot has permission to kick
        if not ctx.guild.me.guild_permissions.kick_members:
            await ctx.send("I don't have permission to kick members.")
            return
            
        # Check if the target is higher in hierarchy
        if ctx.author.top_role <= member.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("You cannot kick this member due to role hierarchy.")
            return
            
        try:
            await member.send(f"You have been kicked from {ctx.guild.name} for the following reason: {reason}")
        except nextcord.Forbidden:
            await ctx.send("Could not send a DM to the user.")
            
        await member.kick(reason=reason)
        embed = nextcord.Embed(
            title="User Kicked",
            description=f"{member.mention} has been kicked. Reason: {reason}",
            color=nextcord.Color.red()
        )
        await ctx.send(embed=embed)

    @kick.error
    async def kick_error(self, ctx, error):
        """Handle errors for the kick command."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to kick members.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid member specified.")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: nextcord.Member = None, *, reason="No reason provided"):
        """Ban a member from the server with an optional reason."""
        if member is None:
            await ctx.send("Error: You must mention a user to ban.")
            return
            
        # Cannot ban yourself
        if member.id == ctx.author.id:
            await ctx.send("You cannot ban yourself.")
            return
            
        # Cannot ban the bot itself
        if member.id == self.bot.user.id:
            await ctx.send("I cannot ban myself.")
            return
            
        # Check if bot has permission to ban
        if not ctx.guild.me.guild_permissions.ban_members:
            await ctx.send("I don't have permission to ban members.")
            return
            
        # Check if the target is higher in hierarchy
        if ctx.author.top_role <= member.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("You cannot ban this member due to role hierarchy.")
            return
            
        try:
            await member.send(f"You have been banned from {ctx.guild.name} for the following reason: {reason}")
        except nextcord.Forbidden:
            await ctx.send("Could not send a DM to the user.")
            
        await member.ban(reason=reason)
        embed = nextcord.Embed(
            title="User Banned",
            description=f"{member.mention} has been banned. Reason: {reason}",
            color=nextcord.Color.red()
        )
        await ctx.send(embed=embed)

    @ban.error
    async def ban_error(self, ctx, error):
        """Handle errors for the ban command."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ban members.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid member specified.")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member_id_or_name: str):
        """Unban a user by ID or name#discriminator."""
        # Try to handle both ID and username formats
        try:
            # Check if input is a user ID
            if member_id_or_name.isdigit():
                user = await self.bot.fetch_user(int(member_id_or_name))
                await ctx.guild.unban(user)
                embed = nextcord.Embed(
                    title="User Unbanned",
                    description=f"{user.mention} has been unbanned.",
                    color=nextcord.Color.green()
                )
                await ctx.send(embed=embed)
                return
        except nextcord.NotFound:
            pass
            
        # If not ID or ID lookup failed, try name#discriminator format
        try:
            banned_users = await ctx.guild.bans()
            if '#' in member_id_or_name:
                member_name, member_discriminator = member_id_or_name.split('#')
                
                for ban_entry in banned_users:
                    user = ban_entry.user
                    if (user.name, user.discriminator) == (member_name, member_discriminator):
                        await ctx.guild.unban(user)
                        embed = nextcord.Embed(
                            title="User Unbanned",
                            description=f"{user.mention} has been unbanned.",
                            color=nextcord.Color.green()
                        )
                        await ctx.send(embed=embed)
                        return
            
            await ctx.send(f"User {member_id_or_name} not found in ban list.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @unban.error
    async def unban_error(self, ctx, error):
        """Handle errors for the unban command."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to unban members.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid member specified.")


def setup(bot):
    bot.add_cog(Moderation(bot))
    return bot.add_cog  # Return a valid callable instead of True
