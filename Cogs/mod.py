import discord
import asyncio
import math, json
from discord.ext import commands
from discord import app_commands

from Cogs.roles import format_seconds
import Tools.DBCables as cables

TIME= 10
DIFFICULTY= 100
DIFF_FACTOR= 1.25

sqldb= cables.Cables("celestia_datastore.db")

def lvl(p: int):

    if p < DIFFICULTY:
        return 0

    res= int(math.floor(math.log(p / DIFFICULTY, DIFF_FACTOR)))
    return 1 if res == 0 and p > DIFFICULTY else res


def anti_lvl(p: int):
    return int(math.ceil((DIFF_FACTOR ** p) * DIFFICULTY))

def to_next_lvl(p:int):
    return int(anti_lvl(lvl(p)+1) - anti_lvl(lvl(p)) - (p - anti_lvl(lvl(p))))

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
    def __init__(self, bot: commands.Bot):
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

    @app_commands.command(name= "snipe", description= "Summons elite sniper to snipe messages for you :3")
    @app_commands.guild_only()
    async def __cmd_snipe(self, interaction: discord.Interaction):
        await sqldb.connect()
        getSnip= await sqldb.get_g_snipe(interaction.guild_id)
        if not getSnip.lower().replace('"', "'").replace(" ", "").startswith("{'"):
            await interaction.response.send_message("No snipes in DB.", ephemeral= True)
            return
        jdict= json.loads(getSnip)
        txt= jdict['message']
        dm_ts= "`Unknown`" if jdict['timestamp'] == 0 else f"<t:{int(jdict['timestamp'])}:R>"
        member= None
        try:
            if interaction.guild:
                member= interaction.guild.get_member(int(jdict['auth_id']))
        except:
            pass
        em0= discord.Embed(color= 0xEE90AC, title= "Headshot!")
        if not member:
            em0.add_field(name= "User", value= "Anonymous", inline= True)
        else:
            em0.add_field(name= "User", value= member.mention, inline= True)
            if member.display_avatar:
                em0.set_thumbnail(url= member.display_avatar.url)
        em0.add_field(name= "UID", value= f"`{jdict['auth_id']}`", inline= True)
        em0.add_field(name= "Timestamp", value= f"{dm_ts}", inline= True)
        if not jdict['channel_id'] == 0:
            chan= interaction.guild.get_channel(jdict['channel_id'])
            if chan:
                em0.add_field(name= "Channel", value= chan.mention, inline= True)
        em0.add_field(name= "Guild", value= interaction.guild.name, inline= True)
        if len(txt) > 990:
            txt= txt[:985]+ "... (trimmed)"
        em0.add_field(name= "Message", value= txt, inline= False)
        em0.set_footer(text= "lol get sniped :3")
        await interaction.response.send_message(embed= em0)

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
        for role in user.roles[::-1]:
            if role.name == "@everyone":
                continue
            show_roles= show_roles+ f"`[{role.name}]` "

        embed = discord.Embed(colour=0xEE90AC,title=f"About user: {user.display_name}", description= f"{user.mention}")
        if user.display_avatar:
            embed.set_thumbnail(url=user.display_avatar)

        if user.display_banner:
            embed.set_image(url= user.display_banner.url)

        await sqldb.connect()
        lm= await sqldb.get_u_last(int(user.id))
        full_ts= f"<t:{int(lm)}:R>"
        if lm == 0 or not lm:
            full_ts= "`Unknown`"

        dcl= await sqldb.get_u_dc(int(user.id))
        if not dcl:
            dcl= 0

        scl= await sqldb.get_u_sc(int(user.id))
        if not scl:
            scl= 0
        scl= int(scl)
        scp= scparse(scl)

        upts= await sqldb.get_gu_pts(int(user.id), int(user.guild.id))
        pointo= str(upts)

        tg= await sqldb.get_u_tg(int(user.id))
        if not tg or tg == 0:
            calc_tg= "Unknown"

        ts= int(interaction.created_at.timestamp())
        old_ts= float(await sqldb.get_u_last(user.id))
        calc= ts - old_ts
        old_avg= int(tg)
        points= int(await sqldb.get_u_dc(user.id))
        if not points or points == 0:
            calc_tg= "Unknown"
        else:
            appendix= ""
            if points < 50:
                appendix= "[!] "
            new_avg= int((calc + old_avg) / ((points + 1) / points))
            calc_tg= appendix+ format_seconds(int(new_avg))

        ldm_obj= await sqldb.get_u_snipe(int(user.id))
        ldm= None
        if not ldm_obj.replace('"', "'").replace(" ", "").strip().startswith("{'"):
            ldm= {'message': 'Unknown', 'channel_id': 0, 'guild_id': 0, 'timestamp': 0}
        else:
            ldm= json.loads(ldm_obj)
            if len(ldm['message']) > 990:
                ldm['message']= ldm['message'][:985]+ "... (trimmed)"
        dm_ts= "`Unknown`" if ldm['timestamp'] == 0 else f"<t:{int(ldm['timestamp'])}:R>"

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
        embed.add_field(name= "Touching grass for", value= f"`{calc_tg}`", inline= True)
        embed.add_field(name= "Server points", value= f"`{pointo}` <:CelestialPoints:1412891132559495178>\n`{time_chatting(int(pointo))} | lvl: {lvl(int(pointo))}`", inline= True)
        embed.add_field(name= "DM GID", value= f"`{ldm['guild_id']}`", inline= True)
        embed.add_field(name= "DM CID", value= f"`{ldm['channel_id']}`", inline= True)
        embed.add_field(name= "DM Timestamp", value= f"{dm_ts}", inline= True)
        embed.add_field(name= "Last Deleted Message", value= f"{ldm['message']}", inline= False)
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
