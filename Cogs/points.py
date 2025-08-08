import discord
from discord.ext import commands
from discord import app_commands
from NekoMimi import reg

TIME= 10

def lvl(p: int):
    return int(p/128) - int(p/256) - int(p/512) - int (p/1024) - int (p/2048) - int (p/4096) - int (p/8192)

def get_point_count(uid, gid):
    regName= "Celestia-Guilds-"+gid
    db= reg.Database(regName)
    q= db.query(uid)
    r= 0
    if q == "":
        return r
    return int(q.split(":")[0])

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
    removes= 0
    if (ts - tso) > TIME:
        db.store(str(uid), f"{xp+1}:{ts}")
    lb= db.query("lb").split(";")
    del lb[-1]

    isOnLb= False
    for spot in lb:
        if spot.split(":")[1] == str(uid):
            isOnLb= True

    if isOnLb:
        i= 0
        for spot in lb:
            if spot.split(":")[1] == str(uid):
                del lb[i]
            i= i+1
        lb.append("0:0")

    i= 0
    for spot in lb:
        if int(spot.split(":")[0]) < xp:
            lb[i] = f"{xp}:{uid}"
            lbs= ""
            for entry in lb:
                lbs= lbs+ f"{entry};"
            db.store("lb", lbs)
            return lb

    return lb

class PointsCog(commands.Cog):
    def __init__(self, bot):
        self.bot= bot

    @app_commands.command(name= "points", description= "Take a look at your personal standings")
    @app_commands.guild_only()
    async def __com_points(self, interaction: discord.Interaction):
        points= get_point_count(str(interaction.user.id), str(interaction.guild_id))
        em0= discord.Embed(title= f"Points of {interaction.user.display_name}", colour= 0xEE90AC)
        em0.add_field(name= "Points", value= f"`{points}` CP")
        await interaction.response.send_message(embed= em0)

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
