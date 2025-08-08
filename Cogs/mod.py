import discord
from discord.ext import commands
from discord import app_commands
from discord.webhook.async_ import interaction_response_params

class ModCog(commands.Cog):
    def __init__(self, bot):
        self.bot= bot

    @app_commands.command(name= "purge")
    @app_commands.guild_only()
    @app_commands.describe(count= "Amount of messages to purge")
    @app_commands.checks.has_permissions(manage_messages= True)
    async def __cmd_purge(self, interaction: discord.Interaction, count: int= 5):
        i= count
        await interaction.response.send_message("Done.", ephemeral= True)
        while i > 0:
            if i < 50:
                await interaction.channel.purge(limit= count)
                break
            else:
                await interaction.channel.purge(limit= 50)
            i = i - 50

    @app_commands.command(name= "user", description= "User information")
    @app_commands.describe(user= "User to perform operation on")
    @commands.guild_only()
    async def user(self,interaction: discord.Interaction, user: discord.Member= None):
        if not user:
            user= interaction.user

        show_roles = ""
        for role in user.roles:
            if role.name == "@everyone":
                continue
            show_roles= show_roles+ f"`{role.name}` "

        embed = discord.Embed(colour=0xEE90AC,title=f"About **{user.display_name}**")
        embed.set_thumbnail(url=user.display_avatar)

        embed.add_field(name="Full name", value=user.global_name, inline=True)
        embed.add_field(name="Nickname", value=user.nick if hasattr(user, "nick") else "None", inline=True)
        embed.add_field(name= "UID", value= user.id)
        embed.add_field(name= "SID", value= user.name)
        embed.add_field(name="Account created", value=user.created_at.date(), inline=True)
        embed.add_field(name="Joined this server", value=user.joined_at.date(), inline=True)
        embed.add_field(name="Roles", value=show_roles, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name= "guild", description= "Give information about the current guild")
    @commands.guild_only()
    async def server(self,interaction: discord.Interaction):
        find_bots = sum(1 for member in interaction.guild.members if member.bot)

        embed = discord.Embed(color=0xEE90AC,title=f'information about **{interaction.guild.name}**')

        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        if interaction.guild.banner:
            embed.set_image(url=interaction.guild.banner.url)

        embed.add_field(name="Server Name", value=interaction.guild.name, inline=True)
        embed.add_field(name="Server ID", value=interaction.guild_id, inline=True)
        embed.add_field(name="Members", value=interaction.guild.member_count, inline=True)
        embed.add_field(name="Bots", value=find_bots, inline=True)
        embed.add_field(name="Owner", value=interaction.guild.owner.display_name, inline=True)
        embed.add_field(name="Region", value="Deprecated", inline=True)
        embed.add_field(name="Created", value=interaction.guild.created_at.date(), inline=True)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ModCog(bot))
