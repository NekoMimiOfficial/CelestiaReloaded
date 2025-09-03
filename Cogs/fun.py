import random
import discord
import random
import nekos

from discord import app_commands
from discord.ext import commands
from NekoMimi import reg

def getScr(uid, gid):
    regName= "Celestia-Guilds-"+gid
    db= reg.Database(regName)
    q= db.query(uid)
    r= 0
    if q == "":
        return r
    return int(q.split(":")[0])

def writeScr(uid, gid, amt):
    regName= "Celesia-Guilds-"+gid
    db= reg.Database(regName)
    q= db.query(uid)
    r= int(q.split(":")[0])
    r= r+amt
    db.store(uid, f"{r:{q.split(':')[1]}}")

class Fun_Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name= "flipcoin", description= "flip a coin")
    @app_commands.guild_only()
    async def coinflip(self, interaction: discord.Interaction):
        """ Coinflip! """
        coinsides = ['Heads', 'Tails']
        await interaction.response.send_message(f"**{interaction.user.display_name}** flipped a coin and got **{random.choice(coinsides)}**!")

    @app_commands.command(name= "hotness", description= "how hot is this user?")
    @app_commands.guild_only()
    async def hotcalc(self, interaction: discord.Interaction, user: discord.Member = None):
        """ Returns a random percent for how hot is a discord user """
        user = user or interaction.user

        random.seed(user.id)
        r = random.randint(1, 100)
        hot = r / 1.17

        if user.id == 770344920510103573:
            hot= 1000

        emoji = "💔"
        if hot > 25:
            emoji = "❤"
        if hot > 50:
            emoji = "💖"
        if hot > 75:
            emoji = "💞"

        await interaction.response.send_message(f"**{user.name}** is **{hot:.2f}%** hot {emoji}")
    @app_commands.command(name= "slotmachine", description= "oh nyo... gambling..")
    @app_commands.guild_only()
    async def slot(self, interaction: discord.Interaction):
        """ Roll the slot machine """
        emojis = "🍎🍊🍐🍋🍉🍇🍓🍒"
        a = random.choice(emojis)
        b = random.choice(emojis)
        c = random.choice(emojis)

        slotmachine = f"**[ {a} {b} {c} ]\n{interaction.user.display_name}**,"
        points = getScr(str(interaction.user.id), str(interaction.guild_id))
        if points > 4:
            if (a == b == c):
                await interaction.response.send_message(f"{slotmachine} All matching, you **won** `100` Celestial Points! 🎉")
                writeScr(str(interaction.user.id), str(interaction.guild_id), 200)
            elif (a == b) or (a == c) or (b == c):
                await interaction.response.send_message(f"{slotmachine} 2 in a row, you **won** `10` Celestial Points! 🎉")
                writeScr(str(interaction.user.id), str(interaction.guild_id), 25)
            else:
                await interaction.response.send_message(f"{slotmachine} No match, you **lost** `5` Celestial Points 😢")
                writeScr(str(interaction.user.id), str(interaction.guild_id), -5)
        else:
            await interaction.response.send_message(embed=discord.Embed(color=0xEE90AC,description="You must have at least `5` points, keep talking!"), ephemeral= True)

    @app_commands.command(name= "waifu", description= "Get a random waifu image")
    @app_commands.guild_only()
    async def waifu(self, interaction: discord.Interaction):
        embed = discord.Embed(color=0xEE90AC)
        embed.set_image(url=nekos.img(target='waifu'))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name= "rate", description= "Rate a thing!")
    @app_commands.guild_only()
    async def rate(self, interaction: discord.Interaction, thing: str):
        rate_amount = random.uniform(0.0, 100.0)
        embed = discord.Embed(color=0xEE90AC,title='Rating',description=f"I'd rate `{thing}` a **{round(rate_amount, 4)} / 100**")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name= "f", description= "To pay respect")
    @app_commands.guild_only()
    async def f(self, interaction: discord.Interaction, text: str = None):
        hearts = ['❤', '💛', '💚', '💙', '💜']
        reason = f"for **{text}** " if text else ""
        embed = discord.Embed(description=f"**{interaction.user.display_name}** has paid their respect {reason}{random.choice(hearts)}",color=0xEE90AC,title='Respect has been paid')
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun_Commands(bot))
