import discord
import asyncio
from discord.ext import commands
from discord import app_commands
from discord.webhook.async_ import interaction_response_params

class ModCog(commands.Cog):
    def __init__(self, bot):
        self.bot= bot

    class KickerButtonC(discord.ui.Button):
        def __init__(self, members: list[discord.Member]):
            super().__init__(label= "Confirm", style= discord.ButtonStyle.green)
            self.members= members

        async def callback(self, interaction: discord.Interaction):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("Only an administrator can use this button.")
            for member in self.members:
                await member.kick(reason= "Ghost busted!")
                await asyncio.sleep(0.5)
            await interaction.message.delete()
            await interaction.response.send_message("The ghosts have been busted!\nEnjoy your fresh server!")

    class KickerButtonS(discord.ui.Button):
        def __init__(self, members):
            super().__init__(label= "Cancel", style= discord.ButtonStyle.red)
            self.members= members

        async def callback(self, interaction: discord.Interaction):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("Only an administrator can use this button.")
            await interaction.message.delete()
            await interaction.response.send_message("Operation canceled", ephemeral= True)

    class Kicker(discord.ui.View):
        def __init__(self, members: list[discord.Member]):
            super().__init__(timeout=300)
            self.add_item(ModCog.KickerButtonC(members))
            self.add_item(ModCog.KickerButtonS(members))

    @app_commands.command(name= "ghost-bust", description= "kicks all the members who dont have a specific role")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator= True)
    @app_commands.describe(role= "The role a user must have to NOT get kicked.")
    async def __CMD_kne(self, interaction: discord.Interaction, role: discord.Role):
        members= []
        for member in interaction.guild.members:
            isGhost= True
            for mem_role in member.roles:
                if mem_role.id == role.id:
                    isGhost= False
                    break
            if isGhost:
                members.append(member)

        embed= discord.Embed(color= 0xEE90AC, title= f"Kicking **{len(members)}** members", description= "ARE YOU SURE YOU WANT TO KICK THESE MEMBERS?\nThis action is irreversible")
        view= self.Kicker(members)
        await interaction.response.send_message(embed= embed, view= view)

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

        embed = discord.Embed(colour=0xEE90AC,title=f"About {user.mention}")
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
