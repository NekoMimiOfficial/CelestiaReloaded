import discord
from discord.ext import commands
from discord import app_commands
import math

import Tools.DBCables as cables

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

def user_xp(ts, uid, gid, dname, gname):
    sqldb.init_guild(gid, gname)
    old_ts= sqldb.get_gu_ts(gid, uid)
    if (ts - old_ts) > TIME:
        sqldb.inc_gu_points(gid, uid, ts, 1, dname)

class PointsCog(commands.Cog):
    def __init__(self, bot):
        self.bot= bot

    @app_commands.command(name= "points", description= "Take a look at your personal standings")
    @app_commands.guild_only()
    @app_commands.describe(member= "Lookup points for a specific member")
    async def __com_points(self, interaction: discord.Interaction, member: discord.Member= None):
        member= member or interaction.user
        points= get_point_count(member.id, interaction.guild_id)
        if not points:
            await interaction.response.send_message("unable to fetch points, the user may not have sent a message yet", ephemeral= True)
            return
        tnl= to_next_lvl(points)
        tchat= time_chatting(points)
        em0= discord.Embed(title= f"Points of {member.display_name}", colour= 0xEE90AC)
        em0.add_field(name= "Points", value= f"`{points}` <:CelestialPoints:1412891132559495178>", inline= True)
        em0.add_field(name= "Level", value=f"`{lvl(points)}`", inline= True)
        em0.add_field(name= "Time chatting", value= f"`{tchat}`", inline= True)
        em0.add_field(name= "Level-up after", value= f"`{tnl}` <:CelestialPoints:1412891132559495178>", inline= True)
        em0.add_field(name= "Base level points", value= f"`{anti_lvl(lvl(points))}` <:CelestialPoints:1412891132559495178>", inline= True)
        em0.add_field(name= "Next level points", value= f"`{anti_lvl(lvl(points)+1)}` <:CelestialPoints:1412891132559495178>", inline= True)
        if member.display_avatar:
            em0.set_thumbnail(url=member.display_avatar)
        await interaction.response.send_message(embed= em0)

    @app_commands.command(name= "bank", description= "access data about the points you save across all guilds.")
    @app_commands.describe(member= "Lookup points for a specific member")
    async def __com_bank(self, interaction: discord.Interaction, member: discord.Member= None):
        member= member or interaction.user
        bank= sqldb.get_u_bank(member.id)
        if not bank:
            bank= 0
        em0= discord.Embed(title= f"Bank account of {member.display_name}", color= 0xEE90AC, description= "Welcome to the central celestial bank, your funds are safely stored here and are separate from your guild points and discord credits")
        if member.display_avatar:
            em0.set_thumbnail(url= member.display_avatar)
        em0.add_field(name= "Points", value= f"`{bank}` <:CelestialPoints:1412891132559495178>", inline= True)
        em0.add_field(name= "Level", value= f"`{lvl(bank)}`", inline= True)
        em0.add_field(name= "Next level", value= f"`{to_next_lvl(bank)}` <:CelestialPoints:1412891132559495178>")
        await interaction.response.send_message(embed= em0)

    @app_commands.command(name= "leaderboard", description= "show the leaderboard for the current server")
    @app_commands.guild_only()
    async def __com_lb(self, interaction: discord.Interaction):
        lb= []
        get_lb= sqldb.get_gu_lb(interaction.guild_id)
        for entry in get_lb:
            lb.append({'user_id': int(entry[0]), 'score': int(entry[1]), 'name': entry[2]})

        body= "**Congrats to the top 3 members!**\n"
        i= 1
        for entry in lb:
            if i == 3:
                spacer= "\n"
            else:
                spacer= ""
            body= body+ f"[{i}] {entry['name']} | `{int(entry['score'])+1}`<:CelestialPoints:1412891132559495178> | lvl{lvl(entry['score']+1)}\n{spacer}"
            i+= 1
        embed= discord.Embed(color= 0xEE90AC, title= "Leaderboard", description= body)
        try:
            embed.set_thumbnail(url= interaction.guild.get_member(int(lb[0]["user_id"])).display_avatar)
        except:
            pass
        await interaction.response.send_message(embed= embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author.bot:

            ts= int(message.created_at.timestamp())
            old_ts= int(sqldb.get_u_last(message.author.id))
            calc= ts - old_ts
            if calc > TIME:
                old_avg= int(sqldb.get_u_tg(message.author.id))
                points= int(sqldb.get_u_dc(message.author.id))
                new_avg= int((calc + old_avg) / ((points + 1) / points))
                sqldb.set_u_tg(message.author.id, new_avg)
            
            user_xp(message.created_at.timestamp(), message.author.id, message.guild.id, message.author.display_name, message.guild.name)
            

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        sqldb.init_guild(guild.id, guild.name)


async def setup(bot):
    await bot.add_cog(PointsCog(bot))
