import discord
from discord.ext import commands
from discord import app_commands
from NekoMimi import reg

TIME= 10

def lvl(p: int):
    return int(p/128) - int(p/256) - int(p/512) - int (p/1024) - int (p/2048) - int (p/4096) - int (p/8192)

def check(uid, gid):
    dbName= "Celestia-Guilds-"+str(gid)
    db= reg.Database(dbName)
    gdb= db.query(str(uid))
    if gdb == "":
        db.store(str(uid), "0:0")
    ldb= db.query("lb")
    if ldb == "":
        db.store("lb", "0:0;0:0;0:0;0:0;0:0;0:0;0:0;0:0;")

def user_xp(ts, uid, gid):
    dbName= "Celestia-Guilds-"+str(gid)
    db= reg.Database(dbName)
    qs= db.query(str(uid))
    xp= qs.split(":")[0]
    tso= qs.split(":")[1].split(".")[0].strip("\n\t")
    xp= int(xp)
    tso= int(tso)
    ts= int(ts)
    if (ts - tso) > TIME:
        db.store(str(uid), f"{xp+1}:{ts}")
    lb= db.query("lb").split(";")
    del lb[-1]
    for spot in lb:
        if int(uid) == int(spot.split(":")[1]):
            for j in range(len(lb)):
                if lb[j].startswith("0"):
                    del lb[j]
    i= 0
    for spot in lb:
        if xp > int(spot.split(":")[0]):
            lb[i]= f"{xp}:{uid}"
            lbs= ""
            for entry in lb:
                lbs = lbs + entry + ";"
                db.store("lb", lbs)
            break
        i= i+1
    
    i= 0
    for spot in lb:
        if spot == "0:0":
            del lb[i]
        i= i+1
    return lb

class PointsCog(commands.Cog):
    def __init__(self, bot):
        self.bot= bot

    @app_commands.command(name= "leaderboard", description= "show the leaderboard for the current server")
    @app_commands.guild_only()
    async def __com_lb(self, interaction: discord.Interaction):
        regName= "Celestia-Guilds-"+str(interaction.guild_id)
        db= reg.Database(regName)
        lb= db.query("lb").split(";")
        del lb[-1]
        for j in range(4):
            i= 0
            for spot in lb:
                if spot.startswith("0"):
                    del lb[i]
                i= i+1
        body= ""
        for spot in lb:
            uid= int(spot.split(":")[1])
            user= interaction.guild.get_member(uid)
            name= user.display_name
            points= int(spot.split(":")[0])
            body= body + f"> **{name}** | points: {points} | lvl:{lvl(points)}" + "\n\n"
        embed= discord.Embed(color= 0xEE90AC, title= "Leaderboard", description= body)
        embed.set_thumbnail(url= interaction.guild.get_member(int(lb[0].split(":")[1])).display_avatar)
        await interaction.response.send_message(embed= embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author.bot:
            check(message.author.id, message.guild.id)
            user_xp(message.created_at.timestamp(), message.author.id, message.guild.id)


async def setup(bot):
    await bot.add_cog(PointsCog(bot))
