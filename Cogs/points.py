import discord
from discord.ext import commands
from discord import app_commands
from NekoMimi import reg
import math

TIME= 10
DIFFICULTY= 100
DIFF_FACTOR= 1.25

def lvl(p: int):

    if p < DIFFICULTY:
        return 0

    return int(math.floor(math.log(p / DIFFICULTY, DIFF_FACTOR)))

def anti_lvl(p: int):
    return int(math.ceil((DIFF_FACTOR ** p) * DIFFICULTY))

def to_next_lvl(p:int):
    return int(anti_lvl(lvl(p)+1) - anti_lvl(lvl(p)) - (p - anti_lvl(lvl(p))))

def get_point_count(uid, gid):
    regName= "Celestia-Guilds-"+gid
    db= reg.Database(regName)
    q= db.query(uid)
    r= 0
    if q == "":
        return r
    return int(q.split(":")[0])

def time_chatting(p: int):
    sec= p* TIME
    mins= 0
    hours= 0
    if sec > 60:
        mins= int(sec/60)
    if mins > 60:
        hours= int(mins/60)

    return f"{hours}:{mins}:{sec%60}"

def check(uid, gid):
    dbName= "Celestia-Guilds-"+str(gid)
    db= reg.Database(dbName)
    gdb= db.query(str(uid))
    if gdb == "":
        db.store(str(uid), "0:0")

def user_xp(ts, uid, gid, dname):
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
            score, suid, name = line.strip().split(',')
            lb.append({'user_id': suid, 'score': int(score), 'name': name})
        except ValueError:
            continue

    isOnBoard= False
    for entry in lb:
        if entry['user_id'] == str(uid):
            entry['score'] = xp
            entry['name'] = dname
            isOnBoard = True
            break

    if not isOnBoard:
        if len(lb) < 10 or xp > min(entry['score'] for entry in lb):
            lb.append({'user_id': str(uid), 'score': xp, 'name': dname})

    lb.sort(key=lambda x: x['score'], reverse=True)

    new_lb= ""
    for entry in lb:
        new_lb= new_lb+ f"{entry['score']},{entry['user_id']},{entry['name']}\n"
    db.store("lb", new_lb)

    return lb[:10]


class PointsCog(commands.Cog):
    def __init__(self, bot):
        self.bot= bot

    @app_commands.command(name= "points", description= "Take a look at your personal standings")
    @app_commands.guild_only()
    async def __com_points(self, interaction: discord.Interaction):
        points= get_point_count(str(interaction.user.id), str(interaction.guild_id))
        tnl= to_next_lvl(points)
        tchat= time_chatting(points)
        em0= discord.Embed(title= f"Points of {interaction.user.display_name}", colour= 0xEE90AC)
        em0.add_field(name= "Points", value= f"`{points}` <:CelestialPoints:1412891132559495178>", inline= True)
        em0.add_field(name= "Level", value=f"`{lvl(points)}`", inline= True)
        em0.add_field(name= "Time chatting", value= f"`{tchat}`", inline= True)
        em0.add_field(name= "Level-up after", value= f"`{tnl}` <:CelestialPoints:1412891132559495178>", inline= True)
        em0.add_field(name= "Base level points", value= f"`{anti_lvl(lvl(points))}` <:CelestialPoints:1412891132559495178>", inline= True)
        em0.add_field(name= "Next level points", value= f"`{anti_lvl(lvl(points)+1)}` <:CelestialPoints:1412891132559495178>", inline= True)
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
                score, suid, name = line.strip().split(',')
                lb.append({'user_id': suid, 'score': int(score), 'name': name})
            except ValueError:
                continue
        lb= lb[:10]

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
        embed.set_thumbnail(url= interaction.guild.get_member(int(lb[0]["user_id"])).display_avatar)
        await interaction.response.send_message(embed= embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author.bot:
            check(message.author.id, message.guild.id)
            user_xp(message.created_at.timestamp(), message.author.id, message.guild.id, message.author.display_name)


async def setup(bot):
    await bot.add_cog(PointsCog(bot))
