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
    # ldb= db.query("lb")
    # if ldb == "":
        # db.store("lb", "0:0;0:0;0:0;0:0;0:0;0:0;0:0;0:0;")

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

    lb= []
    get_lb= db.query("lb")
    for line in get_lb.split("\n"):
        try:
            score, suid = line.strip().split(',')
            lb.append({'user_id': suid, 'score': int(score)})
        except ValueError:
            continue

    isOnBoard= False
    for entry in lb:
        if entry['user_id'] == str(uid):
            entry['score'] = xp
            isOnBoard = True
            break

    if not isOnBoard:
        if len(lb) < 10 or xp > min(entry['score'] for entry in lb):
            lb.append({'user_id': str(uid), 'score': xp})

    lb.sort(key=lambda x: x['score'], reverse=True)

    new_lb= ""
    for entry in lb:
        new_lb= new_lb+ f"{entry['score']},{entry['user_id']}\n"
    db.store("lb", new_lb)

    return lb[:10]


class PointsCog(commands.Cog):
    def __init__(self, bot):
        self.bot= bot

    @app_commands.command(name= "points", description= "Take a look at your personal standings")
    @app_commands.guild_only()
    async def __com_points(self, interaction: discord.Interaction):
        points= get_point_count(str(interaction.user.id), str(interaction.guild_id))
        em0= discord.Embed(title= f"Points of {interaction.user.display_name}", colour= 0xEE90AC)
        em0.add_field(name= "Points", value= f"`{points}` CelestialPoints")
        await interaction.response.send_message(embed= em0)

    @app_commands.command(name= "leaderboard", description= "show the leaderboard for the current server")
    @app_commands.guild_only()
    async def __com_lb(self, interaction: discord.Interaction):
        regName= "Celestia-Guilds-"+str(interaction.guild_id)
        db= reg.Database(regName)
        lb= []
        get_lb= db.query("lb")
        for line in get_lb.split("\n"):
            try:
                score, suid = line.strip().split(',')
                lb.append({'user_id': suid, 'score': int(score)})
            except ValueError:
                continue
        lb= lb[:10]

        body= ""
        i= 1
        for entry in lb:
            body= body+ f"[{i}] {interaction.guild.get_member(int(entry['user_id'])).display_name} -> `{int(entry['score'])+1}`CelestialPoints\n"
            i+= 1
        embed= discord.Embed(color= 0xEE90AC, title= "Leaderboard", description= body)
        embed.set_thumbnail(url= interaction.guild.get_member(int(lb[0]["user_id"])).display_avatar)
        await interaction.response.send_message(embed= embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author.bot:
            check(message.author.id, message.guild.id)
            user_xp(message.created_at.timestamp(), message.author.id, message.guild.id)


async def setup(bot):
    await bot.add_cog(PointsCog(bot))
