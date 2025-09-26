import discord
import asyncio
import math
from discord.ext import commands
from discord import app_commands
from discord.webhook.async_ import interaction_response_params

from Cogs.roles import format_seconds
import Tools.DBCables as cables

sqldb= cables.Cables("celestia_datastore.db")
sqldb.connect()

TIME= 10
DIFFICULTY= 100
DIFF_FACTOR= 1.25

sqldb= cables.Cables("celestia_datastore.db")
sqldb.connect()

def lvl(p: int):

    if p < DIFFICULTY:
        return 0

    return int(math.floor(math.log(p / DIFFICULTY, DIFF_FACTOR)))

def anti_lvl(p: int):
    return int(math.ceil((DIFF_FACTOR ** p) * DIFFICULTY))

def to_next_lvl(p:int):
    return int(anti_lvl(lvl(p)+1) - anti_lvl(lvl(p)) - (p - anti_lvl(lvl(p))))

def get_point_count(uid, gid):
    return sqldb.get_gu_pts(uid, gid)

def time_chatting(p: int):
    sec= p* TIME
    mins= 0
    hours= 0
    if sec >= 60:
        mins= int(sec/60)
    if mins >= 60:
        hours= int(mins/60)

    return f"{hours}:{mins%60}:{sec%60}"

def format_seconds(p: int):
    sec= p
    mins= 0
    hours= 0
    if sec >= 60:
        mins= int(sec/60)
    if mins >= 60:
        hours= int(mins/60)

    return f"{hours}:{mins%60}:{sec%60}"

def scparse(sc: int):
    if sc >= 95:
        return "Perfect"
    if sc >= 60:
        return "Good"
    if sc >= 50:
        return "Average"
    if sc >= 30:
        return "Iffy"
    return "Dangerous"

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
                try:
                    await member.kick(reason= "Ghost busted!")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"[ghost buster] error busting {member.display_name}, {e}")
            await interaction.message.delete()
            await interaction.response.send_message("The ghosts have been busted!\nEnjoy your fresh server!")

    class KickerButtonS(discord.ui.Button):
        def __init__(self):
            super().__init__(label= "Cancel", style= discord.ButtonStyle.red)

        async def callback(self, interaction: discord.Interaction):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("Only an administrator can use this button.")
            await interaction.message.delete()
            await interaction.response.send_message("Operation canceled", ephemeral= True)

    class Kicker(discord.ui.View):
        def __init__(self, members: list[discord.Member]):
            super().__init__(timeout=300)
            self.add_item(ModCog.KickerButtonC(members))
            self.add_item(ModCog.KickerButtonS())

    @app_commands.command(name= "ghost-bust", description= "kicks all the members who dont have a specific role")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator= True)
    @app_commands.describe(role= "The role a user must have to NOT get kicked.")
    async def __CMD_kne(self, interaction: discord.Interaction, role: discord.Role):
        members= []
        for member in interaction.guild.members:
            isGhost= True
            for mem_role in member.roles:
                if mem_role.id == role.id or member.bot:
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
            show_roles= show_roles+ f"`[{role.name}]` "

        embed = discord.Embed(colour=0xEE90AC,title=f"About user: {user.display_name}", description= f"{user.mention}")
        if user.display_avatar:
            embed.set_thumbnail(url=user.display_avatar)

        lm= sqldb.get_u_last(int(user.id))
        full_ts= f"<t:{int(lm)}:R>"
        if lm == 0 or not lm:
            full_ts= "`Unknown`"

        dcl= sqldb.get_u_dc(int(user.id))
        if not dcl:
            dcl= 0

        scl= sqldb.get_u_sc(int(user.id))
        if not scl:
            scl= 0
        scl= int(scl)
        scp= scparse(scl)

        upts= sqldb.get_gu_pts(int(user.id), int(user.guild.id))
        pointo= str(upts)

        tg= sqldb.get_u_tg(int(user.id))
        if not tg or tg == 0:
            calc_tg= "Unknown"
        calc_tg= format_seconds(int(tg))

        embed.add_field(name= "Full name", value=user.global_name, inline=True)
        embed.add_field(name= "Nickname", value=user.nick if hasattr(user, "nick") else "None", inline=True)
        embed.add_field(name= "UID", value= user.id)
        embed.add_field(name= "SID", value= user.name)
        embed.add_field(name= "Account created", value=user.created_at.date(), inline=True)
        embed.add_field(name= "Joined this server", value=user.joined_at.date(), inline=True)
        embed.add_field(name= "Social Score", value= f"`{scl} | {scp}`", inline= True)
        embed.add_field(name= "Discord Credit", value= f"`{dcl} | {time_chatting(dcl)}`\n`lvl: {lvl(dcl)}`", inline= True)
        embed.add_field(name= "Last Message", value= full_ts, inline= True)
        embed.add_field(name= "Standing", value= "Regular user", inline= True)
        embed.add_field(name= "Touching grass for", value= f"`{calc_tg}`")
        embed.add_field(name= "Server points", value= f"`{pointo}` <:CelestialPoints:1412891132559495178>", inline= True)
        embed.add_field(name="Roles", value=show_roles, inline=False)

        await interaction.response.send_message(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        print("[ fail ] discord command error:", error)

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
