import random
from typing import Optional
import discord
import random
import nekos, re

from discord import app_commands
from discord.ext import commands
import Tools.DBCables as cables

sqldb= cables.Cables("celestia_datastore.db")

async def getScr(uid: int):
    await sqldb.connect()
    res= int(await sqldb.get_u_bank(uid))
    return res

async def writeScr(uid: int, amt: int):
    await sqldb.connect()
    if amt > 0:
        await sqldb.inc_u_bank(uid, amt)
    else:
        await sqldb.dec_u_bank(uid, amt*-1)

def is_vowel(char: str) -> bool:
    return char.lower() in 'aeiouy'

def calculate_word_sensibility(name: str) -> float:
    score = 1.0
    n = name.lower()
    if len(n) < 3:
        return 0.5 # Neutral score for very short names

    consecutive_consonants = 0
    consecutive_vowels = 0
    
    for i in range(len(n)):
        char = n[i]
        
        if is_vowel(char):
            consecutive_vowels += 1
            consecutive_consonants = 0
            if consecutive_vowels >= 3:
                score -= 0.10
        else:
            consecutive_consonants += 1
            consecutive_vowels = 0
            if consecutive_consonants >= 3:
                score -= 0.20
    return max(0.0, min(1.0, score))

def blend_names(name1: str, name2: str) -> str:
    n1 = name1.lower()
    n2 = name2.lower()
    len1 = len(n1)
    len2 = len(n2)

    best_split1 = len1 // 2
    
    for i in range(max(1, len1 // 3), min(len1, 2 * len1 // 3 + 1)):
        if not is_vowel(n1[i-1]) and is_vowel(n1[i]):
            best_split1 = i
            break
        elif is_vowel(n1[i-1]) and not is_vowel(n1[i]):
             best_split1 = i
             break
    
    prefix = n1[:best_split1]
    
    if not prefix:
        if len1 > 0: prefix = n1[0]
        else: prefix = "Unknown"

    best_split2_start_index = len2 // 2
    if prefix != "Unknown":
        for i in range(max(1, len2 // 3), min(len2, 2 * len2 // 3 + 1)):
            if not is_vowel(prefix[-1]) and is_vowel(n2[i]):
                best_split2_start_index = i
                break
            elif is_vowel(prefix[-1]) and not is_vowel(n2[i]):
                best_split2_start_index = i
                break
                
    suffix = n2[best_split2_start_index:]
    merged_name = (prefix + suffix).capitalize()
    
    if len(merged_name) < 4 and len(n1) > 2 and len(n2) > 2:
        return (n1[:len1//2] + n2[len2//2:]).capitalize()
        
    return merged_name

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

    @app_commands.command(name= "ship", description= "See how compatible 2 member would be together >.<")
    @app_commands.describe(member1= "First member")
    @app_commands.describe(member2= "Second member")
    async def __CMD_ship(self, interaction: discord.Interaction, member1: discord.Member, member2: discord.Member= None): #type: ignore
        member2= member2 or interaction.user
        sed= member1.id- member2.id if member1.id > member2.id else member2.id- member1.id
        random.seed(sed)

        r= random.randint(1, 100)
        compat= r/ 0.78

        merger= "Uhh you have weird names... can't do that sorry :'3"
        try:
            clean_name1 = re.sub(r'[^a-zA-Z ]', '', member1.display_name.replace("_", " ").replace("-", " "))
            clean_name2 = re.sub(r'[^a-zA-Z ]', '', member2.display_name.replace("_", " ").replace("-", " "))
            merger= blend_names(clean_name1, clean_name2)
        except:
            pass

        compat= compat* calculate_word_sensibility(merger)* 1.17
        compat= compat if compat < 100 else compat* 0.75 if compat* 0.75 < 100 else 100
        compat= compat if compat > 10 else 10 # cause i'd feel bad :'3
        compat= int(compat* 100)/ 100

        shipStat= "Ah... You two might not belong to each other :'<"
        if compat > 25:
            shipStat= "Cute! you two look good together!"
        if compat > 50:
            shipStat= "A strong bond! you two are such a great pair!"
        if compat > 70:
            shipStat= "Awww! what a lovely couple! when's the wed? >.<"

        em0= discord.Embed(title= shipStat, color= 0xEE90AC)
        em0.add_field(name= "Member 1", value= member1.mention, inline= True)
        em0.add_field(name= "Member 2", value= member2.mention, inline= True)
        em0.add_field(name= "Couple Name", value= f"**{merger}**", inline= not merger.startswith("Uhh you have"))
        em0.add_field(name= "Details", value= f"I have shipped **{member1.display_name}** and **{member2.display_name}** with a score of **{compat}**%!", inline= False)

        await interaction.response.send_message(embed= em0)

    @app_commands.command(name= "slotmachine", description= "oh nyo... gambling..")
    @app_commands.guild_only()
    async def slot(self, interaction: discord.Interaction):
        """ Roll the slot machine """
        emojis = "🍎🍊🍐🍋🍉🍇🍓🍒"
        a = random.choice(emojis)
        b = random.choice(emojis)
        c = random.choice(emojis)

        slotmachine = f"**[ {a} {b} {c} ]\n{interaction.user.display_name}**,"
        points = await getScr(int(interaction.user.id))
        if points > 4:
            if (a == b == c):
                await writeScr(int(interaction.user.id), 100)
                await interaction.response.send_message(f"{slotmachine} All matching, you **won** `100` <:CelestialPoints:1412891132559495178>! 🎉")
            elif (a == b) or (a == c) or (b == c):
                await writeScr(int(interaction.user.id), 10)
                await interaction.response.send_message(f"{slotmachine} 2 in a row, you **won** `10` <:CelestialPoints:1412891132559495178>! 🎉")
            else:
                await writeScr(int(interaction.user.id), -5)
                await interaction.response.send_message(f"{slotmachine} No match, you **lost** `5` <:CelestialPoints:1412891132559495178> 😢")
        else:
            await interaction.response.send_message(embed=discord.Embed(color=0xEE90AC,description="You must have at least `5` <:CelestialPoints:1412891132559495178>, keep talking!"), ephemeral= True)

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
