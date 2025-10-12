import discord
from discord.ext import commands
from discord import app_commands
import math, random

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
    return (anti_lvl(lvl(p)+ 1))- p

async def get_point_count(uid, gid):
    await sqldb.connect()
    res= await sqldb.get_gu_pts(uid, gid)
    return res

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

def generate_biased_random(min_val: int= 50, max_val: int= 1200, target_mean: int= 200, std_dev: float= 50) -> int:
    """
    Generates a random integer within a specified range, biased towards a target mean 
    using a Normal (Gaussian) distribution.

    Args:
        min_val (int): The absolute minimum value (e.g., 50).
        max_val (int): The absolute maximum value (e.g., 1200).
        target_mean (int): The central value to bias the results towards (e.g., 200).
        std_dev (float): The standard deviation controlling the spread around the mean.
                         A smaller value means tighter clustering around the mean.
                         (You can choose 50 to keep most values between 100 and 300).
                         (No.. it's not std::dev :3)

    Returns:
        int: A random integer, clamped within [min_val, max_val].
    """
    gaussianeur = random.gauss(mu=target_mean, sigma=std_dev)
    clampino = max(min_val, min(max_val, gaussianeur))

    return int(clampino)

async def user_xp(ts, uid, gid, dname, gname):
    await sqldb.connect()
    await sqldb.init_guild(gid, gname)
    old_ts= await sqldb.get_gu_ts(gid, uid)
    if (ts - old_ts) > TIME:
        await sqldb.inc_gu_points(gid, uid, ts, 1, dname)

class PointsCog(commands.Cog):
    def __init__(self, bot):
        self.bot= bot

    @app_commands.command(name= "points", description= "Take a look at your personal standings")
    @app_commands.guild_only()
    @app_commands.describe(member= "Lookup points for a specific member")
    async def __com_points(self, interaction: discord.Interaction, member: discord.Member= None):
        member= member or interaction.user
        points= await get_point_count(member.id, interaction.guild_id)
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
        await sqldb.connect()
        bank= await sqldb.get_u_bank(member.id)
        if not bank:
            bank= 0
        em0= discord.Embed(title= f"Bank account of {member.display_name}", color= 0xEE90AC, description= "Welcome to the central celestial bank, your funds are safely stored here and are separate from your guild points and discord credits")
        if member.display_avatar:
            em0.set_thumbnail(url= member.display_avatar)
        em0.add_field(name= "Points", value= f"`{bank}` <:CelestialPoints:1412891132559495178>", inline= True)
        em0.add_field(name= "Level", value= f"`{lvl(bank)}`", inline= True)
        em0.add_field(name= "Next level", value= f"`{to_next_lvl(bank)}` <:CelestialPoints:1412891132559495178>")
        await interaction.response.send_message(embed= em0)

    @app_commands.command(name= "pay", description= "Pay a user money/Transfer money into another user's account with a 1% fee.")
    @app_commands.describe(amount= "Amount to pay")
    @app_commands.describe(user= "The user to pay to")
    async def __CMD_pay(self, interaction: discord.Interaction,user: discord.User, amount: int):
        await sqldb.connect()
        if amount < 0:
            amount= amount* -1
        available= await sqldb.get_u_bank(interaction.user.id)
        fee= math.ceil(amount / 100)
        if int(available) < amount + fee:
            await interaction.response.send_message(f"Sorry... you dont have enough funds to complete the transfer, make sure you can cover your amount plus an additional fee of **{fee}** <:CelestialPoints:1412891132559495178>", ephemeral= True)
            return
        await sqldb.pay(interaction.user.id, user.id, amount, fee, user.display_name, interaction.created_at.timestamp())
        embed= discord.Embed(color= 0xEE90AC, title= "Celestial Pay", description= f"Transaction: {interaction.user.mention} → {user.mention}\nSent: **{amount}** <:CelestialPoints:1412891132559495178>\nFee: **{fee}** <:CelestialPoints:1412891132559495178>\nRemaining balance: **{await sqldb.get_u_bank(interaction.user.id) - amount}** <:CelestialPoints:1412891132559495178>")
        embed.set_footer(text= "Funds are sent to the bank, they are not connected to your server points")
        embed.set_thumbnail(url="http://nekomimi.tilde.team/res/misc/CelestialPay.png")
        embed.timestamp= interaction.created_at.now()
        await interaction.response.send_message(embed= embed)

    @app_commands.command(name= "daily", description= "Get your daily salary")
    async def __CMD_daily(self, interaction: discord.Interaction):
        await sqldb.connect()
        daily_ts= await sqldb.get_u_daily(interaction.user.id)
        current_ts= interaction.created_at.timestamp()
        if (current_ts - daily_ts) < (86400 - 4 * 60 * 60):
            await interaction.response.send_message(f"Please wait `{format_seconds(int((86400 - 14400) - (current_ts - daily_ts)))}` before the next daily.", ephemeral= True)
            return
        salary= generate_biased_random()
        await sqldb.inc_u_bank(interaction.user.id, salary)
        await sqldb.set_u_daily(interaction.user.id, current_ts)
        embed= discord.Embed(color= 0xEE90AC, title= "Received daily!", description= f"You have received **{salary}** <:CelestialPoints:1412891132559495178>!\nCome back after 20 hours to claim your next daily")
        embed.set_footer(text= "Funds are sent to the bank, they are not connected to your server points")
        embed.set_thumbnail(url="http://nekomimi.tilde.team/res/misc/CelestialPay.png")
        await interaction.response.send_message(embed= embed)

    @app_commands.command(name= "leaderboard", description= "show the leaderboard for the current server")
    @app_commands.guild_only()
    async def __com_lb(self, interaction: discord.Interaction):
        lb= []
        await sqldb.connect()
        get_lb= await sqldb.get_gu_lb(interaction.guild_id)
        for entry in get_lb:
            lb.append({'user_id': int(entry[0]), 'score': int(entry[1]), 'name': entry[2]})

        body= "**Congrats to the top 3 members!**\n"
        i= 1
        for entry in lb:
            if i == 3:
                spacer= "\n"
            else:
                spacer= ""
            body= body+ f"[{i}] {entry['name']} | `{int(entry['score'])+1}` <:CelestialPoints:1412891132559495178> | lvl{lvl(entry['score']+1)}\n{spacer}"
            i+= 1
        embed= discord.Embed(color= 0xEE90AC, title= "Leaderboard", description= body)
        try:
            embed.set_thumbnail(url= interaction.guild.get_member(int(lb[0]["user_id"])).display_avatar)
        except:
            pass
        await interaction.response.send_message(embed= embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author.bot and message.guild:
            await sqldb.connect()

            ts= int(message.created_at.timestamp())
            old_ts= float(await sqldb.get_u_last(message.author.id))
            calc= ts - old_ts
            old_avg= int(await sqldb.get_u_tg(message.author.id))
            if calc > TIME:
                points= int(await sqldb.get_u_dc(message.author.id))
                if points == 0:
                    points= 1
                new_avg= int(((old_avg * points) + calc) / (points + 1))
                await sqldb.set_u_tg(message.author.id, new_avg)
            else:
                new_avg= int(old_avg - calc)
                if new_avg > 0:
                    await sqldb.set_u_tg(message.author.id, new_avg)
            
            await user_xp(message.created_at.timestamp(), message.author.id, message.guild.id, message.author.display_name, message.guild.name)
            

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await sqldb.connect()
        await sqldb.init_guild(guild.id, guild.name)


async def setup(bot):
    await bot.add_cog(PointsCog(bot))
